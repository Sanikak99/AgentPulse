import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from groq import Groq
from utils.db import get_db
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def get_all_departments():
    db = get_db()
    return list(db.departments.find({}, {"_id": 0}))

def get_department_by_name(dept_name):
    db = get_db()
    return db.departments.find_one({"name": {"$regex": dept_name, "$options": "i"}}, {"_id": 0})

def get_all_department_names():
    db = get_db()
    depts = db.departments.find({}, {"name": 1, "_id": 0})
    return [d["name"] for d in depts]

def log_event(agent, action, details):
    db = get_db()
    db.event_log.insert_one({
        "agent":     agent,
        "action":    action,
        "details":   details,
        "timestamp": datetime.now().isoformat()
    })

def run(query):
    """
    Process queries about hospital departments and personnel.
    Handles questions like:
    - "Who is the head of ICU?"
    - "What floor is blood bank on?"
    - "List all departments"
    - "Contact information for departments"
    """
    
    system_prompt = """You are an Information Assistant for the hospital management system.
    You have access to department information including:
    - Department names
    - Department heads
    - Floor numbers
    - Capacity information
    
    You are given the following departments data:
    {departments_data}
    
    Answer questions about departments, staff, and contact information.
    Be helpful and specific. If asked about a specific department, provide relevant details.
    If information is not available, say so clearly."""
    
    departments = get_all_departments()
    
    # Format departments for the prompt
    dept_text = "\n".join([
        f"- {d['name']}: Head = {d['head']}, Floor = {d['floor']}, Capacity = {d['capacity']}"
        for d in departments
    ])
    
    system_prompt = system_prompt.format(departments_data=dept_text)
    
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query}
        ],
        temperature=0.5,
        max_tokens=500
    )
    
    result = response.choices[0].message.content.strip()
    
    log_event(
        agent="InformationAgent",
        action="query_processed",
        details=f"Query: '{query}' → Response sent"
    )
    
    return result
