"""Compliance & HACCP monitoring API endpoints."""

import hashlib
import random
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter

from nexusfab.api.schemas.compliance import AllergenMatrix, CCPStatus, CIPSchedule, ComplianceScore
from nexusfab.seed.plants import PLANTS
from nexusfab.seed.products import PRODUCTS

router = APIRouter(prefix="/api/compliance", tags=["Compliance"])

ALLERGENS = ["GLUTEN", "DAIRY", "NUTS", "SOY", "EGGS", "SESAME"]

# CCP definitions per plant category
_CCP: dict[str, list[dict]] = {
    "WATER": [
        {"id": "UV",  "name": "UV Treatment",       "parameter": "UV Intensity",   "unit": "mJ/cm²", "lo": 40.0,  "hi": 80.0,  "clo": 38.0,  "chi": 90.0,  "nom": 55.0,  "var": 3.0},
        {"id": "TBY", "name": "Turbidity Check",    "parameter": "Turbidity",      "unit": "NTU",    "lo": 0.0,   "hi": 1.0,   "clo": 0.0,   "chi": 2.0,   "nom": 0.3,   "var": 0.05},
        {"id": "CL2", "name": "Residual Chlorine",  "parameter": "Cl₂ Residual",   "unit": "mg/L",   "lo": 0.2,   "hi": 0.5,   "clo": 0.1,   "chi": 0.8,   "nom": 0.35,  "var": 0.03},
    ],
    "CONFECTIONERY": [
        {"id": "TMP", "name": "Enrober Temp",       "parameter": "Chocolate Temp", "unit": "°C",     "lo": 29.0,  "hi": 32.0,  "clo": 27.0,  "chi": 35.0,  "nom": 30.5,  "var": 0.5},
        {"id": "MTD", "name": "Metal Detection",    "parameter": "Detection Rate",  "unit": "%",      "lo": 99.9,  "hi": 100.0, "clo": 99.5,  "chi": 100.0, "nom": 100.0, "var": 0.05},
        {"id": "AW",  "name": "Water Activity",     "parameter": "a_w",            "unit": "a_w",    "lo": 0.50,  "hi": 0.65,  "clo": 0.45,  "chi": 0.70,  "nom": 0.57,  "var": 0.02},
    ],
    "DAIRY": [
        {"id": "PST", "name": "Pasteurisation Temp","parameter": "Temperature",    "unit": "°C",     "lo": 72.0,  "hi": 85.0,  "clo": 71.0,  "chi": 90.0,  "nom": 76.0,  "var": 1.0},
        {"id": "CLG", "name": "Cold Storage",       "parameter": "Storage Temp",   "unit": "°C",     "lo": 1.0,   "hi": 4.0,   "clo": 0.0,   "chi": 6.0,   "nom": 3.0,   "var": 0.3},
        {"id": "PH",  "name": "pH Control",         "parameter": "pH",             "unit": "pH",     "lo": 6.6,   "hi": 6.8,   "clo": 6.4,   "chi": 7.0,   "nom": 6.7,   "var": 0.05},
    ],
    "PET_FOOD": [
        {"id": "MST", "name": "Moisture Content",   "parameter": "Moisture",       "unit": "%",      "lo": 6.0,   "hi": 12.0,  "clo": 4.0,   "chi": 14.0,  "nom": 9.0,   "var": 0.5},
        {"id": "MTD", "name": "Metal Detection",    "parameter": "Detection Rate",  "unit": "%",      "lo": 99.9,  "hi": 100.0, "clo": 99.5,  "chi": 100.0, "nom": 100.0, "var": 0.05},
        {"id": "STR", "name": "Retort Temp",        "parameter": "Retort Temp",    "unit": "°C",     "lo": 121.0, "hi": 135.0, "clo": 120.0, "chi": 140.0, "nom": 127.0, "var": 1.5},
    ],
    "PREPARED_FOODS": [
        {"id": "PH",  "name": "pH Control",         "parameter": "pH",             "unit": "pH",     "lo": 4.0,   "hi": 4.6,   "clo": 3.8,   "chi": 5.0,   "nom": 4.3,   "var": 0.08},
        {"id": "AW",  "name": "Water Activity",     "parameter": "a_w",            "unit": "a_w",    "lo": 0.85,  "hi": 0.92,  "clo": 0.80,  "chi": 0.95,  "nom": 0.88,  "var": 0.01},
        {"id": "MTD", "name": "Metal Detection",    "parameter": "Detection Rate",  "unit": "%",      "lo": 99.9,  "hi": 100.0, "clo": 99.5,  "chi": 100.0, "nom": 100.0, "var": 0.05},
    ],
}


def _rng(plant_id: str, salt: str) -> random.Random:
    seed = int(hashlib.md5(f"{plant_id}{salt}".encode()).hexdigest()[:8], 16)
    return random.Random(seed)


def _plant(plant_id: str):
    return next((p for p in PLANTS if p.id == plant_id), None)


