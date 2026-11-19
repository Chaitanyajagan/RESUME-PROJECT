import re
from typing import List, Dict, Any, Tuple
from vector_store import get_vector_store
from database import get_candidate, get_all_candidates, update_candidate_match
from ingestion import extract_skills

# Curated job description presets for recruiter quick-testing
DEFAULT_JD_TEMPLATES = {
    "Senior Full-Stack Engineer": """
Role: Senior Full Stack Engineer
Department: Engineering
Location: Remote / Hybrid

Key Responsibilities:
- Design and architect scalable cloud applications using Python, FastAPI or Django, and React or TypeScript.
- Build resilient microservices, REST APIs, and database schemas in PostgreSQL and Redis.
- Deploy and monitor production workloads using Docker, Kubernetes, and AWS CI/CD pipelines.
- Collaborate with cross-functional teams in an Agile/Scrum environment.

Requirements & Qualifications:
- 4+ years software engineering experience.
- Strong proficiency in Python, React, JavaScript, SQL, and Docker.
- Experience with Cloud platforms (AWS/GCP), Git, and CI/CD pipelines.
- Excellent communication and problem-solving skills.
""",
    "Senior Accountant & Financial Analyst": """
Role: Senior Accountant & Financial Analyst
Department: Finance & Accounting
Location: Hybrid

Key Responsibilities:
- Oversee month-end and year-end closing processes, reconciliations, and general ledger operations.
- Ensure strict compliance with US GAAP guidelines, financial reporting, and tax accounting.
- Conduct in-depth financial statement analysis, budgeting, and variance forecasting.
- Prepare audit schedules, tax preparation documentation, and support external auditors.

Requirements & Qualifications:
- Bachelor's or Master's in Accounting, Finance, or related field.
- 3+ years experience with GAAP, General Ledger, Auditing, and Financial Analysis.
- Advanced expertise in Excel, QuickBooks, or SAP.
- Strong attention to detail, time management, and ethical compliance.
""",
    "Data Scientist & AI / GenAI Engineer": """
Role: Data Scientist & AI / GenAI Engineer
Department: AI Research & Development
Location: Remote

Key Responsibilities:
- Build and evaluate machine learning models, retrieval-augmented generation (RAG), and LLM pipelines.
- Work with vector databases like ChromaDB, Pinecone, or Qdrant for semantic search.
- Develop data processing workflows using Python, PyTorch, Scikit-Learn, Pandas, and NumPy.
- Deploy scalable GenAI microservices with Docker and REST APIs.

Requirements & Qualifications:
- Degree in Computer Science, Data Science, or related quantitative field.
- Proven experience with Python, Machine Learning, Deep Learning, NLP, and RAG architectures.
- Hands-on skills in PyTorch, ChromaDB, Transformers, and Git.
""",
    "DevOps & Cloud Infrastructure Engineer": """
Role: DevOps & Cloud Infrastructure Engineer
Department: Infrastructure & Platform
Location: Remote

Key Responsibilities:
- Maintain highly available cloud infrastructure on AWS, Azure, or GCP using Terraform and Infrastructure as Code.
- Orchestrate containerized services with Docker and Kubernetes.
- Implement robust CI/CD deployment pipelines, automated testing, and secrets management.
- Monitor system reliability, logging, and performance metrics in Linux environments.

Requirements & Qualifications:
- 3+ years DevOps/SRE experience.
- Deep expertise in Docker, Kubernetes, Linux, AWS, Terraform, and CI/CD.
- Scripting proficiency in Python or Bash.
"""
}

