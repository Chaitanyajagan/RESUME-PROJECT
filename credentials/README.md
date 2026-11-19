# Backend Credentials Vault 🔒

This folder securely stores your private credentials in the backend so they are **never exposed on the frontend Streamlit UI**.

---

### 📧 1. Gmail Sending Configuration
Configure in `credentials/credentials.env`:
```env
GMAIL_ADDRESS=yourname@gmail.com
GMAIL_APP_PASSWORD=abcd efgh ijkl mnop
```
* Generate your 16-character Google App Password at: **[https://myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)** (with 2-Step Verification enabled).
* Spaces in the 16-character code are automatically handled.

---

### 📅 2. Calendly Scheduling Link
Configure in `credentials/credentials.env`:
```env
CALENDLY_URL=https://calendly.com/your-username/30min
```
When an interview is approved, the candidate's name and email are dynamically appended to this Calendly link.

---

### 🛡️ Privacy & Security
* **Frontend Protection**: Your credentials are kept purely in the backend and are never displayed in the browser.
* **Sandbox Mode**: Available anytime to simulate dispatches risk-free without sending real emails.
