import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from config import DATABASE_PATH

def get_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Candidates table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS candidates (
        candidate_id TEXT PRIMARY KEY,
        name TEXT,
        email TEXT,
        phone TEXT,
        filename TEXT,
        file_path TEXT,
        raw_text TEXT,
        skills_json TEXT,
        category TEXT,
        status TEXT DEFAULT 'New',
        match_score REAL DEFAULT 0.0,
        evidence_json TEXT,
        ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Action Outbox (Interviews, Rejections, Status Updates)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS action_outbox (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        candidate_id TEXT,
        candidate_name TEXT,
        candidate_email TEXT,
        candidate_phone TEXT,
        action_type TEXT, -- 'Interview', 'Rejection', 'Under Review'
        subject TEXT,
        body TEXT,
        calendly_link TEXT,
        status TEXT DEFAULT 'Draft', -- 'Draft', 'Approved', 'Sent', 'Failed'
        provider TEXT DEFAULT 'sandbox',
        delivery_receipt TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        sent_at TIMESTAMP,
        FOREIGN KEY (candidate_id) REFERENCES candidates(candidate_id)
    )
    """)
    
    # Audit trail log
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS audit_trail (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_type TEXT,
        details TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    conn.commit()
    conn.close()

def log_audit(event_type: str, details: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO audit_trail (event_type, details, timestamp) VALUES (?, ?, ?)",
        (event_type, details, datetime.utcnow().isoformat())
    )
    conn.commit()
    conn.close()

def upsert_candidate(candidate: Dict[str, Any]):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO candidates (
        candidate_id, name, email, phone, filename, file_path, raw_text, skills_json, category, status, ingested_at, updated_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(candidate_id) DO UPDATE SET
        name = excluded.name,
        email = excluded.email,
        phone = excluded.phone,
        filename = excluded.filename,
        file_path = excluded.file_path,
        raw_text = excluded.raw_text,
        skills_json = excluded.skills_json,
        category = excluded.category,
        updated_at = excluded.updated_at
    """, (
        candidate["candidate_id"],
        candidate.get("name", "Unknown Candidate"),
        candidate.get("email", ""),
        candidate.get("phone", ""),
        candidate.get("filename", ""),
        candidate.get("file_path", ""),
        candidate.get("raw_text", ""),
        json.dumps(candidate.get("skills", [])),
        candidate.get("category", "General"),
        candidate.get("status", "New"),
        datetime.utcnow().isoformat(),
        datetime.utcnow().isoformat()
    ))
    conn.commit()
    conn.close()

def update_candidate_match(candidate_id: str, match_score: float, evidence: List[Dict[str, Any]]):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE candidates
    SET match_score = ?, evidence_json = ?, updated_at = ?
    WHERE candidate_id = ?
    """, (match_score, json.dumps(evidence), datetime.utcnow().isoformat(), candidate_id))
    conn.commit()
    conn.close()

def update_candidate_status(candidate_id: str, new_status: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE candidates
    SET status = ?, updated_at = ?
    WHERE candidate_id = ?
    """, (new_status, datetime.utcnow().isoformat(), candidate_id))
    conn.commit()
    conn.close()
    log_audit("CANDIDATE_STATUS_UPDATED", f"Candidate {candidate_id} status changed to {new_status}")

def get_all_candidates() -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM candidates ORDER BY match_score DESC, ingested_at DESC")
    rows = cursor.fetchall()
    candidates = []
    for r in rows:
        d = dict(r)
        d["skills"] = json.loads(d["skills_json"]) if d.get("skills_json") else []
        d["evidence"] = json.loads(d["evidence_json"]) if d.get("evidence_json") else []
        candidates.append(d)
    conn.close()
    return candidates

def get_candidate(candidate_id: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM candidates WHERE candidate_id = ?", (candidate_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        d = dict(row)
        d["skills"] = json.loads(d["skills_json"]) if d.get("skills_json") else []
        d["evidence"] = json.loads(d["evidence_json"]) if d.get("evidence_json") else []
        return d
    return None

def save_outbox_action(action: Dict[str, Any]) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO action_outbox (
        candidate_id, candidate_name, candidate_email, candidate_phone,
        action_type, subject, body, calendly_link, status, provider, created_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        action.get("candidate_id"),
        action.get("candidate_name"),
        action.get("candidate_email"),
        action.get("candidate_phone"),
        action.get("action_type", "Interview"),
        action.get("subject", ""),
        action.get("body", ""),
        action.get("calendly_link", ""),
        action.get("status", "Draft"),
        action.get("provider", "sandbox"),
        datetime.utcnow().isoformat()
    ))
    action_id = cursor.lastrowid
    conn.commit()
    conn.close()
    log_audit("OUTBOX_ACTION_CREATED", f"Draft {action.get('action_type')} created for {action.get('candidate_name')} (ID: {action_id})")
    return action_id

def update_outbox_status(action_id: int, status: str, delivery_receipt: str = ""):
    conn = get_connection()
    cursor = conn.cursor()
    sent_at = datetime.utcnow().isoformat() if status == "Sent" else None
    cursor.execute("""
    UPDATE action_outbox
    SET status = ?, delivery_receipt = ?, sent_at = ?
    WHERE id = ?
    """, (status, delivery_receipt, sent_at, action_id))
    conn.commit()
    conn.close()
    log_audit("OUTBOX_STATUS_UPDATED", f"Action #{action_id} status changed to {status}")

def get_outbox_items() -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM action_outbox ORDER BY id DESC")
    rows = cursor.fetchall()
    items = [dict(r) for r in rows]
    conn.close()
    return items

def get_audit_trail() -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM audit_trail ORDER BY id DESC LIMIT 100")
    rows = cursor.fetchall()
    trail = [dict(r) for r in rows]
    conn.close()
    return trail

def clear_all_data():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM candidates")
    cursor.execute("DELETE FROM action_outbox")
    cursor.execute("DELETE FROM audit_trail")
    conn.commit()
    conn.close()
    log_audit("SYSTEM_RESET", "All ATS data and records were reset.")

# Initialize tables upon module import
init_db()
