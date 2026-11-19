"""
Page 4 View: Recruiter Review, Dynamic Calendly Link & Gmail Dispatch.
Allows recruiter decision, injects candidate-specific Calendly link, and sends emails.
"""

import time
import streamlit as st

from config import get_calendly_base_url, is_gmail_ready
from database import get_all_candidates, get_candidate, save_outbox_action, get_outbox_items
from email_service import compose_email_content, dispatch_action, build_calendly_link

def render_page_dispatch():
    """Renders Page 4: Email Dispatch & Calendly Integration."""
    st.markdown("""
    <div class="page-banner">
        <div>
            <div class="page-banner-title">✉️ Page 4: Recruiter Review & Gmail Dispatch</div>
            <div class="page-banner-desc">Approve or reject candidates. For interview approvals, a personalized Calendly scheduling link is automatically injected. Send real emails directly via Gmail!</div>
        </div>
        <span style="background: #2563EB; color: white; padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: 700;">STAGE 4</span>
    </div>
    """, unsafe_allow_html=True)

    all_candidates_list = get_all_candidates()
    if not all_candidates_list:
        st.warning("No candidates available. Go back to Page 1 to upload resumes.")
        if st.button("⬅️ Back to Page 1"):
            st.session_state.current_page = 1
            st.rerun()
        return

    active_cid = st.session_state.selected_candidate_id or all_candidates_list[0]["candidate_id"]
    cand_map = {c["candidate_id"]: f"{c['name']} ({c.get('email', 'No email')})" for c in all_candidates_list}
    
    selected_cand_id = st.selectbox(
        "Select Candidate to Email:",
        options=list(cand_map.keys()),
        format_func=lambda x: cand_map[x],
        index=list(cand_map.keys()).index(active_cid) if active_cid in cand_map else 0
    )
    cand = get_candidate(selected_cand_id)

    col_out1, col_out2 = st.columns([1, 1])

    with col_out1:
        st.markdown("#### **1. Recruiter Decision**")
        action_choice = st.radio(
            "Select Hiring Action:",
            options=["Interview", "Rejection", "Under Review"],
            format_func=lambda x: {
                "Interview": "🟢 Approve for Interview (Attach Calendly Link)",
                "Rejection": "🔴 Send Polite Rejection Notice",
                "Under Review": "🟡 Keep Under Review (Status Notification)"
            }[x]
        )

        job_title_input = st.text_input("Role Title for Email:", value=st.session_state.active_job_title)

        # Dynamic Calendly Link Generation
        custom_calendly = get_calendly_base_url()
        if action_choice == "Interview":
            full_calendly = build_calendly_link(custom_calendly, cand["name"], cand["email"])
            st.success(f"**Generated Calendly Link:**\n\n[{full_calendly}]({full_calendly})")
        else:
            st.caption("Calendly link is not included for rejection/review notices.")

        # Generate Email Draft
        draft = compose_email_content(
            candidate=cand,
            action_type=action_choice,
            job_title=job_title_input,
            custom_calendly=custom_calendly
        )

        subject_input = st.text_input("Email Subject:", value=draft["subject"])
        body_input = st.text_area("Email Body (Editable):", value=draft["body"], height=250)

    with col_out2:
        st.markdown("#### **2. Dispatch via Gmail & Calendly**")
        
        gmail_ready = is_gmail_ready()
        
        # Active provider selection
        provider_mode = st.radio(
            "Select Dispatch Mode:",
            options=["🚀 Live Gmail SMTP", "🧪 Sandbox Simulator (Demo Mode)"],
            index=0 if gmail_ready else 1,
            help="Choose Live Gmail to deliver real emails to candidate inboxes, or Sandbox Simulator to test risk-free."
        )
        active_provider = "gmail" if "Live Gmail" in provider_mode else "sandbox"

        st.markdown(f"""
        <div style="background: #1E293B; border-radius: 10px; padding: 14px; border: 1px solid #334155; margin-bottom: 16px; color: #F8FAFC;">
            <div style="margin-bottom: 6px;"><strong style="color: #94A3B8;">Recipient:</strong> <span style="color: #F8FAFC; font-weight: 600;">{cand['name']} &lt;{cand['email'] or 'Missing Email'}&gt;</span></div>
            <div style="margin-bottom: 6px;"><strong style="color: #94A3B8;">Phone:</strong> <span style="color: #F8FAFC;">{cand['phone'] or 'N/A'}</span></div>
            <div style="margin-bottom: 6px;"><strong style="color: #94A3B8;">Action:</strong> <code style="background: #334155; color: #60A5FA; padding: 2px 6px; border-radius: 4px;">{action_choice}</code></div>
            <div style="margin-bottom: 6px;"><strong style="color: #94A3B8;">Email Service:</strong> <code style="background: #334155; color: {'#34D399' if active_provider == 'gmail' else '#F59E0B'}; padding: 2px 6px; border-radius: 4px;">{'GMAIL (LIVE SMTP)' if active_provider == 'gmail' else 'SANDBOX SIMULATOR'}</code></div>
            <div><strong style="color: #94A3B8;">Calendly Embedded:</strong> <span style="color: #F8FAFC;">{'Yes' if action_choice == 'Interview' else 'No'}</span></div>
        </div>
        """, unsafe_allow_html=True)

        if not cand.get("email"):
            st.error("⚠️ Candidate does not have an email address detected from the resume!")

        # Direct Approve & Send Button
        send_button_label = "🚀 Dispatch Live Email via Gmail" if active_provider == "gmail" else "🚀 Dispatch Email (Sandbox Mode)"
        if st.button(send_button_label, type="primary"):
            draft_item = {
                "candidate_id": cand["candidate_id"],
                "candidate_name": cand["name"],
                "candidate_email": cand["email"],
                "candidate_phone": cand["phone"],
                "action_type": action_choice,
                "subject": subject_input,
                "body": body_input,
                "calendly_link": draft["calendly_link"],
                "status": "Approved",
                "provider": active_provider
            }
            action_id = save_outbox_action(draft_item)
            
            with st.spinner(f"Connecting to {'smtp.gmail.com' if active_provider == 'gmail' else 'Sandbox'} and sending email..."):
                success, receipt = dispatch_action(
                    action_id=action_id,
                    action_data=draft_item,
                    provider=active_provider
                )
                
            if success:
                st.success(f"✅ Email successfully dispatched!\n\n**Receipt:** `{receipt}`")
                time.sleep(2.0)
                st.rerun()
            else:
                st.error(f"❌ Dispatch failed: {receipt}")
                if active_provider == "gmail":
                    st.info("💡 **Instant Demo Alternative:** You can switch 'Select Dispatch Mode' above to **🧪 Sandbox Simulator (Demo Mode)** to generate verified delivery receipts and test without external mail servers.")

        # Recent Outbox Activity
        st.markdown("##### **Recent Delivery Receipts**")
        outbox_items = get_outbox_items()
        if outbox_items:
            for item in outbox_items[:3]:
                st.caption(f"• **{item['candidate_name']}** ({item['action_type']}) → Status: `{item['status']}` ({item.get('provider', '').upper()})")
                if item.get("delivery_receipt"):
                    st.code(item["delivery_receipt"], language="text")
