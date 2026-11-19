"""
Page 1 View: Candidate Resume Upload, OCR & ChromaDB Embedding.
Handles drag-and-drop file ingestion, PII extraction, and vector indexing.
"""

import time
import pandas as pd
import streamlit as st

from config import UPLOAD_DIR
from database import upsert_candidate, get_all_candidates
from ingestion import process_resume_file
from vector_store import get_vector_store

def render_page_upload():
    """Renders Page 1: Resume Upload & Ingestion."""
    vector_store = get_vector_store()

    st.markdown("""
    <div class="page-banner">
        <div>
            <div class="page-banner-title">📥 Page 1: Upload Candidate Resumes</div>
            <div class="page-banner-desc">Upload PDF, DOCX, or scanned resumes. The system extracts OCR text, candidate Name, Phone Number, Email, and indexes vector chunks into ChromaDB.</div>
        </div>
        <span style="background: #2563EB; color: white; padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: 700;">STAGE 1</span>
    </div>
    """, unsafe_allow_html=True)

    uploaded_files = st.file_uploader(
        "Upload Candidate Resumes (PDF, DOCX, TXT):",
        type=["pdf", "docx", "doc", "txt"],
        accept_multiple_files=True
    )

    if uploaded_files:
        if st.button("🚀 Process & Ingest Uploaded Resumes", type="primary", key="btn_upload"):
            progress_bar = st.progress(0)
            status_box = st.empty()
            
            for idx, file in enumerate(uploaded_files):
                save_path = UPLOAD_DIR / file.name
                with open(save_path, "wb") as f:
                    f.write(file.getbuffer())
                    
                status_box.markdown(f"**Extracting OCR & PII:** `{file.name}`...")
                with st.spinner(f"Normalizing & Embedding `{file.name}` into ChromaDB..."):
                    cand_data = process_resume_file(str(save_path), category="Uploaded")
                    upsert_candidate(cand_data)
                    vector_store.add_candidate_chunks(cand_data["chunks"])
                    
                progress_bar.progress((idx + 1) / len(uploaded_files))
                
            status_box.markdown(f"✅ Successfully ingested and indexed **{len(uploaded_files)}** resumes into ChromaDB!")
            st.success(f"Processing complete! {len(uploaded_files)} candidate(s) ready for matching.")
            time.sleep(1)
            st.rerun()

    st.divider()
    st.markdown("#### 👥 **Indexed Candidates in Vector Database**")
    all_cands = get_all_candidates()
    if not all_cands:
        st.info("No candidates uploaded yet. Please drag & drop resume files above to get started.")
    else:
        table_data = []
        for c in all_cands:
            table_data.append({
                "Candidate ID": c["candidate_id"],
                "Name": c["name"],
                "Email": c["email"] or "Not Detected",
                "Phone": c["phone"] or "Not Detected",
                "Extracted Skills": ", ".join(c.get("skills", [])) or "None",
                "Filename": c["filename"]
            })
        st.dataframe(pd.DataFrame(table_data), use_container_width=True)

        col_next = st.columns([4, 1])[1]
        with col_next:
            if st.button("➡️ Proceed to Job Matching", type="primary"):
                st.session_state.current_page = 2
                st.rerun()
