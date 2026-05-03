import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from groq import Groq
from utils.db import get_db
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def get_low_stock_assets():
    db = get_db()
    pipeline = [
        {
            "$match": {
                "$expr": {"$lte": ["$current_stock", "$min_threshold"]}
            }
        },
        {"$project": {"_id": 0}}
    ]
    return list(db.assets.aggregate(pipeline))

def alert_already_exists(asset_name, department):
    db = get_db()
    existing = db.alerts.find_one({
        "asset_name":  asset_name,
        "department":  department,
        "status":      "open"
    })
    return existing is not None

def create_alert(asset_name, department, current_stock,
                 min_threshold, severity, message):
    db = get_db()
    alert = {
        "asset_name":    asset_name,
        "department":    department,
        "current_stock": current_stock,
        "min_threshold": min_threshold,
        "severity":      severity,
        "message":       message,
        "status":        "open",
        "created_at":    datetime.now().isoformat(),
        "resolved_at":   None
    }
    db.alerts.insert_one(alert)
    log_event(
        agent="AlertAgent",
        action="alert_created",
        details=f"[{severity}] {asset_name} in {department} — stock: {current_stock}"
    )
    return alert

def get_open_alerts():
    db = get_db()
    return list(db.alerts.find({"status": "open"}, {"_id": 0}))

def resolve_alert(asset_name, department):
    db = get_db()
    db.alerts.update_one(
        {"asset_name": asset_name, "department": department, "status": "open"},
        {"$set": {
            "status":      "resolved",
            "resolved_at": datetime.now().isoformat()
        }}
    )
    log_event(
        agent="AlertAgent",
        action="alert_resolved",
        details=f"{asset_name} in {department} alert resolved"
    )

def log_event(agent, action, details):
    db = get_db()
    db.event_log.insert_one({
        "agent":     agent,
        "action":    action,
        "details":   details,
        "timestamp": datetime.now().isoformat()
    })

def calculate_severity(current_stock, min_threshold):
    if min_threshold == 0:
        return "LOW"
    ratio = current_stock / min_threshold
    if ratio <= 0.5:
        return "CRITICAL"
    elif ratio <= 0.8:
        return "HIGH"
    else:
        return "MEDIUM"

def run(query=None):
    low_stock_assets = get_low_stock_assets()
    newly_created    = []

    for asset in low_stock_assets:
        name       = asset["name"]
        dept       = asset["department"]
        stock      = asset["current_stock"]
        threshold  = asset["min_threshold"]
        severity   = calculate_severity(stock, threshold)

        if not alert_already_exists(name, dept):
            message = (
                f"{name} in {dept} is at {stock} {asset['unit']} "
                f"— below minimum threshold of {threshold}. "
                f"Immediate restocking required."
            )
            alert = create_alert(name, dept, stock, threshold, severity, message)
            newly_created.append(alert)

    open_alerts = get_open_alerts()

    system_prompt = f"""You are the Alert Agent for a hospital asset management system.
Your job is to analyze asset alerts and give a clear summary to hospital staff.

Newly created alerts this run:
{newly_created}

All currently open alerts:
{open_alerts}

Rules:
- Group alerts by severity: CRITICAL first, then HIGH, then MEDIUM
- Be direct and urgent for CRITICAL items
- Suggest which department should be checked first
- Never give medical advice — only asset management advice
"""

    if query is None:
        query = "Give me a full alert summary of the current hospital asset situation."

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": query}
        ],
        temperature=0.3,
        max_tokens=600
    )

    answer = response.choices[0].message.content
    log_event(
        agent="AlertAgent",
        action="summary_generated",
        details=answer[:150]
    )
    return answer


if __name__ == "__main__":
    print("Alert Agent running...\n")
    print(run())
    print("\n" + "=" * 60)
    print("Open alerts in MongoDB:")
    for a in get_open_alerts():
        print(f"  [{a['severity']}] {a['asset_name']} — {a['department']} "
              f"(stock: {a['current_stock']})")