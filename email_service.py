import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from urllib.parse import quote
from datetime import datetime
from typing import Dict, Any, Tuple

from config import (
    get_calendly_base_url,
    get_default_provider,
    get_smtp_config,
    get_sendgrid_config,
    get_twilio_config
)
from database import save_outbox_action, update_outbox_status, update_candidate_status, log_audit

def build_calendly_link(base_url: str, candidate_name: str, candidate_email: str) -> str:
    """Construct personalized Calendly booking link with candidate URL parameters."""
    if not base_url:
        base_url = get_calendly_base_url()
    clean_base = base_url.rstrip("/")
    params = f"?name={quote(candidate_name)}&email={quote(candidate_email)}"
    return f"{clean_base}{params}"

def compose_email_content(candidate: Dict[str, Any], action_type: str, job_title: str = "Target Position", custom_calendly: str = "") -> Dict[str, Any]:
    """
    Draft personalized email based on recruiter response:
    - If 'Interview': Generates invitation with embedded Calendly booking link.
    - If 'Rejection': Generates polite professional rejection letter without Calendly.
    - If 'Under Review': Generates update acknowledging progress.
    """
    cand_name = candidate.get("name", "Candidate")
    cand_email = candidate.get("email", "")
    cand_phone = candidate.get("phone", "")
    cand_id = candidate.get("candidate_id", "")
    
    calendly_url = ""
    active_calendly = custom_calendly or get_calendly_base_url()
    
    if action_type == "Interview":
        calendly_url = build_calendly_link(active_calendly, cand_name, cand_email)
        subject = f"Interview Invitation: {job_title} at EDUKRON Talent"
        body = f"""Dear {cand_name},

Thank you for your interest in the {job_title} role at EDUKRON Talent. 

Our hiring committee reviewed your credentials and background, and we are very impressed by your qualifications. We would love to invite you for an initial 30-minute technical and cultural alignment conversation.

Please use the dedicated Calendly link below to choose a time that suits your schedule:

👉 Schedule Your Interview:
{calendly_url}

During this discussion, we will cover:
1. Your previous experience and key projects
2. Deep dive into technical problem solving
3. Questions you have about our team, culture, and roadmap

If you need any adjustments or encounter any scheduling conflicts, please reply directly to this email.

Best regards,

Talent Acquisition Team
EDUKRON GenAI HR Operations
"""
    elif action_type == "Rejection":
        subject = f"Update regarding your application for {job_title} at EDUKRON"
        body = f"""Dear {cand_name},

Thank you for taking the time to apply for the {job_title} position with EDUKRON Talent. We appreciate your interest in our organization.

After careful review of all applications against our current headcount needs, we have decided to proceed with other candidates whose experience more closely matches the specific technical requirements for this round.

We will keep your resume in our talent network for future opportunities that align with your background. We wish you every success in your career journey.

Sincerely,

Talent Acquisition Team
EDUKRON GenAI HR Operations
"""
    else:  # Under Review
        subject = f"Application Status: {job_title} - Under Review"
        body = f"""Dear {cand_name},

We are writing to let you know that your resume has been successfully indexed and shortlisted for the {job_title} role. 

Our recruitment team is currently finishing internal assessments and expects to share next steps within 2 to 3 business days.

Thank you for your patience!

Best regards,

Talent Acquisition Team
EDUKRON GenAI HR Operations
"""

    return {
        "candidate_id": cand_id,
        "candidate_name": cand_name,
        "candidate_email": cand_email,
        "candidate_phone": cand_phone,
        "action_type": action_type,
        "subject": subject,
        "body": body,
        "calendly_link": calendly_url,
        "status": "Draft",
        "provider": get_default_provider()
    }

