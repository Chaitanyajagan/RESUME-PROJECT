# EDUKRON Resume Intelligence & HR Automation

A production-grade, modular GenAI ATS (Applicant Tracking System) built with **Streamlit** and **ChromaDB**, inspired by modern AI recruiting architecture and handwritten design requirements.

---

## 🌟 Dynamic 4-Stage Architecture

The application has been restructured into **Dynamic Web Pages** guiding the recruiter step-by-step:

1. **Stage 1: 📥 Resume Intake & OCR Parsing**
   - Clean drag-and-drop resume uploader (PDF, DOCX, TXT).
   - Local **Tesseract OCR Fallback** for scanned image resumes.
   - Extracts candidate Name, Phone Number, and Email ID.
   - Generates section-aware chunks and indexes them into ChromaDB.

2. **Stage 2: 🎯 Job Description & Vector Search**
   - Recruiter submits a custom Job Description or selects from industry presets.
   - Executes dense semantic retrieval against candidate vector chunks in ChromaDB.

3. **Stage 3: 📊 Candidate Ranking & Grounded Assessment**
   - Composite scoring rubric: **Semantic Vector Similarity (55%) + Skill Overlap (45%)**.
   - Displays ranked candidates with extracted Phone, Email, matched skills, and missing skill gaps.
   - Grounded evidence excerpts cited directly from resume chunks.
   - AI-generated customized technical and behavioral interview questions tailored to each candidate.

4. **Stage 4: ✉️ Recruiter Review & Gmail Dispatch**
   - Recruiter hiring decision gate:
     - **Approve for Interview**: Automatically generates and injects personalized **Calendly booking links** (`https://calendly.com/.../?name=...&email=...`).
     - **Rejection**: Generates encouraging rejection notices (Calendly link excluded).
   - Real **Gmail Sending** with dual TLS (Port 587) and SSL (Port 465) fallback.
   - Rich HTML email formatting with interactive Calendly button.
   - Zero-risk **Sandbox Mode** fallback when credentials are not yet entered.

---

## 🔒 Backend Credentials & Gmail Setup

Sensitive credentials are stored in `credentials/credentials.env` and **never displayed on the frontend**:

```env
# Gmail SMTP Configuration
GMAIL_ADDRESS=yourname@gmail.com
GMAIL_APP_PASSWORD=abcdefghijklmnop

# Calendly Scheduling Link
CALENDLY_URL=https://calendly.com/talent-acquisition/technical-interview

# Provider
EMAIL_PROVIDER=gmail
```

Generate a 16-character Google App Password at: **https://myaccount.google.com/apppasswords**

---

## 🚀 How to Run

The app is running live at:
👉 **[http://localhost:8501](http://localhost:8501)**

To start anytime:
```powershell
.\run.bat
```
or
```powershell
.\.venv\Scripts\streamlit.exe run app.py
```

To run the automated integration test:
```powershell
.\.venv\Scripts\python.exe test_pipeline.py
```
