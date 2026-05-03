import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from groq import Groq
from utils.db import get_db
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def get_asset_summary():
    db = get_db()
    return list(db.assets.find({}, {"_id": 0}))

def get_open_alerts():
    db = get_db()
    return list(db.alerts.find({"status": "open"}, {"_id": 0}))

def get_surplus_assets():
    db = get_db()
    pipeline = [
        {
            "$match": {
                "$expr": {
                    "$gte": [
                        "$current_stock",
                        {"$multiply": ["$min_threshold", 1.5]}
                    ]
                }
            }
        },
        {"$project": {"_id": 0}}
    ]
    return list(db.assets.aggregate(pipeline))

def transfer_stock(asset_name, from_dept, to_dept, quantity):
    db = get_db()

    from_asset = db.assets.find_one(
        {"name": asset_name, "department": from_dept}
    )
    to_asset = db.assets.find_one(
        {"name": asset_name, "department": to_dept}
    )

    if not from_asset:
        return f"Asset {asset_name} not found in {from_dept}"
    if from_asset["current_stock"] < quantity:
        return f"Not enough stock in {from_dept} to transfer {quantity}"

    db.assets.update_one(
        {"name": asset_name, "department": from_dept},
        {"$inc": {"current_stock": -quantity},
         "$set": {"last_updated": datetime.now().isoformat()}}
    )

    if to_asset:
        db.assets.update_one(
            {"name": asset_name, "department": to_dept},
            {"$inc": {"current_stock": quantity},
             "$set": {"last_updated": datetime.now().isoformat()}}
        )
    else:
        db.assets.insert_one({
            "name":          asset_name,
            "department":    to_dept,
            "current_stock": quantity,
            "min_threshold": from_asset["min_threshold"],
            "max_capacity":  from_asset["max_capacity"],
            "unit":          from_asset["unit"],
            "category":      from_asset["category"],
            "last_updated":  datetime.now().isoformat()
        })

    db.alerts.update_one(
        {"asset_name": asset_name, "department": to_dept, "status": "open"},
        {"$set": {
            "status":      "resolved",
            "resolved_at": datetime.now().isoformat()
        }}
    )

    log_event(
        agent="AllocatorAgent",
        action="stock_transferred",
        details=(
            f"Transferred {quantity} {from_asset['unit']} of "
            f"{asset_name} from {from_dept} to {to_dept}"
        )
    )

    return (
        f"Transferred {quantity} {from_asset['unit']} of "
        f"{asset_name} from {from_dept} to {to_dept}"
    )

def log_event(agent, action, details):
    db = get_db()
    db.event_log.insert_one({
        "agent":     agent,
        "action":    action,
        "details":   details,
        "timestamp": datetime.now().isoformat()
    })

def find_best_match(asset_name_from_ai, from_dept):
    db = get_db()
    all_assets = list(db.assets.find(
        {"department": from_dept},
        {"_id": 0, "name": 1}
    ))
    asset_name_lower = asset_name_from_ai.lower().strip()
    for a in all_assets:
        if asset_name_lower in a["name"].lower() or \
           a["name"].lower() in asset_name_lower:
            return a["name"]
    return asset_name_from_ai

def run(query=None):
    all_assets  = get_asset_summary()
    open_alerts = get_open_alerts()
    surplus     = get_surplus_assets()

    system_prompt = system_prompt = f"""You are the Allocator Agent for a hospital asset management system.
Your job is to decide how to move assets from departments with surplus
to departments that are critically low.

All current assets:
{all_assets}

Open alerts (departments that need stock urgently):
{open_alerts}

Departments with surplus stock (can donate):
{surplus}

Your task:
1. Match each open alert with a surplus department that has the same asset
2. Decide how many units to transfer (bring the critical dept above its threshold)
3. Output your transfer plan clearly
4. Format EVERY transfer EXACTLY like this on its own line:
   TRANSFER: <quantity> <exact_asset_name> FROM <exact_department> TO <exact_department>

Use EXACT asset names and department names as they appear in the data above.
Example: TRANSFER: 13 IV Drip Set FROM Ward B TO Ward A

STRICT SAFETY RULES — you must follow these without exception:
- NEVER transfer blood bags of different types between each other.
  Blood Bag O+, Blood Bag A+, Blood Bag B+ are completely different assets.
  A+ cannot substitute O+. B+ cannot substitute A+. Never mix blood types.
- If asked to transfer between blood types, respond:
  "This transfer is not possible. Blood types cannot be substituted.
   Please contact the Blood Bank for external procurement."
- Only transfer IDENTICAL assets — same name, same type, same specification.
- Never give medical advice or clinical recommendations.
- Only move physical assets between departments.
"""

    if query is None:
        query = (
            "Analyze all open alerts and surplus stock. "
            "Create the best transfer plan to resolve as many alerts as possible."
        )

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": query}
        ],
        temperature=0.2,
        max_tokens=700
    )

    plan = response.choices[0].message.content
    log_event(
        agent="AllocatorAgent",
        action="allocation_plan_generated",
        details=plan[:200]
    )

    lines    = plan.split("\n")
    executed = []

    for line in lines:
        line = line.strip()
        if "TRANSFER:" not in line:
            continue
        try:
            transfer_part = line[line.index("TRANSFER:") + 9:].strip()
            from_idx      = transfer_part.upper().index(" FROM ")
            to_idx        = transfer_part.upper().index(" TO ")

            before_from   = transfer_part[:from_idx].strip().split()
            quantity      = int(before_from[0])
            asset_name    = " ".join(before_from[1:])
            from_dept     = transfer_part[from_idx + 6: to_idx].strip()
            to_dept       = transfer_part[to_idx + 4:].strip()

            matched_name  = find_best_match(asset_name, from_dept)
            result        = transfer_stock(matched_name, from_dept, to_dept, quantity)
            executed.append(result)
            print(f"  DONE: {result}")

        except Exception as e:
            executed.append(f"Could not parse: {line} — {e}")
            print(f"  FAILED: {line} — {e}")

    return plan, executed

if __name__ == "__main__":
    print("Allocator Agent running...\n")
    plan, transfers = run()

    print("ALLOCATION PLAN:")
    print(plan)
    print("\nEXECUTED TRANSFERS:")
    if transfers:
        for t in transfers:
            print(f"  {t}")
    else:
        print("  No transfers executed")