class EmailDispatcher:
    @staticmethod
    def send_via_sandbox(to_email: str, subject: str, body: str) -> Tuple[bool, str]:
        """Sandbox simulation mode: verifies payload, records simulated dispatch."""
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        receipt = f"SANDBOX_OK: Simulated dispatch to {to_email} at {timestamp}. (No external Gmail API consumed)"
        return True, receipt

    @staticmethod
    def send_via_gmail(to_email: str, subject: str, body: str, calendly_link: str = "") -> Tuple[bool, str]:
        """
        Dispatch real email via Gmail SMTP with dual TLS/SSL port fallback (587 -> 465)
        and formatted HTML + plain-text fallback.
        """
        cfg = get_smtp_config()
        user = cfg.get("user")
        password = cfg.get("password")
        from_email = cfg.get("from_email") or user
        host = cfg.get("host") or "smtp.gmail.com"

        if not user or not password:
            return False, "Gmail Error: Please configure GMAIL_ADDRESS and GMAIL_APP_PASSWORD in credentials/credentials.env"

        # Validate recipient email format
        if not to_email or "@" not in to_email:
            return False, f"Gmail Error: Invalid candidate email address '{to_email}'."

        # Create multi-part message (plain text + rich HTML)
        msg = MIMEMultipart("alternative")
        msg["From"] = f"EDUKRON Talent Acquisition <{from_email}>"
        msg["To"] = to_email
        msg["Subject"] = subject

        # Plain-text version
        msg.attach(MIMEText(body, "plain", "utf-8"))

        # HTML formatted version
        html_body = body.replace("\n", "<br>")
        if calendly_link:
            button_html = f"""
            <div style="margin: 24px 0;">
                <a href="{calendly_link}" style="background-color: #2563EB; color: #FFFFFF; padding: 12px 24px; text-decoration: none; border-radius: 8px; font-weight: bold; display: inline-block;">
                    📅 Schedule Interview on Calendly
                </a>
            </div>
            """
            html_body = html_body.replace(calendly_link, button_html)

        full_html = f"""
        <!DOCTYPE html>
        <html>
        <head><meta charset="utf-8"></head>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #1E293B; line-height: 1.6; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px; padding: 28px; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
                <div style="font-size: 18px; font-weight: bold; color: #2563EB; margin-bottom: 16px;">EDUKRON Talent Acquisition</div>
                <div style="font-size: 14px; color: #334155;">{html_body}</div>
                <hr style="border: none; border-top: 1px solid #E2E8F0; margin: 24px 0;">
                <div style="font-size: 11px; color: #94A3B8;">EDUKRON HR Automation System • Automated Recruitment Gateway</div>
            </div>
        </body>
        </html>
        """
        msg.attach(MIMEText(full_html, "html", "utf-8"))

        # Attempt 1: Port 587 with STARTTLS
        try:
            server = smtplib.SMTP(host, 587, timeout=12)
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(user, password)
            server.send_message(msg)
            server.quit()
            timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
            return True, f"GMAIL_SUCCESS: Delivered to {to_email} via smtp.gmail.com:587 (TLS) at {timestamp}"
        except (smtplib.SMTPAuthenticationError, smtplib.SMTPServerDisconnected) as e587:
            # Fallback Attempt 2: Port 465 with SSL (bypasses restricted 587 ISP firewalls)
            try:
                server = smtplib.SMTP_SSL(host, 465, timeout=12)
                server.login(user, password)
                server.send_message(msg)
                server.quit()
                timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
                return True, f"GMAIL_SUCCESS: Delivered to {to_email} via smtp.gmail.com:465 (SSL) at {timestamp}"
            except (smtplib.SMTPAuthenticationError, smtplib.SMTPServerDisconnected):
                return False, (
                    "Gmail Authentication Rejected (Google SMTP 535 Bad Credentials). "
                    "Google mail servers do not accept personal email passwords for third-party automated SMTP. "
                    "Google requires a dedicated 16-character Google App Password. "
                    "To fix this: (1) Turn on 2-Step Verification at https://myaccount.google.com/signinoptions/two-step-verification, "
                    "(2) Generate an App Password at https://myaccount.google.com/apppasswords, "
                    "(3) Put the generated 16-character code in credentials/credentials.env as GMAIL_APP_PASSWORD. "
                    "Alternatively, select Sandbox mode to test and demonstrate the pipeline immediately without sending real emails."
                )
            except Exception as e465:
                return False, f"Gmail Connection Error: Port 587 failed ({str(e587)}) and Port 465 failed ({str(e465)}). Please check internet connection and credentials."
        except Exception as e587:
            # Fallback Attempt 2: Port 465 with SSL (bypasses restricted 587 ISP firewalls)
            try:
                server = smtplib.SMTP_SSL(host, 465, timeout=12)
                server.login(user, password)
                server.send_message(msg)
                server.quit()
                timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
                return True, f"GMAIL_SUCCESS: Delivered to {to_email} via smtp.gmail.com:465 (SSL) at {timestamp}"
            except (smtplib.SMTPAuthenticationError, smtplib.SMTPServerDisconnected):
                return False, (
                    "Gmail Authentication Rejected (535 Bad Credentials). "
                    "Google closed the connection because personal account passwords cannot be used for SMTP. "
                    "Please generate a 16-character Google App Password at https://myaccount.google.com/apppasswords."
                )
            except Exception as e465:
                return False, f"Gmail Connection Error: Port 587 failed ({str(e587)}) and Port 465 failed ({str(e465)}). Please check internet connection and credentials."

    @staticmethod
    def send_via_sendgrid(to_email: str, subject: str, body: str) -> Tuple[bool, str]:
        """Dispatch email via SendGrid API using backend credentials."""
        cfg = get_sendgrid_config()
        key = cfg.get("api_key")
        sender = cfg.get("from_email") or "recruiter@edukron-ats.com"

        if not key:
            return False, "SendGrid Error: SENDGRID_API_KEY is not configured in credentials/credentials.env"

        try:
            from sendgrid import SendGridAPIClient
            from sendgrid.helpers.mail import Mail

            message = Mail(
                from_email=sender,
                to_emails=to_email,
                subject=subject,
                plain_text_content=body
            )
            sg = SendGridAPIClient(key)
            response = sg.send(message)
            receipt = f"SENDGRID_SUCCESS: Status {response.status_code}, MsgID: {response.headers.get('X-Message-Id', 'unknown')}"
            return True, receipt
        except Exception as e:
            return False, f"SendGrid Exception: {str(e)}"

    @staticmethod
    def send_via_twilio(to_phone_or_email: str, subject: str, body: str) -> Tuple[bool, str]:
        """Dispatch notification via Twilio using backend credentials."""
        cfg = get_twilio_config()
        sid = cfg.get("account_sid")
        token = cfg.get("auth_token")
        from_phone = cfg.get("from_number")

        if not sid or not token:
            return False, "Twilio Error: Missing TWILIO_ACCOUNT_SID or TWILIO_AUTH_TOKEN in credentials/credentials.env"

        try:
            from twilio.rest import Client
            client = Client(sid, token)
            
            if to_phone_or_email.startswith("+") or any(c.isdigit() for c in to_phone_or_email):
                clean_phone = "".join(c for c in to_phone_or_email if c.isdigit() or c == "+")
                if not clean_phone.startswith("+"):
                    clean_phone = "+1" + clean_phone
                sms_message = f"{subject}\n{body[:120]}...\nCheck email for Calendly link."
                msg = client.messages.create(
                    body=sms_message,
                    from_=from_phone,
                    to=clean_phone
                )
                receipt = f"TWILIO_SMS_SUCCESS: Message SID {msg.sid} sent to {clean_phone}"
                return True, receipt
            else:
                return False, "Twilio Error: Destination is not a valid phone number format."
        except Exception as e:
            return False, f"Twilio Exception: {str(e)}"

