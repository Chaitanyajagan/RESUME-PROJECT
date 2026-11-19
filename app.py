"""
EDUKRON AI Resume Intelligence & HR Automation System.
Main Application Entrypoint and Dynamic Router.
"""

import streamlit as st

from database import init_db, clear_all_data
from matcher import DEFAULT_JD_TEMPLATES
from vector_store import get_vector_store
from views import (
    apply_custom_styles,
    render_phase_wheel,
    render_page_upload,
    render_page_jd,
    render_page_ranking,
    render_page_dispatch
)

# 1. Page Configuration
st.set_page_config(
    page_title="EDUKRON - AI Resume Intelligence & HR Automation",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 2. Global Styles & Theme Injection
apply_custom_styles()

def main():
    """Main Application Entrypoint and Dynamic Page Router."""
    # System Initialization
    init_db()
    vector_store = get_vector_store()
    
    # Initialize Session State Defaults
    if "current_page" not in st.session_state:
        st.session_state.current_page = 1
    if "ranked_candidates" not in st.session_state:
        st.session_state.ranked_candidates = []
    if "selected_candidate_id" not in st.session_state:
        st.session_state.selected_candidate_id = None
    if "active_jd_text" not in st.session_state:
        st.session_state.active_jd_text = DEFAULT_JD_TEMPLATES["Senior Full-Stack Engineer"]
    if "active_job_title" not in st.session_state:
        st.session_state.active_job_title = "Senior Full-Stack Engineer"

    # Header Bar with Title and System Reset
    head_col1, head_col2 = st.columns([5, 1])
    with head_col1:
        st.markdown('<div class="main-title">EDUKRON Resume Intelligence & HR Automation</div>', unsafe_allow_html=True)
        st.markdown('<div class="sub-title">Parse Resumes • ChromaDB Vector Retrieval • Grounded Ranking • Gmail Dispatch with Dynamic Calendly</div>', unsafe_allow_html=True)
    with head_col2:
        if st.button("🔄 Reset All", type="secondary", help="Clear all candidates and reset ChromaDB"):
            vector_store.reset_collection()
            clear_all_data()
            st.session_state.ranked_candidates = []
            st.session_state.selected_candidate_id = None
            st.session_state.current_page = 1
            st.success("All data reset.")
            st.rerun()

    # Active Dynamic Workflow Progress Wheel (SVG)
    render_phase_wheel(st.session_state.current_page)

    # Top Stage Stepper Navigation
    st_cols = st.columns(4)
    stages = [
        (1, "1. 📥 Resume Upload"),
        (2, "2. 🎯 Job Description"),
        (3, "3. 📊 Candidate Ranking"),
        (4, "4. ✉️ Gmail Dispatch")
    ]
    for idx, (num, name) in enumerate(stages):
        with st_cols[idx]:
            is_active = (st.session_state.current_page == num)
            btn_type = "primary" if is_active else "secondary"
            if st.button(name, key=f"top_nav_{num}", type=btn_type, use_container_width=True):
                st.session_state.current_page = num
                st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # Dynamic Page Routing
    if st.session_state.current_page == 1:
        render_page_upload()
    elif st.session_state.current_page == 2:
        render_page_jd()
    elif st.session_state.current_page == 3:
        render_page_ranking()
    elif st.session_state.current_page == 4:
        render_page_dispatch()

if __name__ == "__main__":
    main()
