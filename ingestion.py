import os
import re
import io
import uuid
from typing import Dict, List, Any, Tuple
from pathlib import Path

# PDF, OCR and Document parsers
import pymupdf  # PyMuPDF
import pytesseract
from PIL import Image
import docx

from config import TESSERACT_CMD

# Configure pytesseract path if binary exists
if TESSERACT_CMD and os.path.exists(TESSERACT_CMD):
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD

# Canonical casing map for standard industry technologies
CANONICAL_SKILL_CASING = {
    # AI & Machine Learning
    "python": "Python", "fastapi": "FastAPI", "langgraph": "LangGraph", "langchain": "LangChain",
    "rag": "RAG", "llm": "LLM", "pydantic": "Pydantic", "faiss": "FAISS", "embeddings": "Embeddings",
    "vector databases": "Vector Databases", "vector database": "Vector Databases", "reranking": "Reranking",
    "prompt design": "Prompt Design", "prompt engineering": "Prompt Engineering", "structured outputs": "Structured Outputs",
    "llm evaluation": "LLM Evaluation", "state machines": "State Machines", "tool calling": "Tool Calling",
    "guardrails": "Guardrails", "agentic ai": "Agentic AI", "generative ai": "Generative AI",
    "machine learning": "Machine Learning", "deep learning": "Deep Learning", "nlp": "NLP",
    "computer vision": "Computer Vision", "scikit-learn": "Scikit-Learn", "pandas": "Pandas", "numpy": "NumPy",
    "pytorch": "PyTorch", "tensorflow": "TensorFlow", "keras": "Keras", "mlflow": "MLflow",
    "chromadb": "ChromaDB", "pinecone": "Pinecone", "qdrant": "Qdrant", "weaviate": "Weaviate",
    "transformers": "Transformers", "hugging face": "Hugging Face", "huggingface": "Hugging Face",
    "sentence-transformers": "Sentence-Transformers", "feature engineering": "Feature Engineering",
    "classification": "Classification", "regression": "Regression", "clustering": "Clustering", "forecasting": "Forecasting",
    # Engineering & Backend
    "sql": "SQL", "postgresql": "PostgreSQL", "mysql": "MySQL", "mongodb": "MongoDB", "redis": "Redis",
    "sqlite": "SQLite", "docker": "Docker", "kubernetes": "Kubernetes", "git": "Git", "github": "GitHub",
    "gitlab": "GitLab", "ci/cd": "CI/CD", "linux": "Linux", "rest apis": "REST APIs", "rest api": "REST APIs",
    "graphql": "GraphQL", "grpc": "gRPC", "pytest": "pytest", "unit testing": "Unit Testing",
    "object-oriented programming": "Object-Oriented Programming", "oop": "OOP",
    "asynchronous programming": "Asynchronous Programming", "data structures": "Data Structures",
    "exception handling": "Exception Handling", "document parsing": "Document Parsing", "data validation": "Data Validation",
    "experiment tracking": "Experiment Tracking", "trace analysis": "Trace Analysis", "api payloads": "API Payloads",
    "csv": "CSV", "json": "JSON", "xml": "XML", "excel": "Excel", "microservices": "Microservices",
    "system design": "System Design", "kafka": "Kafka", "rabbitmq": "RabbitMQ",
    # Cloud & DevOps
    "aws": "AWS", "gcp": "GCP", "azure": "Azure", "terraform": "Terraform", "ansible": "Ansible",
    "jenkins": "Jenkins", "nginx": "Nginx", "prometheus": "Prometheus", "grafana": "Grafana",
    # Languages & Web
    "java": "Java", "c++": "C++", "c#": "C#", "golang": "Golang", "rust": "Rust", "javascript": "JavaScript",
    "typescript": "TypeScript", "react": "React", "next.js": "Next.js", "node.js": "Node.js", "django": "Django",
    "flask": "Flask", "spring boot": "Spring Boot", "html": "HTML", "css": "CSS", "tailwind": "Tailwind",
    # Data & Analytics
    "etl": "ETL", "spark": "Spark", "hadoop": "Hadoop", "airflow": "Airflow", "snowflake": "Snowflake",
    "bigquery": "BigQuery", "tableau": "Tableau", "power bi": "Power BI",
    # Finance & Management
    "accounting": "Accounting", "gaap": "GAAP", "ifrs": "IFRS", "financial analysis": "Financial Analysis",
    "general ledger": "General Ledger", "balance sheet": "Balance Sheet", "tax accounting": "Tax Accounting",
    "auditing": "Auditing", "quickbooks": "QuickBooks", "sap": "SAP", "agile": "Agile", "scrum": "Scrum",
    "jira": "Jira", "confluence": "Confluence", "leadership": "Leadership", "communication": "Communication"
}