def dispatch_action(action_id: int, action_data: Dict[str, Any], provider: str = "gmail") -> Tuple[bool, str]:
    """Execute outbox action dispatch and record audit state."""
    to_email = action_data.get("candidate_email", "")
    to_phone = action_data.get("candidate_phone", "")
    subject = action_data.get("subject", "EDUKRON Talent Update")
    body = action_data.get("body", "")
    calendly_link = action_data.get("calendly_link", "")
    action_type = action_data.get("action_type", "Interview")
    cand_id = action_data.get("candidate_id", "")
    
    if not to_email and not to_phone:
        err = "Dispatch Failed: Candidate has neither an email nor phone number."
        update_outbox_status(action_id, "Failed", err)
        return False, err
        
    provider = provider.lower()
    success = False
    receipt = ""
    
    if provider in ("gmail", "smtp"):
        success, receipt = EmailDispatcher.send_via_gmail(to_email, subject, body, calendly_link)
    elif provider == "sendgrid":
        success, receipt = EmailDispatcher.send_via_sendgrid(to_email, subject, body)
    elif provider == "twilio":
        target = to_phone if to_phone else to_email
        success, receipt = EmailDispatcher.send_via_twilio(target, subject, body)
    elif provider == "sandbox":
        success, receipt = EmailDispatcher.send_via_sandbox(to_email or to_phone, subject, body)
    else:
        # Default to Gmail or Sandbox if Gmail credentials are not set
        cfg = get_smtp_config()
        if cfg["user"] and cfg["password"]:
            success, receipt = EmailDispatcher.send_via_gmail(to_email, subject, body, calendly_link)
        else:
            success, receipt = EmailDispatcher.send_via_sandbox(to_email or to_phone, subject, body)

    status = "Sent" if success else "Failed"
    update_outbox_status(action_id, status, receipt)
    
    if success:
        if action_type == "Interview":
            update_candidate_status(cand_id, "Interview Scheduled")
        elif action_type == "Rejection":
            update_candidate_status(cand_id, "Rejected")
        elif action_type == "Under Review":
            update_candidate_status(cand_id, "Shortlisted")
            
        log_audit("EMAIL_SENT", f"Action #{action_id} successfully dispatched via {provider.upper()} to {to_email or to_phone}")
    else:
        log_audit("EMAIL_FAILED", f"Action #{action_id} failed via {provider.upper()}: {receipt}")
        
    return success, receipt
