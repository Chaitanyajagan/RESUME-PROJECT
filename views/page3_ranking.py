"""
Page 3 View: Candidate Ranking, Grounded Assessment & AI Questions.
Displays leaderboard, skills breakdown, tailored questions, and evidence citations.
"""

import streamlit as st
from database import get_candidate
from matcher import get_candidate_matcher

# Grounded Assessment Dialog Modal
@st.dialog("Candidate Grounded Assessment & Interview Questions", width="large")
def show_candidate_assessment_dialog(cand_id: str):
    """Interactive modal showing complete candidate dossier and AI questions."""
    cand = get_candidate(cand_id)
    if not cand:
        st.error("Candidate not found.")
        return

    matcher = get_candidate_matcher()
    score = cand.get("match_score", 0)
    badge_color = "#10B981" if score >= 75 else "#F59E0B" if score >= 50 else "#EF4444"

    st.markdown(f"""
    <div style="background: #1E293B; border: 1px solid #334155; border-radius: 12px; padding: 18px; margin-bottom: 16px; color: #F8FAFC;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
            <span style="font-size: 1.4rem; font-weight: 800; color: #60A5FA;">{cand['name']}</span>
            <span style="background-color: {badge_color}; color: white; padding: 4px 14px; border-radius: 16px; font-weight: 800; font-size: 1rem;">
                {score}% Match
            </span>
        </div>
        <div style="font-size: 0.95rem; color: #CBD5E1; margin-bottom: 6px;">
            <strong>📧 Email:</strong> {cand['email'] or 'Not Detected'} &nbsp;|&nbsp; 
            <strong>📞 Phone:</strong> {cand['phone'] or 'Not Detected'}
        </div>
        <div style="font-size: 0.85rem; color: #94A3B8;">
            <strong>File:</strong> <code>{cand.get('filename', '')}</code> &nbsp;|&nbsp;
            <strong>Status:</strong> <span style="background: #334155; padding: 2px 8px; border-radius: 6px; color: #F8FAFC;">{cand.get('status', 'New')}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 1. All Extracted Skills
    st.markdown("#### 🛠️ **All Extracted Skills**")
    skills = cand.get("skills", [])
    if skills:
        st.markdown(" ".join([f'<span class="skill-tag">{s}</span>' for s in skills]), unsafe_allow_html=True)
    else:
        st.caption("No specific skills identified.")

    st.markdown("<br>", unsafe_allow_html=True)

    # 2. AI Tailored Interview Questions
    st.markdown("#### 🎯 **Tailored AI Interview Questions**")
    st.caption("Probing candidate strengths and bridging identified skill gaps:")
    questions = matcher.generate_interview_questions(
        candidate_name=cand["name"],
        matched_skills=skills,
        missing_skills=["Cloud Architecture", "Distributed Systems"],
        category=cand.get("category", "General")
    )
    for i, q in enumerate(questions, 1):
        st.info(f"**Q{i}:** {q}")

    # 3. Grounded Evidence from ChromaDB
    st.markdown("#### 📍 **Grounded Evidence from ChromaDB Vector Chunks**")
    evidence = cand.get("evidence", [])
    if evidence:
        for ev in evidence:
            with st.expander(f"Section: {ev.get('section', 'General')} (Similarity: {ev.get('similarity', 'N/A')}%)", expanded=True):
                st.write(f'"{ev.get("text_snippet", "")}"')
    else:
        st.caption("No semantic evidence chunks available.")

    st.divider()
    if st.button("✉️ Proceed to Gmail Dispatch for this Candidate", type="primary", use_container_width=True, key=f"dlg_btn_dispatch_{cand['candidate_id']}"):
        st.session_state.selected_candidate_id = cand["candidate_id"]
        st.session_state.current_page = 4
        st.rerun()

def render_page_ranking():
    """Renders Page 3: Candidate Leaderboard & Grounded Assessment."""
    matcher = get_candidate_matcher()
    ranked_list = st.session_state.ranked_candidates

    st.markdown("""
    <div class="page-banner">
        <div>
            <div class="page-banner-title">📊 Page 3: Candidate Ranking & Grounded Assessment</div>
            <div class="page-banner-desc">Inspect ranked candidates, match percentages, extracted Phone & Email, skill gap analysis, and tailored AI interview questions.</div>
        </div>
        <span style="background: #2563EB; color: white; padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: 700;">STAGE 3</span>
    </div>
    """, unsafe_allow_html=True)

    if not ranked_list:
        st.warning("No candidates ranked yet! Go back to Page 2 to match against a Job Description.")
        if st.button("⬅️ Back to Job Description"):
            st.session_state.current_page = 2
            st.rerun()
        return

    col_rank1, col_rank2 = st.columns([1, 1])

    with col_rank1:
        st.markdown("#### **Leaderboard & Ranked Candidates**")
        for idx, cand in enumerate(ranked_list):
            score = cand["match_score"]
            badge_color = "#10B981" if score >= 75 else "#F59E0B" if score >= 50 else "#EF4444"
            is_active = cand["candidate_id"] == st.session_state.selected_candidate_id

            st.markdown(f"""
            <div class="candidate-card" style="border-left: 4px solid {badge_color}; {'border: 2px solid #3B82F6;' if is_active else ''}">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <span style="font-size: 1.15rem; font-weight: 700; color: #F8FAFC;">#{idx+1} {cand['name']}</span>
                    </div>
                    <div style="background-color: {badge_color}; color: white; padding: 3px 10px; border-radius: 14px; font-weight: 800; font-size: 0.9rem;">
                        {score}% Match
                    </div>
                </div>
                <div style="margin-top: 6px; font-size: 0.86rem; color: #CBD5E1;">
                    <strong style="color: #F8FAFC;">📧 Email:</strong> {cand['email'] or 'Not Detected'} &nbsp;|&nbsp; 
                    <strong style="color: #F8FAFC;">📞 Phone:</strong> {cand['phone'] or 'Not Detected'}
                </div>
                <div style="margin-top: 6px;">
                    <strong style="font-size: 0.8rem; color: #94A3B8;">Matched Skills:</strong> 
                    {' '.join([f'<span class="skill-tag">{s}</span>' for s in cand['matched_skills']]) if cand['matched_skills'] else '<span style="font-size: 0.8rem; color: #64748B;">None identified</span>'}
                </div>
            </div>
            """, unsafe_allow_html=True)

            btn_c1, btn_c2 = st.columns([1, 1])
            with btn_c1:
                if st.button(f"🔍 Inspect Assessment", key=f"sel_{cand['candidate_id']}", use_container_width=True):
                    st.session_state.selected_candidate_id = cand["candidate_id"]
                    show_candidate_assessment_dialog(cand["candidate_id"])
            with btn_c2:
                if st.button(f"✉️ Proceed to Dispatch", key=f"act_{cand['candidate_id']}", use_container_width=True):
                    st.session_state.selected_candidate_id = cand["candidate_id"]
                    st.session_state.current_page = 4
                    st.rerun()

    with col_rank2:
        st.markdown("#### **Grounded Assessment & Interview Questions**")
        active_cid = st.session_state.selected_candidate_id or ranked_list[0]["candidate_id"]
        cand = get_candidate(active_cid)

        if cand:
            st.markdown(f"""
            <div style="background: #1E293B; border: 1px solid #334155; border-radius: 12px; padding: 16px; margin-bottom: 16px; color: #F8FAFC;">
                <div style="font-size: 1.2rem; font-weight: 700; color: #60A5FA; margin-bottom: 4px;">{cand['name']}</div>
                <div style="font-size: 0.88rem; color: #CBD5E1; margin-bottom: 8px;">
                    <strong>📧 Email:</strong> {cand['email'] or 'Not Provided'} &nbsp;|&nbsp;
                    <strong>📞 Phone:</strong> {cand['phone'] or 'Not Provided'}
                </div>
                <div><strong>Current Status:</strong> <span style="background: #334155; padding: 2px 8px; border-radius: 6px; font-size: 12px;">{cand['status']}</span></div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("##### **🛠️ All Extracted Skills**")
            if cand.get("skills"):
                st.markdown(" ".join([f'<span class="skill-tag">{s}</span>' for s in cand["skills"]]), unsafe_allow_html=True)
            else:
                st.caption("No skills identified.")

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("##### **🎯 Tailored AI Interview Questions**")
            st.caption("Probing strengths and bridging identified skill gaps:")
            questions = matcher.generate_interview_questions(
                candidate_name=cand["name"],
                matched_skills=cand.get("skills", []),
                missing_skills=["Cloud Architecture", "Distributed Systems"],
                category=cand.get("category", "General")
            )
            for i, q in enumerate(questions, 1):
                st.info(f"**Q{i}:** {q}")

            st.markdown("##### **📍 Evidence Citations from ChromaDB**")
            evidence = cand.get("evidence", [])
            if evidence:
                for ev in evidence:
                    with st.expander(f"Section: {ev.get('section', 'General')} (Similarity: {ev.get('similarity', 'N/A')}%)", expanded=False):
                        st.write(f'"{ev.get("text_snippet", "")}"')

            if st.button("➡️ Proceed to Review & Gmail Dispatch", type="primary", use_container_width=True):
                st.session_state.selected_candidate_id = cand["candidate_id"]
                st.session_state.current_page = 4
                st.rerun()