class CandidateMatcher:
    def __init__(self):
        self.vector_store = get_vector_store()

    def analyze_job_description(self, jd_text: str) -> Dict[str, Any]:
        """Extract skills, key requirements, and metadata from JD."""
        skills = extract_skills(jd_text)
        
        # Estimate target role from text
        role_match = re.search(r'(?:role|title|position):\s*([^\n]+)', jd_text, re.IGNORECASE)
        role_title = role_match.group(1).strip() if role_match else "Target Role"
        
        return {
            "role_title": role_title,
            "required_skills": skills,
            "raw_text": jd_text
        }

    def match_and_rank(self, jd_text: str, top_candidates: int = 10) -> List[Dict[str, Any]]:
        """
        Match JD against ChromaDB candidate vector chunks,
        aggregate evidence by candidate, calculate scoring rubric,
        and return ranked candidates with phone, email, and grounded assessment.
        """
        jd_analysis = self.analyze_job_description(jd_text)
        required_skills = set(s.lower() for s in jd_analysis["required_skills"])
        
        # 1. Dense Vector Query into ChromaDB
        matched_chunks = self.vector_store.query(jd_text, n_results=40)
        
        # 2. Group evidence chunks by candidate_id
        candidate_evidence: Dict[str, List[Dict[str, Any]]] = {}
        candidate_similarities: Dict[str, List[float]] = {}
        
        for chunk in matched_chunks:
            meta = chunk["metadata"]
            cid = meta["candidate_id"]
            if cid not in candidate_evidence:
                candidate_evidence[cid] = []
                candidate_similarities[cid] = []
            candidate_evidence[cid].append(chunk)
            candidate_similarities[cid].append(chunk["similarity"])
            
        # Also ensure all candidates in DB are considered even if only partially retrieved
        all_db_candidates = {c["candidate_id"]: c for c in get_all_candidates()}
        
        ranked_results = []
        for cid, db_candidate in all_db_candidates.items():
            chunks = candidate_evidence.get(cid, [])
            sims = candidate_similarities.get(cid, [])
            
            # Semantic score: average of top 3 chunk similarities (default 0.2 if unretrieved)
            if sims:
                sims_sorted = sorted(sims, reverse=True)
                semantic_score = sum(sims_sorted[:3]) / min(len(sims_sorted), 3)
            else:
                semantic_score = 0.20
                
            # Skill overlap score
            cand_skills = set(s.lower() for s in db_candidate.get("skills", []))
            if required_skills:
                matched_skill_set = required_skills.intersection(cand_skills)
                missing_skill_set = required_skills - cand_skills
                skill_coverage = len(matched_skill_set) / len(required_skills)
            else:
                matched_skill_set = cand_skills
                missing_skill_set = set()
                skill_coverage = 0.50
                
            # Composite Scoring Rubric:
            # 55% Semantic Vector Match + 45% Direct Skill Match
            raw_match_score = (semantic_score * 0.55) + (skill_coverage * 0.45)
            final_percentage = round(min(max(raw_match_score * 100, 10.0), 98.5), 1)
            
            # Grounded evidence extraction (top 2 most relevant excerpts)
            evidence_excerpts = []
            for ch in sorted(chunks, key=lambda x: x["similarity"], reverse=True)[:3]:
                evidence_excerpts.append({
                    "section": ch["metadata"].get("section", "General"),
                    "text_snippet": ch["text"][:280] + ("..." if len(ch["text"]) > 280 else ""),
                    "similarity": round(ch["similarity"] * 100, 1)
                })
            
            # Generate personalized interview questions based on candidate background & gaps
            interview_questions = self.generate_interview_questions(
                candidate_name=db_candidate.get("name", "Candidate"),
                matched_skills=[s.title() for s in matched_skill_set],
                missing_skills=[s.title() for s in missing_skill_set],
                category=db_candidate.get("category", "General")
            )
            
            # Update SQLite database with latest match score and evidence
            update_candidate_match(cid, final_percentage, evidence_excerpts)
            
            ranked_results.append({
                "candidate_id": cid,
                "name": db_candidate.get("name", "Unknown Candidate"),
                "email": db_candidate.get("email", ""),
                "phone": db_candidate.get("phone", ""),
                "category": db_candidate.get("category", "General"),
                "status": db_candidate.get("status", "New"),
                "filename": db_candidate.get("filename", ""),
                "match_score": final_percentage,
                "semantic_score": round(semantic_score * 100, 1),
                "skill_coverage_score": round(skill_coverage * 100, 1),
                "matched_skills": sorted([s.title() for s in matched_skill_set]),
                "missing_skills": sorted([s.title() for s in missing_skill_set]),
                "evidence_snippets": evidence_excerpts,
                "interview_questions": interview_questions,
                "raw_text_preview": db_candidate.get("raw_text", "")[:400]
            })

        # Sort descending by match score
        ranked_results.sort(key=lambda x: x["match_score"], reverse=True)
        return ranked_results[:top_candidates]

    def generate_interview_questions(self, candidate_name: str, matched_skills: List[str], missing_skills: List[str], category: str) -> List[str]:
        """Generate grounded interview questions probing strengths and skill gaps."""
        questions = []
        
        # 1. Question probing strongest verified skill
        if matched_skills:
            top_skill = matched_skills[0]
            questions.append(f"Can you walk us through a recent project where you applied your expertise in {top_skill} to solve a complex bottleneck?")
        else:
            questions.append(f"Could you elaborate on the core achievements and responsibilities in your previous {category} roles?")
            
        # 2. Question probing secondary skill / methodology
        if len(matched_skills) > 1:
            second_skill = matched_skills[1]
            questions.append(f"How do you ensure reliability and quality standards when working with {second_skill} in a production workflow?")
        else:
            questions.append("Describe a time when you had to adapt quickly to unfamiliar tools or strict deadlines.")
            
        # 3. Question probing identified skill gap
        if missing_skills:
            gap_skill = missing_skills[0]
            questions.append(f"Our tech stack heavily involves {gap_skill}. How have you approached learning or bridging similar technologies in the past?")
        else:
            questions.append("What strategies do you use for effective cross-functional collaboration and stakeholder alignment?")
            
        return questions

# Helper singleton
_matcher_instance = None

def get_candidate_matcher() -> CandidateMatcher:
    global _matcher_instance
    if _matcher_instance is None:
        _matcher_instance = CandidateMatcher()
    return _matcher_instance
