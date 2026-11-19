import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
CREDENTIALS_DIR = BASE_DIR / "credentials"
CREDENTIALS_FILE = CREDENTIALS_DIR / "credentials.env"
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "resumes"
CHROMA_PERSIST_DIR = DATA_DIR / "chroma_db"
DATABASE_PATH = DATA_DIR / "ats_pipeline.db"

# Ensure directories exist
CREDENTIALS_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
CHROMA_PERSIST_DIR.mkdir(parents=True, exist_ok=True)

# 1. Load backend credentials from credentials/credentials.env if present
if CREDENTIALS_FILE.exists():
    load_dotenv(dotenv_path=CREDENTIALS_FILE, override=True)
else:
    load_dotenv()

# Function to refresh environment variables from backend credentials file
def reload_credentials():
    if CREDENTIALS_FILE.exists():
        load_dotenv(dotenv_path=CREDENTIALS_FILE, override=True)

# ChromaDB Settings
CHROMA_COLLECTION_NAME = os.getenv("CHROMA_COLLECTION_NAME", "ats_resume_intelligence")

# Tesseract OCR Path Auto-detection
def get_tesseract_cmd() -> str:
    env_cmd = os.getenv("TESSERACT_CMD")
    if env_cmd and os.path.exists(env_cmd):
        return env_cmd
    
    common_paths = [
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\Tesseract-OCR\tesseract.exe"),
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    ]
    for path in common_paths:
        if os.path.exists(path):
            return path
    return "tesseract"

TESSERACT_CMD = get_tesseract_cmd()

# Backend Helper: Calendly URL
def get_calendly_base_url() -> str:
    reload_credentials()
    return os.getenv("CALENDLY_URL", "https://calendly.com/talent-acquisition/technical-interview").strip()

CALENDLY_BASE_URL = get_calendly_base_url()

# Gmail & SMTP Configuration
def get_smtp_config():
    reload_credentials()
    # Support both GMAIL_ADDRESS and SMTP_USER, GMAIL_APP_PASSWORD and SMTP_PASSWORD
    user = os.getenv("GMAIL_ADDRESS", "").strip() or os.getenv("SMTP_USER", "").strip()
    password = os.getenv("GMAIL_APP_PASSWORD", "").strip() or os.getenv("SMTP_PASSWORD", "").strip()
    # Remove any copied spaces from Google 16-character app password (e.g. 'abcd efgh ijkl mnop' -> 'abcdefghijklmnop')
    password = password.replace(" ", "")
    
    host = os.getenv("SMTP_HOST", "smtp.gmail.com").strip()
    port = int(os.getenv("SMTP_PORT", "587"))
    from_email = os.getenv("SMTP_FROM_EMAIL", "").strip() or user
    use_tls = os.getenv("SMTP_USE_TLS", "true").lower() in ("true", "1", "yes")

    return {
        "host": host,
        "port": port,
        "user": user,
        "password": password,
        "from_email": from_email,
        "use_tls": use_tls
    }

# Email & Notification Provider Settings
# Options: "gmail", "sandbox", "smtp", "sendgrid", "twilio"
def get_default_provider() -> str:
    reload_credentials()
    # If Gmail credentials are provided, default to Gmail SMTP!
    smtp_cfg = get_smtp_config()
    if smtp_cfg["user"] and smtp_cfg["password"]:
        return "gmail"
    return os.getenv("EMAIL_PROVIDER", "gmail").strip().lower()

EMAIL_PROVIDER = get_default_provider()

# SendGrid Configuration
def get_sendgrid_config():
    reload_credentials()
    return {
        "api_key": os.getenv("SENDGRID_API_KEY", "").strip(),
        "from_email": os.getenv("SENDGRID_FROM_EMAIL", "recruiter@edukron-ats.com").strip()
    }

# Twilio Configuration
def get_twilio_config():
    reload_credentials()
    return {
        "account_sid": os.getenv("TWILIO_ACCOUNT_SID", "").strip(),
        "auth_token": os.getenv("TWILIO_AUTH_TOKEN", "").strip(),
        "from_number": os.getenv("TWILIO_FROM_NUMBER", "").strip()
    }

# Backend Secret Presence Indicators (For frontend badges without revealing raw secrets)
def is_gmail_ready() -> bool:
    cfg = get_smtp_config()
    return bool(cfg["user"] and cfg["password"])

def is_smtp_ready() -> bool:
    return is_gmail_ready()

def is_sendgrid_ready() -> bool:
    cfg = get_sendgrid_config()
    return bool(cfg["api_key"])

def is_twilio_ready() -> bool:
    cfg = get_twilio_config()
    return bool(cfg["account_sid"] and cfg["auth_token"])
