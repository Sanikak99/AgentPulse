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
    assets = list(db.assets.find({}, {"_id": 0}))
    return assets

def get_assets_by_department(department):
    db = get_db()
    assets = list(db.assets.find(
        {"department": department},
        {"_id": 0}
    ))
    return assets

def get_low_stock_assets():
    db = get_db()
    pipeline = [
        {
            "$match": {
                "$expr": {
                    "$lte": ["$current_stock", "$min_threshold"]
                }
            }
        },
        {"$project": {"_id": 0}}
    ]
    return list(db.assets.aggregate(pipeline))

def update_stock(asset_name, department, new_stock):
    db = get_db()
    db.assets.update_one(
        {"name": asset_name, "department": department},
        {"$set": {
            "current_stock": new_stock,
            "last_updated": datetime.now().isoformat()
        }}
    )
    log_event(
        agent="InventoryAgent",
        action="stock_updated",
        details=f"{asset_name} in {department} updated to {new_stock}"
    )

def log_event(agent, action, details):
    db = get_db()
    db.event_log.insert_one({
        "agent":     agent,
        "action":    action,
        "details":   details,
        "timestamp": datetime.now().isoformat()
    })

def run(query):
    all_assets   = get_all_assets()
    low_stock    = get_low_stock_assets()

    system_prompt = f"""You are the Inventory Agent for a hospital asset management system.
Your job is to answer questions about hospital stock levels and assets.

Current hospital inventory:
{all_assets}

Assets currently below minimum threshold (CRITICAL):
{low_stock}

Rules:
- Answer only about hospital assets and stock — nothing medical
- Be specific with numbers from the data above
- If an asset is below threshold, always mention it is critical
- Keep answers clear and concise
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": query}
        ],
        temperature=0.3,
        max_tokens=500
    )

    answer = response.choices[0].message.content

    log_event(
        agent="InventoryAgent",
        action="query_answered",
        details=f"Q: {query} | A: {answer[:100]}..."
    )

    return answer


if __name__ == "__main__":
    print("Inventory Agent is running...\n")

    test_queries = [
        "How many ventilators do we have in ICU?",
        "Which assets are critically low right now?",
        "Show me all assets in the Emergency department",
    ]

    for q in test_queries:
        print(f"Q: {q}")
        print(f"A: {run(q)}")
        print("-" * 60)