import streamlit as st
from agent import ingest_document, query_rag
import os

st.set_page_config(page_title="Enterprise Intelligence Layer")
st.title("Enterprise Document Intelligence")

def estimate_time(file_size_kb, file_type):
    if file_type == "pdf":
        return max(1, int(file_size_kb / 200))
    elif file_type == "pptx":
        return max(1, int(file_size_kb / 150))
    elif file_type == "docx":
        return max(1, int(file_size_kb / 600))
    return 1

tab1, tab2 = st.tabs(["Upload Documents", "Ask Questions"])

with tab1:
    st.subheader("Single or Multiple Documents")
    uploaded = st.file_uploader(
        "Upload Documents", 
        type=["pdf", "pptx", "docx"], 
        accept_multiple_files=True
    )

    if uploaded:
        for f in uploaded:
            size_kb = f.size / 1024
            ext = f.name.split(".")[-1].lower()
            est = estimate_time(size_kb, ext)
            st.info(f"⏱ **{f.name}** ({size_kb:.1f} KB) — Estimated ingestion time: **~{est} minutes**")

    if uploaded and st.button("Ingest"):
        for f in uploaded:
            path = f"temp_{f.name}"
            with open(path, "wb") as out:
                out.write(f.getbuffer())
            with st.spinner(f"Ingesting {f.name}..."):
                try:
                    ingest_document(path)
                    st.success(f"✅ {f.name} ingested!")
                except Exception as e:
                    st.error(f"❌ {f.name} failed: {e}")
                finally:
                    if os.path.exists(path):
                        os.remove(path)

with tab2:
    st.subheader("Ask Questions")
    question = st.text_input("Ask a question about your documents")
    if st.button("Search") and question:
        with st.spinner("Searching..."):
            try:
                answer = query_rag(question)
                st.write(answer)
            except Exception as e:
                st.error(f"Error: {e}")