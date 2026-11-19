"""
Page 2 View: Job Description Query & ChromaDB Dense Retrieval.
Allows recruiters to enter JD or select presets, and runs semantic vector matching.
"""

import time
import streamlit as st

from matcher import get_candidate_matcher, DEFAULT_JD_TEMPLATES
from vector_store import get_vector_store

def render_page_jd():
    """Renders Page 2: Job Description Input & Vector Matching."""
    vector_store = get_vector_store()
    matcher = get_candidate_matcher()
    total_chunks = vector_store.count()

    st.markdown("""
    <div class="page-banner">
        <div>
            <div class="page-banner-title">🎯 Page 2: Job Description & Vector Search</div>
            <div class="page-banner-desc">Submit your Job Description (User Query). ChromaDB performs dense semantic retrieval across all candidate chunks to compute similarity and skill overlap.</div>
        </div>
        <span style="background: #2563EB; color: white; padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: 700;">STAGE 2</span>
    </div>
    """, unsafe_allow_html=True)

    col_jd1, col_jd2 = st.columns([1, 1])

    with col_jd1:
        st.markdown("#### **1. Choose or Customize Job Description**")
        template_name = st.selectbox(
            "Select JD Preset or Custom:",
            options=list(DEFAULT_JD_TEMPLATES.keys()) + ["Custom Job Description"]
        )
        
        if template_name != "Custom Job Description":
            default_text = DEFAULT_JD_TEMPLATES[template_name]
            st.session_state.active_job_title = template_name
        else:
            default_text = st.session_state.active_jd_text
            
        job_title_input = st.text_input("Role Title:", value=st.session_state.active_job_title)
        st.session_state.active_job_title = job_title_input
        
        jd_text_input = st.text_area(
            "Job Description Text (User Query):",
            value=default_text,
            height=260
        )
        st.session_state.active_jd_text = jd_text_input

        if st.button("🔍 Match & Rank Candidates (ChromaDB)", type="primary"):
            if total_chunks == 0:
                st.error("ChromaDB vector store is empty! Please upload resumes on Page 1 first.")
            else:
                with st.spinner("Searching ChromaDB Dense Vectors & Aggregating Candidate Evidence..."):
                    ranked = matcher.match_and_rank(jd_text_input, top_candidates=10)
                    st.session_state.ranked_candidates = ranked
                    if ranked:
                        st.session_state.selected_candidate_id = ranked[0]["candidate_id"]
                    st.success(f"Successfully ranked {len(ranked)} candidates!")
                    time.sleep(0.5)
                    st.session_state.current_page = 3
                    st.rerun()

    with col_jd2:
        st.markdown("#### **2. Search Overview**")
        st.info("""
        **How ChromaDB Dense Matching Works:**
        1. **Semantic Embeddings**: The Job Description is converted into a high-dimensional vector.
        2. **Cosine Retrieval**: ChromaDB searches section-aware chunks (Experience, Education, Skills).
        3. **Candidate Aggregation**: Chunks are grouped by Candidate ID.
        4. **Composite Rubric**: Computes a calibrated Match % (55% Vector Similarity + 45% Skill Overlap).
        """)
        if st.session_state.ranked_candidates:
            st.success(f"Currently ranked candidates: **{len(st.session_state.ranked_candidates)}**")
            if st.button("➡️ View Candidate Rankings", type="secondary"):
                st.session_state.current_page = 3
                st.rerun()
