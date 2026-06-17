from google import genai
from google.genai import types
from dotenv import load_dotenv
import os
import fitz
from pinecone import Pinecone
import time
from pptx import Presentation
from docx import Document
import zipfile

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GOOGLE_API_KEY"),
    http_options=types.HttpOptions(api_version="v1beta")
)

pc    = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index("multimodal-rag")

GENERATION_MODEL = "gemini-2.5-flash"
EMBEDDING_MODEL  = "gemini-embedding-001"
EMBEDDING_DIM    = 768


def chunk_text(text, chunk_size=500, overlap=50):
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size - overlap):
        chunk = " ".join(words[i:i + chunk_size])
        if chunk.strip():
            chunks.append(chunk)
    return chunks


def get_embedding(text):
    for attempt in range(3):
        try:
            result = client.models.embed_content(
                model=EMBEDDING_MODEL,
                contents=text,
                config=types.EmbedContentConfig(output_dimensionality=EMBEDDING_DIM)
            )
            return result.embeddings[0].values
        except Exception as e:
            wait = 5 * (attempt + 1)
            print(f"Embedding attempt {attempt+1} failed. Retrying in {wait}s...")
            time.sleep(wait)
    return None


def describe_image(image_bytes, ext="png"):
    mime = "image/jpeg" if ext.lower() in ["jpg", "jpeg"] else f"image/{ext.lower()}"
    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model=GENERATION_MODEL,
                contents=[
                    types.Part.from_bytes(data=image_bytes, mime_type=mime),
                    types.Part.from_text(text="Describe this image in detail. If it contains a diagram, chart, or flowchart, explain each component and how they connect.")
                ]
            )
            return response.text
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                print(f"Quota exceeded — skipping image.")
                return None
            wait = 5 * (attempt + 1)
            print(f"Image attempt {attempt+1} failed: {e}. Retrying in {wait}s...")
            time.sleep(wait)
    return None


def extract_text_from_pdf(pdf_path):
    doc, texts = fitz.open(pdf_path), []
    for page_num, page in enumerate(doc):
        text = page.get_text()
        if text.strip():
            texts.append({"page": page_num + 1, "text": text.strip()})
    return texts


def extract_images_from_pdf(pdf_path):
    doc, images = fitz.open(pdf_path), []
    for page_num in range(len(doc)):
        for img in doc[page_num].get_images():
            base = doc.extract_image(img[0])
            if len(base["image"]) >= 5000:
                images.append({"page": page_num + 1, "data": base["image"], "ext": base["ext"]})
    return images


def extract_from_docx(docx_path):
    doc       = Document(docx_path)
    full_text = "\n".join(p.text.strip() for p in doc.paragraphs if p.text.strip())
    texts     = [{"page": 1, "text": full_text}] if full_text else []
    images    = []
    with zipfile.ZipFile(docx_path) as z:
        for name in z.namelist():
            if name.startswith("word/media/"):
                ext  = name.rsplit(".", 1)[-1].lower()
                data = z.read(name)
                if ext in ["png", "jpg", "jpeg"] and len(data) >= 5000:
                    images.append({"page": 1, "data": data, "ext": ext})
    return texts, images


def extract_from_pptx(pptx_path):
    prs, texts, images = Presentation(pptx_path), [], []
    for slide_num, slide in enumerate(prs.slides):
        slide_text = ""
        for shape in slide.shapes:
            if hasattr(shape, "text") and shape.text.strip():
                slide_text += shape.text + "\n"
            try:
                if hasattr(shape, "image"):
                    data = shape.image.blob
                    if len(data) >= 5000:
                        images.append({"page": slide_num + 1, "data": data, "ext": "png"})
            except Exception:
                continue
        if slide_text.strip():
            texts.append({"page": slide_num + 1, "text": slide_text.strip()})
    return texts, images


def ingest_document(file_path):
    ext = file_path.lower().rsplit(".", 1)[-1]
    if ext == "pdf":
        texts  = extract_text_from_pdf(file_path)
        images = extract_images_from_pdf(file_path)
    elif ext == "pptx":
        texts, images = extract_from_pptx(file_path)
    elif ext == "docx":
        texts, images = extract_from_docx(file_path)
    else:
        print(f"Unsupported: {ext}")
        return

    doc_id, batch = os.path.basename(file_path), []

    for item in texts:
        for chunk in chunk_text(item["text"]):
            emb = get_embedding(chunk)
            if emb:
                batch.append({
                    "id":     f"{doc_id}_text_p{item['page']}_{abs(hash(chunk)) % 100000}",
                    "values": emb,
                    "metadata": {"source": doc_id, "page": item["page"], "type": "text", "content": chunk[:1000]}
                })

    for img in images:
        desc = describe_image(img["data"], img["ext"])
        if desc:
            emb = get_embedding(desc)
            if emb:
                batch.append({
                    "id":     f"{doc_id}_img_p{img['page']}_{abs(hash(desc)) % 100000}",
                    "values": emb,
                    "metadata": {"source": doc_id, "page": img["page"], "type": "image", "content": desc[:1000]}
                })

    if batch:
        for i in range(0, len(batch), 100):
            index.upsert(vectors=batch[i:i + 100])
        print(f"✓ {len(batch)} vectors ingested from: {doc_id}")
    else:
        print(f"⚠ No vectors from: {doc_id}")


def batch_ingest(folder_path):
    files = [
        os.path.join(folder_path, f) for f in os.listdir(folder_path)
        if f.rsplit(".", 1)[-1].lower() in {"pdf", "pptx", "docx"}
    ]
    print(f"Found {len(files)} document(s)")
    for i, fp in enumerate(files):
        print(f"\n[{i+1}/{len(files)}] {fp}")
        try:
            ingest_document(fp)
        except Exception as e:
            print(f"✗ Failed: {fp} — {e}")
    print("\nDone.")


def query_rag(question, top_k=5):
    emb = get_embedding(question)
    if not emb:
        return "Embedding failed."

    results = index.query(vector=emb, top_k=top_k, include_metadata=True)
    if not results.matches:
        return "No relevant content found."

    context = "\n\n".join(
        f"[{m.metadata.get('source','unknown')}, p.{m.metadata.get('page','?')}]\n{m.metadata.get('content','')}"
        for m in results.matches
    )

    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model=GENERATION_MODEL,
                contents=(
                    f"Context:\n{context}\n\n"
                    f"Question: {question}\n\n"
                    f"Answer strictly from context. If not found, say so."
                )
            )
            return response.text
        except Exception as e:
            wait = 10 * (attempt + 1)
            print(f"Query attempt {attempt+1} failed. Retrying in {wait}s...")
            time.sleep(wait)
    return "Service temporarily unavailable. Please try again in a few minutes."