SKILL_STOP_WORDS = {
    "data", "human", "review", "technical", "validation", "documentation", "concepts",
    "tools", "basics", "skills", "level", "roles", "responsibilities", "knowledge", "years", "experience"
}

def extract_skills(text: str) -> List[str]:
    """
    Extract comprehensive skills from resume text:
    1. Scan full text for 150+ canonical industry skills & technologies.
    2. Deep parse the explicit 'Skills' / 'Technical Skills' / 'Core Competencies' section.
    3. Deep parse project 'Technology Stack' lines.
    4. Normalize capitalization and deduplicate.
    """
    found_skills = set()
    lowered_text = text.lower()

    # 1. Match full canonical taxonomy with word boundary detection
    for raw_skill, canonical_name in CANONICAL_SKILL_CASING.items():
        pattern = r'\b' + re.escape(raw_skill) + r'\b'
        if re.search(pattern, lowered_text):
            found_skills.add(canonical_name)

    # 2. Extract from explicit Skills / Technical Skills sections
    sec_pattern = r'(?:^|\n)\s*(?:Skills|Technical Skills|Core Competencies|Technologies|Tools & Technologies)\s*\n+(.*?)(?=\n+\s*(?:Projects?|Project Title|Experience|Professional Experience|Education|Certifications?|Work History|Employment)\b|\Z)'
    sec_match = re.search(sec_pattern, text, re.DOTALL | re.IGNORECASE)
    if sec_match:
        for line in sec_match.group(1).split('\n'):
            line = line.strip()
            if not line:
                continue
            # Strip section category prefix (e.g., 'Programming:', 'Engineering:')
            if ':' in line:
                line = line.split(':', 1)[1]
            parts = re.split(r'[,;•|]+', line)
            for part in parts:
                item = re.sub(r'\b(concepts|tools|basics|technologies|proficient in|hands-on|experience in)\b', '', part, flags=re.IGNORECASE).strip()
                if len(item) >= 2 and len(item) <= 40:
                    low_item = item.lower()
                    if low_item not in SKILL_STOP_WORDS:
                        canonical = CANONICAL_SKILL_CASING.get(low_item, item.title())
                        found_skills.add(canonical)

    # 3. Extract from project Technology Stack lines
    tech_matches = re.findall(r'(?:Technology Stack|Tech Stack|Tools Used):\s*([^\n]+)', text, re.IGNORECASE)
    for tm in tech_matches:
        for part in re.split(r'[,;•|]+', tm):
            item = re.sub(r'\b(concepts|tools|technologies)\b', '', part, flags=re.IGNORECASE).strip()
            if len(item) >= 2 and len(item) <= 40:
                low_item = item.lower()
                if low_item not in SKILL_STOP_WORDS:
                    canonical = CANONICAL_SKILL_CASING.get(low_item, item.title())
                    found_skills.add(canonical)

    return sorted(list(found_skills))

def clean_text(text: str) -> str:
    """Normalize whitespace, remove excess newlines, and clean OCR noise."""
    if not text:
        return ""
    # Replace non-breaking spaces and irregular whitespace
    text = re.sub(r'[\r\t\f\v]', ' ', text)
    # Fix broken hyphenated words from OCR (e.g. "deadClaire-\nnes" or "deve-\nlopment")
    text = re.sub(r'(\w+)-\s*\n\s*(\w+)', r'\1\2', text)
    # Collapse multiple empty lines
    text = re.sub(r'\n{3,}', '\n\n', text)
    # Collapse multiple spaces
    text = re.sub(r' +', ' ', text)
    return text.strip()

