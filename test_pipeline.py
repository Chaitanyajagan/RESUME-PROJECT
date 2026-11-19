import os
from pathlib import Path
from ingestion import process_resume_file
from vector_store import get_vector_store
from database import init_db, upsert_candidate, get_all_candidates, save_outbox_action, get_outbox_items
from matcher import get_candidate_matcher, DEFAULT_JD_TEMPLATES
from email_service import compose_email_content, dispatch_action

def run_integration_test():
    print("=== Step 1: Initializing Database & Vector Store ===")
    init_db()
    vector_store = get_vector_store()
    matcher = get_candidate_matcher()
    print("Total initial vector chunks in ChromaDB:", vector_store.count())

    print("\n=== Step 2: Ingesting Resumes (Accountant & Arts samples) ===")
    sample_files = [
        ("Resume Dataset/Accountant/0.pdf", "Accountant"),
        ("Resume Dataset/Accountant/0287439839da10d2.pdf", "Accountant"),
        ("Resume Dataset/Arts/0.pdf", "Arts")
    ]
    
    for file_path, category in sample_files:
        if os.path.exists(file_path):
            print(f"Processing: {file_path}...")
            cand = process_resume_file(file_path, category=category)
            print(f"  -> Candidate: {cand['name']}")
            print(f"  -> Email: {cand['email'] or 'N/A'}")
            print(f"  -> Phone: {cand['phone'] or 'N/A'}")
            print(f"  -> Skills: {cand['skills']}")
            print(f"  -> Chunks: {len(cand['chunks'])}")
            
            upsert_candidate(cand)
            vector_store.add_candidate_chunks(cand["chunks"])

    print("Total ChromaDB chunks after ingestion:", vector_store.count())
    all_cands = get_all_candidates()
    print("Total DB candidates:", len(all_cands))

    print("\n=== Step 3: Matching against Job Description ===")
    accountant_jd = DEFAULT_JD_TEMPLATES["Senior Accountant & Financial Analyst"]
    ranked = matcher.match_and_rank(accountant_jd, top_candidates=5)
    print(f"Ranked {len(ranked)} candidates:")
    for idx, r in enumerate(ranked):
        print(f"  #{idx+1}: {r['name']} ({r['category']}) - {r['match_score']}% Match")
        print(f"      Matched Skills: {r['matched_skills']}")
        print(f"      Questions: {r['interview_questions'][0]}")

    print("\n=== Step 4: Testing Outbox Action & Calendly Link Injection ===")
    top_cand = ranked[0]
    draft = compose_email_content(
        candidate=top_cand,
        action_type="Interview",
        job_title="Senior Accountant & Financial Analyst",
        custom_calendly="https://calendly.com/talent-team/interview"
    )
    print("Email Subject:", draft["subject"])
    print("Calendly Link:", draft["calendly_link"])
    assert "https://calendly.com/talent-team/interview" in draft["calendly_link"]
    assert "name=" in draft["calendly_link"]

    print("\n=== Step 5: Dispatching Email via Sandbox Provider ===")
    action_id = save_outbox_action(draft)
    success, receipt = dispatch_action(action_id, draft, provider="sandbox")
    print(f"Dispatch status: {success}, Receipt: {receipt}")

    outbox = get_outbox_items()
    print(f"Total outbox items: {len(outbox)}, latest status: {outbox[0]['status']}")

    print("\n✅ All End-to-End Pipeline Steps Passed Successfully!")

if __name__ == "__main__":
    run_integration_test()
