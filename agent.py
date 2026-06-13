from google import genai
from dotenv import load_dotenv
import os
import fitz
from pinecone import Pinecone
import time
from google.genai import types
from pptx import Presentation
import io
from docx import Document
import zipfile
import base64

load_dotenv()

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index("multimodal-rag")


def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    texts = []
    for page_num, page in enumerate(doc):
        text = page.get_text()
        if text.strip():
            texts.append({"page": page_num + 1, "text": text.strip()})
    return texts

def extract_images(pdf_path):
    doc = fitz.open(pdf_path)
    images = []
    for page_num in range(len(doc)):
        page = doc[page_num]
        image_list = page.get_images()
        for img in image_list:
            xref = img[0]
            base_image = doc.extract_image(xref)
            images.append({
                "page": page_num + 1,
                "data": base_image["image"],
                "ext": base_image["ext"]
            })
    return images

def describe_image(image_data, ext="png"):
    for attempt in range(5):
        try:
            mime = "image/jpeg" if ext in ["jpg", "jpeg"] else f"image/{ext}"
            response = client.models.generate_content(
                model="gemini-3.5-flash",
                contents=[{"parts": [
                    {"inline_data": {"mime_type": mime, "data": image_data}},
                    {"text": "Describe this image in detail. If it is a diagram or flowchart, explain each component and how they connect."}
                ]}]
            )
            return response.text
        except Exception as e:
            print(f"Attempt {attempt+1} failed. Retrying in 15 seconds...")
            time.sleep(15)
    return "Image description unavailable"

def chunk_text(text, chunk_size=500, overlap=50):
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size - overlap):
        chunk = " ".join(words[i:i + chunk_size])
        if chunk.strip():
            chunks.append(chunk)
    return chunks

def get_embedding(text):
    for attempt in range(5):
        try:
            result = client.models.embed_content(
                model="gemini-embedding-001",
                contents=text,
                config=types.EmbedContentConfig(output_dimensionality=768)
            )
            return result.embeddings[0].values
        except Exception as e:
            print(f"Embedding attempt {attempt+1} failed. Retrying in 15 seconds...")
            time.sleep(15)
    return None

def extract_from_docx(docx_path):
    doc = Document(docx_path)
    texts = []
    images = []
    full_text = ""
    for para in doc.paragraphs:
        if para.text.strip():
            full_text += para.text.strip() + "\n"
    if full_text:
        texts.append({"page": 1, "text": full_text.strip()})
    with zipfile.ZipFile(docx_path) as z:
        for name in z.namelist():
            if name.startswith("word/media/"):
                ext = name.split(".")[-1].lower()
                if ext in ["png", "jpg", "jpeg"]:
                    images.append({"page": 1, "data": z.read(name), "ext": ext})
    return texts, images

def extract_from_pptx(pptx_path):
    prs = Presentation(pptx_path)
    texts = []
    images = []
    for slide_num, slide in enumerate(prs.slides):
        slide_text = ""
        for shape in slide.shapes:
            if hasattr(shape, "text"):
                slide_text += shape.text + "\n"
            if shape.shape_type == 13:
                image_data = shape.image.blob
                images.append({
                    "page": slide_num + 1,
                    "data": image_data,
                    "ext": shape.image.ext
                })
        if slide_text.strip():
            texts.append({
                "page": slide_num + 1,
                "text": slide_text.strip()
            })
    return texts, images

def ingest_document(file_path):
    ext = file_path.lower().split(".")[-1]

    if ext == "pdf":
        texts = extract_text_from_pdf(file_path)
        images = extract_images(file_path)
    elif ext == "pptx":
        texts, images = extract_from_pptx(file_path)
    elif ext == "docx":
        texts, images = extract_from_docx(file_path)
    else:
        print(f"Unsupported: {ext}")
        return

    doc_id = os.path.basename(file_path)

    for item in texts:
        for chunk in chunk_text(item["text"]):
            embedding = get_embedding(chunk)
            if embedding:
                vid = f"{doc_id}_text_p{item['page']}_{abs(hash(chunk)) % 100000}"
                index.upsert(vectors=[{
                    "id": vid,
                    "values": embedding,
                    "metadata": {
                        "source": doc_id,
                        "page": item["page"],
                        "type": "text",
                        "content": chunk[:500]
                    }
                }])

    for img in images:
        description = describe_image(base64.b64encode(img["data"]).decode(), img["ext"])
        if description:
            embedding = get_embedding(description)
            if embedding:
                vid = f"{doc_id}_img_p{img['page']}_{abs(hash(description)) % 100000}"
                index.upsert(vectors=[{
                    "id": vid,
                    "values": embedding,
                    "metadata": {
                        "source": doc_id,
                        "page": img["page"],
                        "type": "image",
                        "content": description[:500]
                    }
                }])

    print(f"Done: {doc_id}")

def batch_ingest(folder_path):
    supported = ["pdf", "pptx", "docx"]
    files = [
        os.path.join(folder_path, f) 
        for f in os.listdir(folder_path) 
        if f.split(".")[-1].lower() in supported
    ]
    
    print(f"Found {len(files)} documents to process")
    
    for i, file_path in enumerate(files):
        print(f"\nProcessing {i+1}/{len(files)}: {file_path}")
        try:
            ingest_document(file_path)
        except Exception as e:
            print(f"Failed: {file_path} — {e}")
            continue
    
    print("\nBatch ingestion complete!")

def query_rag(question, top_k=5):
    embedding = get_embedding(question)
    if not embedding:
        return "Embedding failed."

    results = index.query(vector=embedding, top_k=top_k, include_metadata=True)
    context = "\n\n".join([
        f"[{m.metadata.get('source', 'unknown')}, p.{m.metadata.get('page', '?')}]\n{m.metadata.get('content', m.metadata.get('text', ''))}"
        for m in results.matches
    ])

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[{"parts": [{"text": f"Context:\n{context}\n\nQuestion: {question}\n\nAnswer strictly from context above."}]}]
    )
    return response.text

