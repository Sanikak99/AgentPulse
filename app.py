import os
import sys
from flask import Flask, render_template, request, jsonify
from agents.orchestrator import run as orchestrator_run
from agents.inventory_agent import get_all_assets, get_low_stock_assets
from agents.alert_agent import get_open_alerts, run as alert_agent_run
from agents.report_agent import get_stats
from data.seed_data import seed
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

# Seed the database on startup
try:
    seed()
    # Auto-generate alerts for any low-stock assets
    alert_agent_run()
except Exception as e:
    print(f"Database seeding error: {e}")

@app.route("/")
def landing():
    return render_template("landing.html")

@app.route("/dashboard")
def dashboard():
    return render_template("index.html")

@app.route("/api/stats")
def stats():
    return jsonify(get_stats())

@app.route("/api/assets")
def assets():
    all_assets = get_all_assets()
    for a in all_assets:
        a.pop("_id", None)
    return jsonify(all_assets)

@app.route("/api/alerts")
def alerts():
    open_alerts = get_open_alerts()
    for a in open_alerts:
        a.pop("_id", None)
    return jsonify(open_alerts)

@app.route("/api/chat", methods=["POST"])
def chat():
    data  = request.json
    query = data.get("query", "").strip()
    if not query:
        return jsonify({"error": "Empty query"}), 400
    try:
        result = orchestrator_run(query)
        return jsonify({"response": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)