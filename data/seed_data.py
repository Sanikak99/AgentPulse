import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.db import get_db

def seed():
    db = get_db()

    # Clear old data
    db.departments.drop()
    db.assets.drop()
    db.alerts.drop()
    db.event_log.drop()
    db.reports.drop()

    # ── DEPARTMENTS ──────────────────────────────────────────
    departments = [
        { "name": "ICU",          "floor": 2, "capacity": 20, "head": "Dr. Sharma" },
        { "name": "OT",           "floor": 3, "capacity": 10, "head": "Dr. Mehta"  },
        { "name": "Ward A",       "floor": 1, "capacity": 40, "head": "Dr. Patil"  },
        { "name": "Ward B",       "floor": 1, "capacity": 40, "head": "Dr. Rao"    },
        { "name": "Emergency",    "floor": 0, "capacity": 15, "head": "Dr. Kulkarni"   },
        { "name": "Blood Bank",   "floor": 2, "capacity": 5,  "head": "Dr. Verma"  },
        { "name": "Pharmacy",     "floor": 0, "capacity": 5,  "head": "Dr. Joshi"  },
    ]
    db.departments.insert_many(departments)
    print(f"Inserted {len(departments)} departments")

    # ── ASSETS ───────────────────────────────────────────────
    assets = [
        # Oxygen Cylinders
        { "name": "Oxygen Cylinder", "category": "respiratory",
          "department": "ICU",       "current_stock": 42,
          "min_threshold": 20,       "max_capacity": 80,  "unit": "units" },
        { "name": "Oxygen Cylinder", "category": "respiratory",
          "department": "Emergency", "current_stock": 15,
          "min_threshold": 20,       "max_capacity": 50,  "unit": "units" },
        { "name": "Oxygen Cylinder", "category": "respiratory",
          "department": "Ward A",    "current_stock": 30,
          "min_threshold": 15,       "max_capacity": 50,  "unit": "units" },

        # Ventilators
        { "name": "Ventilator",      "category": "respiratory",
          "department": "ICU",       "current_stock": 8,
          "min_threshold": 10,       "max_capacity": 25,  "unit": "units" },
        { "name": "Ventilator",      "category": "respiratory",
          "department": "Emergency", "current_stock": 4,
          "min_threshold": 3,        "max_capacity": 10,  "unit": "units" },
        { "name": "Ventilator",      "category": "respiratory",
          "department": "OT",        "current_stock": 11,
          "min_threshold": 5,        "max_capacity": 15,  "unit": "units" },

        # Blood Bags
        { "name": "Blood Bag O+",   "category": "blood",
          "department": "Blood Bank","current_stock": 18,
          "min_threshold": 30,       "max_capacity": 100, "unit": "units" },
        { "name": "Blood Bag A+",   "category": "blood",
          "department": "Blood Bank","current_stock": 25,
          "min_threshold": 20,       "max_capacity": 80,  "unit": "units" },
        { "name": "Blood Bag B+",   "category": "blood",
          "department": "Blood Bank","current_stock": 12,
          "min_threshold": 15,       "max_capacity": 60,  "unit": "units" },

        # Syringes
        { "name": "Syringe 10ml",   "category": "consumable",
          "department": "OT",        "current_stock": 310,
          "min_threshold": 100,      "max_capacity": 500, "unit": "packs" },
        { "name": "Syringe 5ml",    "category": "consumable",
          "department": "Ward A",    "current_stock": 220,
          "min_threshold": 80,       "max_capacity": 400, "unit": "packs" },
        { "name": "Syringe 5ml",    "category": "consumable",
          "department": "Ward B",    "current_stock": 190,
          "min_threshold": 80,       "max_capacity": 400, "unit": "packs" },

        # IV Drip Sets
        { "name": "IV Drip Set",    "category": "consumable",
          "department": "Ward A",    "current_stock": 12,
          "min_threshold": 25,       "max_capacity": 80,  "unit": "sets"  },
        { "name": "IV Drip Set",    "category": "consumable",
          "department": "Ward B",    "current_stock": 35,
          "min_threshold": 25,       "max_capacity": 80,  "unit": "sets"  },
        { "name": "IV Drip Set",    "category": "consumable",
          "department": "ICU",       "current_stock": 28,
          "min_threshold": 20,       "max_capacity": 60,  "unit": "sets"  },

        # Surgical Gloves
        { "name": "Surgical Gloves","category": "consumable",
          "department": "OT",        "current_stock": 95,
          "min_threshold": 50,       "max_capacity": 200, "unit": "boxes" },
        { "name": "Surgical Gloves","category": "consumable",
          "department": "Emergency", "current_stock": 40,
          "min_threshold": 30,       "max_capacity": 100, "unit": "boxes" },

        # Hospital Beds
        { "name": "Hospital Bed",   "category": "infrastructure",
          "department": "Ward A",    "current_stock": 35,
          "min_threshold": 10,       "max_capacity": 40,  "unit": "units" },
        { "name": "Hospital Bed",   "category": "infrastructure",
          "department": "Ward B",    "current_stock": 28,
          "min_threshold": 10,       "max_capacity": 40,  "unit": "units" },
        { "name": "Hospital Bed",   "category": "infrastructure",
          "department": "ICU",       "current_stock": 16,
          "min_threshold": 5,        "max_capacity": 20,  "unit": "units" },

        # Defibrillators
        { "name": "Defibrillator",  "category": "equipment",
          "department": "Emergency", "current_stock": 3,
          "min_threshold": 2,        "max_capacity": 6,   "unit": "units" },
        { "name": "Defibrillator",  "category": "equipment",
          "department": "ICU",       "current_stock": 2,
          "min_threshold": 2,        "max_capacity": 4,   "unit": "units" },

        # Wheelchairs
        { "name": "Wheelchair",     "category": "mobility",
          "department": "Ward A",    "current_stock": 8,
          "min_threshold": 5,        "max_capacity": 15,  "unit": "units" },
        { "name": "Wheelchair",     "category": "mobility",
          "department": "Ward B",    "current_stock": 6,
          "min_threshold": 5,        "max_capacity": 15,  "unit": "units" },
    ]
    db.assets.insert_many(assets)
    print(f"Inserted {len(assets)} assets")
    print("Database seeded successfully!")

if __name__ == "__main__":
    seed()