@router.get("/{plant_id}/ccps", response_model=CCPStatus, summary="Critical Control Point (CCP) status and compliance rates")
async def get_ccps(plant_id: str):
    p = _plant(plant_id)
    templates = _CCP.get(p.category if p else "WATER", _CCP["WATER"])
    rng = _rng(plant_id, "ccp")
    now = datetime.now(timezone.utc)

    ccps = []
    for t in templates:
        val = t["nom"] + rng.gauss(0, t["var"])
        if val < t["clo"] or val > t["chi"]:
            status = "FAIL"
        elif val < t["lo"] or val > t["hi"]:
            status = "WARN"
        else:
            status = "PASS"
        ccps.append({
            "id": f"CCP-{plant_id}-{t['id']}",
            "name": t["name"],
            "parameter": t["parameter"],
            "unit": t["unit"],
            "current_value": round(val, 3),
            "lower_limit": t["lo"],
            "upper_limit": t["hi"],
            "critical_lower": t["clo"],
            "critical_upper": t["chi"],
            "status": status,
            "compliance_rate_30d": round(rng.uniform(94.0, 99.8), 1),
            "last_checked": (now - timedelta(minutes=rng.randint(0, 29))).isoformat(),
        })
    return {"plant_id": plant_id, "ccps": ccps}


@router.get("/{plant_id}/allergens", response_model=AllergenMatrix, summary="Allergen matrix — CONTAINS / MAY_CONTAIN / FREE per product and allergen")
async def get_allergens(plant_id: str):
    plant_products = [p for p in PRODUCTS if p.plant_id == plant_id]
    plant_allergen_set: set[str] = set()
    for prod in plant_products:
        plant_allergen_set.update(prod.allergens)

    current_sku = plant_products[0].sku if plant_products else None
    rows = []
    for i, prod in enumerate(plant_products):
        status: dict[str, str] = {}
        for allergen in ALLERGENS:
            if allergen in prod.allergens:
                status[allergen] = "CONTAINS"
            elif allergen in plant_allergen_set:
                status[allergen] = "MAY_CONTAIN"
            else:
                status[allergen] = "FREE"

        if i + 1 < len(plant_products):
            nxt = plant_products[i + 1]
            curr_tier, nxt_tier = prod.allergen_tier, nxt.allergen_tier
            if curr_tier > nxt_tier or (curr_tier > 0 and nxt_tier == 0):
                cip_class: str | None = "CLASS_A"
            elif curr_tier == nxt_tier and curr_tier > 0:
                cip_class = "CLASS_B"
            else:
                cip_class = "CLASS_C"
        else:
            cip_class = None

        rows.append({
            "sku": prod.sku,
            "name": prod.name,
            "allergen_status": status,
            "is_current_production": prod.sku == current_sku,
            "next_changeover_cip_class": cip_class,
        })

    return {"plant_id": plant_id, "allergens": ALLERGENS, "products": rows}


@router.get("/{plant_id}/cip-schedule", response_model=CIPSchedule, summary="CIP (Clean-in-Place) schedule with upcoming and completed events")
async def get_cip_schedule(plant_id: str):
    p = _plant(plant_id)
    if p is None:
        return {"plant_id": plant_id, "events": []}

    rng = _rng(plant_id, "cip")
    now = datetime.now(timezone.utc)
    events = []
    eid = 0

    for line in p.lines[:4]:
        is_uht = line.line_type in ("UHT_FILLING", "ASEPTIC")
        freq_h = rng.uniform(8.0, 12.0) if is_uht else rng.uniform(16.0, 24.0)
        dur_min = rng.randint(60, 90) if is_uht else rng.randint(30, 60)
        cip_type = "FULL_CIP" if is_uht else ("INTERMEDIATE" if rng.random() > 0.4 else "RINSE")

        t = now - timedelta(days=7) + timedelta(hours=rng.uniform(0, freq_h))
        while t < now + timedelta(hours=24):
            end_t = t + timedelta(minutes=dur_min)
            if end_t < now:
                status = "overdue" if rng.random() < 0.05 else "completed"
                actual = t.isoformat()
            elif t <= now:
                status = "in_progress"
                actual = t.isoformat()
            else:
                status = "upcoming"
                actual = None

            hard_deadline = (t + timedelta(hours=freq_h * 0.9)).isoformat() if (is_uht and status == "upcoming") else None

            events.append({
                "id": f"CIP-{plant_id}-{line.name}-{eid:04d}",
                "line": line.name,
                "line_type": line.line_type,
                "type": cip_type,
                "status": status,
                "scheduled_start": t.isoformat(),
                "actual_start": actual,
                "duration_minutes": dur_min,
                "is_uht_aseptic": is_uht,
                "hard_deadline": hard_deadline,
            })
            eid += 1
            t += timedelta(hours=freq_h)

    events.sort(key=lambda e: e["scheduled_start"])
    return {"plant_id": plant_id, "events": events}


@router.get("/{plant_id}/score", response_model=ComplianceScore, summary="Overall compliance score — food safety, allergen, and documentation sub-scores")
async def get_compliance_score(plant_id: str):
    rng = _rng(plant_id, "score")
    now = datetime.now(timezone.utc)

    food_safety = rng.uniform(88.0, 99.0)
    allergen = rng.uniform(85.0, 98.0)
    documentation = rng.uniform(82.0, 97.0)
    overall = food_safety * 0.40 + allergen * 0.30 + documentation * 0.30

    trend = []
    score = max(75.0, overall - rng.uniform(3.0, 8.0))
    for i in range(30):
        day = now - timedelta(days=29 - i)
        score = max(75.0, min(100.0, score + rng.gauss(0.2, 0.8)))
        trend.append({"date": day.date().isoformat(), "score": round(score, 1)})

    return {
        "plant_id": plant_id,
        "score": round(overall, 1),
        "food_safety_score": round(food_safety, 1),
        "allergen_score": round(allergen, 1),
        "documentation_score": round(documentation, 1),
        "trend": trend,
    }
