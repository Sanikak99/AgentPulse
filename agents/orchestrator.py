import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from groq import Groq
from utils.db import get_db
from dotenv import load_dotenv
from datetime import datetime

import agents.inventory_agent    as inventory
import agents.alert_agent       as alert
import agents.allocator_agent   as allocator
import agents.report_agent      as report
import agents.information_agent as information

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def log_event(agent, action, details):
    db = get_db()
    db.event_log.insert_one({
        "agent":     agent,
        "action":    action,
        "details":   details,
        "timestamp": datetime.now().isoformat()
    })

def decide_agent(query):
    system_prompt = system_prompt = """You are the Orchestrator for a hospital asset management system.
    You have 5 specialist agents available:

    1. INVENTORY  — questions about stock levels, asset counts, department inventory
    2. ALERT      — checking alerts, critical shortages, threshold monitoring
    3. ALLOCATOR  — moving IDENTICAL assets between departments only
    4. REPORT     — generating reports, summaries, statistics, audit trails
    5. INFORMATION — questions about departments, staff, heads, contact info

    IMPORTANT SAFETY RULES:
    - NEVER route blood type substitution requests to ALLOCATOR.
    Example: "transfer A+ to O+" is medically invalid — respond directly with SAFE
    - NEVER route any request that involves mixing different blood types
    - NEVER route medical treatment decisions to any agent

    If a query involves blood type substitution or medical decisions, reply: SAFE

    Otherwise reply with ONLY one word: INVENTORY, ALERT, ALLOCATOR, REPORT, or INFORMATION"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": query}
        ],
        temperature=0,
        max_tokens=10
    )
    return response.choices[0].message.content.strip().upper()

def run(query):
    agent_name = decide_agent(query)
    log_event(
        agent="Orchestrator",
        action="routing",
        details=f"Query: '{query}' → routed to {agent_name}"
    )

    if agent_name == "SAFE":
        return (
            "[Safety System]\n\n"
            "This request involves a medical decision that this system "
            "cannot process. Critical medical assets cannot be substituted "
            "with different variants — each type is a completely different asset.\n\n"
            "Please contact the relevant medical staff or department directly "
            "for procurement of the required asset."
        )

    elif agent_name == "INVENTORY":
        return f"[Inventory Agent]\n\n{inventory.run(query)}"

    elif agent_name == "ALERT":
        return f"[Alert Agent]\n\n{alert.run(query)}"

    elif agent_name == "ALLOCATOR":
        plan, transfers = allocator.run(query)
        transfer_text = "\n".join(transfers) if transfers else "No transfers executed."
        return f"[Allocator Agent]\n\n{plan}\n\nExecuted:\n{transfer_text}"

    elif agent_name == "REPORT":
        return f"[Report Agent]\n\n{report.run(query)}"

    elif agent_name == "INFORMATION":
        return f"[Information Agent]\n\n{information.run(query)}"

    else:
        return "Could not route your query. Please try again."

if __name__ == "__main__":
    print("=" * 60)
    print("  Hospital Asset Management — Multi Agent System")
    print("=" * 60)
    print("Type your query and press Enter.")
    print("Type 'exit' to quit.\n")

    while True:
        try:
            query = input("You: ").strip()
            if not query:
                continue
            if query.lower() == "exit":
                print("System shutting down. Goodbye!")
                break
            run(query)
        except KeyboardInterrupt:
            print("\nSystem shutting down. Goodbye!")
            break