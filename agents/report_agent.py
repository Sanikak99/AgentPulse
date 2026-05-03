import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from groq import Groq
from utils.db import get_db
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def get_all_assets():
    db = get_db()
    return list(db.assets.find({}, {"_id": 0}))

def get_all_alerts():
    db = get_db()
    return list(db.alerts.find({}, {"_id": 0}))

def get_event_log():
    db = get_db()
    return list(db.event_log.find(
        {},
        {"_id": 0}
    ).sort("timestamp", -1).limit(50))

def get_stats():
    db = get_db()
    total_assets   = db.assets.count_documents({})
    open_alerts    = db.alerts.count_documents({"status": "open"})
    resolved       = db.alerts.count_documents({"status": "resolved"})
    total_events   = db.event_log.count_documents({})
    critical_assets = db.assets.count_documents({
        "$expr": {"$lte": ["$current_stock", "$min_threshold"]}
    })
    return {
        "total_assets":    total_assets,
        "open_alerts":     open_alerts,
        "resolved_alerts": resolved,
        "total_events":    total_events,
        "critical_assets": critical_assets
    }

def save_report(report_text):
    db = get_db()
    db.reports.insert_one({
        "report":       report_text,
        "generated_at": datetime.now().isoformat(),
        "type":         "daily_summary"
    })
    log_event(
        agent="ReportAgent",
        action="report_generated",
        details=f"Daily report saved at {datetime.now().isoformat()}"
    )

def log_event(agent, action, details):
    db = get_db()
    db.event_log.insert_one({
        "agent":     agent,
        "action":    action,
        "details":   details,
        "timestamp": datetime.now().isoformat()
    })

def run(query=None):
    assets     = get_all_assets()
    alerts     = get_all_alerts()
    event_log  = get_event_log()
    stats      = get_stats()

    system_prompt = f"""You are the Report Agent for a hospital asset management system.
Your job is to generate a clear, professional daily asset management report
for hospital administrators.

Today's date: {datetime.now().strftime("%Y-%m-%d %H:%M")}

SYSTEM STATISTICS:
{stats}

ALL ASSETS WITH CURRENT STOCK:
{assets}

ALL ALERTS (open and resolved):
{alerts}

RECENT EVENTS LOG:
{event_log}

Generate a professional report with these sections:
1. Executive Summary (2-3 sentences overview)
2. Critical Assets Requiring Attention (list anything still below threshold)
3. Transfers Executed Today (what the Allocator Agent moved)
4. Resolved Alerts (what got fixed)
5. Departments Status (quick status per department)
6. Recommendations (what needs restocking from external supplier)

Keep it concise, professional, and actionable.
No medical advice — only asset management.
"""

    if query is None:
        query = "Generate the complete daily asset management report for today."

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": query}
        ],
        temperature=0.3,
        max_tokens=1000
    )

    report = response.choices[0].message.content
    save_report(report)
    return report


if __name__ == "__main__":
    print("Report Agent running...\n")
    print("=" * 60)
    report = run()
    print(report)
    print("=" * 60)
    print("\nReport saved to MongoDB 'reports' collection!")

    stats = get_stats()
    print(f"\nSystem Stats:")
    print(f"  Total assets tracked : {stats['total_assets']}")
    print(f"  Open alerts          : {stats['open_alerts']}")
    print(f"  Resolved alerts      : {stats['resolved_alerts']}")
    print(f"  Total events logged  : {stats['total_events']}")
    print(f"  Assets still critical: {stats['critical_assets']}")