"""
Views package for EDUKRON ATS Streamlit application.
Modularized pages for upload, job matching, candidate ranking, and dispatch.
"""

from views.styles import apply_custom_styles, render_phase_wheel
from views.page1_upload import render_page_upload
from views.page2_jd import render_page_jd
from views.page3_ranking import render_page_ranking, show_candidate_assessment_dialog
from views.page4_dispatch import render_page_dispatch

__all__ = [
    "apply_custom_styles",
    "render_phase_wheel",
    "render_page_upload",
    "render_page_jd",
    "render_page_ranking",
    "show_candidate_assessment_dialog",
    "render_page_dispatch"
]