def extract_text_from_pdf(file_path: str) -> str:
    """
    Extract text using PyMuPDF.
    If digital text is missing or sparse (scanned PDF), fallback to Tesseract OCR.
    """
    extracted_text = ""
    try:
        doc = pymupdf.open(file_path)
        for page_idx in range(len(doc)):
            page = doc[page_idx]
            page_text = page.get_text() or ""
            extracted_text += page_text + "\n"
        
        # If digital text extracted is meaningful (> 60 chars), return it
        if len(extracted_text.strip()) > 60:
            return clean_text(extracted_text)
        
        # Otherwise, run Tesseract OCR on page pixmaps
        ocr_text = ""
        for page_idx in range(len(doc)):
            page = doc[page_idx]
            pix = page.get_pixmap(dpi=150)
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            try:
                ocr_text += pytesseract.image_to_string(img) + "\n"
            except Exception as ocr_err:
                print(f"[OCR Warning] Page {page_idx} OCR error: {ocr_err}")
        
        return clean_text(ocr_text if ocr_text.strip() else extracted_text)
    except Exception as e:
        print(f"[PDF Extraction Error] {file_path}: {e}")
        return ""

def extract_text_from_docx(file_path: str) -> str:
    """Extract clean text from Word documents (.docx)."""
    try:
        doc = docx.Document(file_path)
        full_text = []
        for para in doc.paragraphs:
            if para.text.strip():
                full_text.append(para.text.strip())
        for table in doc.tables:
            for row in table.rows:
                row_text = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                if row_text:
                    full_text.append(" | ".join(row_text))
        return clean_text("\n".join(full_text))
    except Exception as e:
        print(f"[DOCX Extraction Error] {file_path}: {e}")
        return ""

def extract_contact_info(text: str, filename: str = "") -> Tuple[str, str, str]:
    """
    Extract:
    1. Candidate Name
    2. Email Address
    3. Phone Number
    """
    # 1. Email Extraction
    email_pattern = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
    email_matches = re.findall(email_pattern, text)
    email = email_matches[0] if email_matches else ""
    # Filter common template/bogus emails if multiple
    for m in email_matches:
        if "sample" not in m.lower() and "example" not in m.lower():
            email = m
            break

    # 2. Phone Extraction
    # Look for common phone patterns like (555) 432-1000, 555-432-1000, +1 555 432 1000, +91 9876543210
    phone_pattern = r'(?:(?:\+?\d{1,3}[- ]?)?\(?\d{3}\)?[- ]?\d{3}[- ]?\d{4})'
    phone = ""
    # Process line by line to avoid cross-line bleeding from zip codes
    for line in text.split("\n"):
        match = re.search(phone_pattern, line)
        if match:
            candidate_phone = match.group().strip()
            digits = re.sub(r'\D', '', candidate_phone)
            if 10 <= len(digits) <= 13:
                phone = candidate_phone
                break

    # 3. Candidate Name Extraction
    # Strategy: check top 10 lines of text for capitalized names (avoiding section titles)
    name = ""
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    skip_keywords = {"summary", "resume", "curriculum", "vitae", "contact", "experience", "education", "skills", "profile", "profile summary"}
    
    for line in lines[:8]:
        cleaned_line = re.sub(r'[^a-zA-Z\s]', '', line).strip()
        words = cleaned_line.split()
        if 2 <= len(words) <= 4:
            if not any(kw in cleaned_line.lower() for kw in skip_keywords):
                # Check title-case or ALL CAPS name
                if cleaned_line.isupper() or all(w[0].isupper() for w in words if w):
                    name = cleaned_line.title()
                    break

    # Fallback to filename if name not determined
    if not name and filename:
        clean_fn = Path(filename).stem
        clean_fn = re.sub(r'[\d_-]+', ' ', clean_fn).strip()
        if len(clean_fn.split()) >= 2:
            name = clean_fn.title()
        else:
            name = Path(filename).stem

    return name or "Candidate Profile", email, phone



def chunk_resume_text(text: str, candidate_metadata: Dict[str, Any], chunk_size: int = 500, overlap: int = 80) -> List[Dict[str, Any]]:
    """
    Section-aware and sliding-window chunking.
    Splits text into coherent passages and attaches candidate metadata.
    """
    sections = re.split(r'\n(?=[A-Z\s]{4,25}\b)', text)
    chunks = []
    chunk_index = 0

    for section in sections:
        section = section.strip()
        if not section:
            continue
        
        # Identify section header
        first_line = section.split('\n')[0].strip()
        section_name = first_line[:30] if len(first_line) <= 30 else "General"
        
        # If section is small enough, keep as single chunk
        if len(section) <= chunk_size + 100:
            chunks.append({
                "chunk_id": f"{candidate_metadata['candidate_id']}_c{chunk_index}",
                "text": section,
                "metadata": {
                    "candidate_id": candidate_metadata["candidate_id"],
                    "candidate_name": candidate_metadata.get("name", "Unknown"),
                    "email": candidate_metadata.get("email", ""),
                    "phone": candidate_metadata.get("phone", ""),
                    "filename": candidate_metadata.get("filename", ""),
                    "section": section_name,
                    "chunk_index": chunk_index
                }
            })
            chunk_index += 1
        else:
            # Sliding window over larger section
            start = 0
            while start < len(section):
                end = min(start + chunk_size, len(section))
                # Try breaking at newline or space
                if end < len(section):
                    break_point = section.rfind('\n', start, end)
                    if break_point == -1 or break_point < start + 200:
                        break_point = section.rfind(' ', start, end)
                    if break_point != -1 and break_point > start + 200:
                        end = break_point
                
                chunk_str = section[start:end].strip()
                if len(chunk_str) > 40:
                    chunks.append({
                        "chunk_id": f"{candidate_metadata['candidate_id']}_c{chunk_index}",
                        "text": chunk_str,
                        "metadata": {
                            "candidate_id": candidate_metadata["candidate_id"],
                            "candidate_name": candidate_metadata.get("name", "Unknown"),
                            "email": candidate_metadata.get("email", ""),
                            "phone": candidate_metadata.get("phone", ""),
                            "filename": candidate_metadata.get("filename", ""),
                            "section": section_name,
                            "chunk_index": chunk_index
                        }
                    })
                    chunk_index += 1
                start += max(chunk_size - overlap, 100)

    # If no chunks created, create one default chunk
    if not chunks and text.strip():
        chunks.append({
            "chunk_id": f"{candidate_metadata['candidate_id']}_c0",
            "text": text[:chunk_size * 2],
            "metadata": {
                "candidate_id": candidate_metadata["candidate_id"],
                "candidate_name": candidate_metadata.get("name", "Unknown"),
                "email": candidate_metadata.get("email", ""),
                "phone": candidate_metadata.get("phone", ""),
                "filename": candidate_metadata.get("filename", ""),
                "section": "General",
                "chunk_index": 0
            }
        })

    return chunks

def process_resume_file(file_path: str, category: str = "General") -> Dict[str, Any]:
    """
    End-to-end ingestion pipeline for a single file:
    1. Parse text (PDF/DOCX/TXT with OCR fallback)
    2. Normalize text
    3. Extract PII & metadata (Name, Phone, Email, Skills)
    4. Produce section-aware chunks
    """
    ext = Path(file_path).suffix.lower()
    if ext == ".pdf":
        raw_text = extract_text_from_pdf(file_path)
    elif ext in (".docx", ".doc"):
        raw_text = extract_text_from_docx(file_path)
    else:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            raw_text = clean_text(f.read())
            
    filename = Path(file_path).name
    candidate_id = f"cand_{uuid.uuid5(uuid.NAMESPACE_DNS, filename).hex[:10]}"
    name, email, phone = extract_contact_info(raw_text, filename)
    skills = extract_skills(raw_text)

    candidate_data = {
        "candidate_id": candidate_id,
        "name": name,
        "email": email,
        "phone": phone,
        "filename": filename,
        "file_path": str(file_path),
        "raw_text": raw_text,
        "skills": skills,
        "category": category,
        "status": "New"
    }

    chunks = chunk_resume_text(raw_text, candidate_data)
    candidate_data["chunks"] = chunks
    return candidate_data
