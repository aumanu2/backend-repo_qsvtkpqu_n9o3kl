import os
from datetime import date, datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from bson import ObjectId

from database import db, create_document, get_documents

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class HabitIn(BaseModel):
    name: str
    description: Optional[str] = None
    color: str = "#6366f1"
    frequency: str = "daily"  # daily or weekly
    days_of_week: Optional[List[int]] = None  # 0-6 for Mon-Sun when weekly

class HabitOut(HabitIn):
    id: str

class LogIn(BaseModel):
    day: date
    value: int = 1

@app.get("/")
def read_root():
    return {"message": "Habit Tracker API is running"}

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    return response

# Helpers

def _coerce_objectid(id_str: str) -> ObjectId:
    try:
        return ObjectId(id_str)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ID format")

# Habits Endpoints

@app.post("/api/habits", response_model=HabitOut)
def create_habit(habit: HabitIn):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    to_insert = habit.model_dump()
    inserted_id = db["habit"].insert_one({
        **to_insert,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }).inserted_id
    return HabitOut(id=str(inserted_id), **to_insert)

@app.get("/api/habits", response_model=List[HabitOut])
def list_habits():
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    docs = db["habit"].find().sort("created_at", -1)
    results = []
    for d in docs:
        d["id"] = str(d.pop("_id"))
        # remove meta fields if present
        d.pop("created_at", None)
        d.pop("updated_at", None)
        results.append(HabitOut(**d))
    return results

@app.delete("/api/habits/{habit_id}")
def delete_habit(habit_id: str):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    oid = _coerce_objectid(habit_id)
    res = db["habit"].delete_one({"_id": oid})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Habit not found")
    # also delete habit logs
    db["habitlog"].delete_many({"habit_id": habit_id})
    return {"ok": True}

# Logs Endpoints

@app.post("/api/habits/{habit_id}/logs")
def toggle_log(habit_id: str, payload: LogIn):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    # Upsert: if a log exists for that habit+day, toggle remove; else insert
    day_str = payload.day.isoformat()
    existing = db["habitlog"].find_one({"habit_id": habit_id, "day": day_str})
    if existing:
        db["habitlog"].delete_one({"_id": existing["_id"]})
        return {"checked": False}
    else:
        db["habitlog"].insert_one({
            "habit_id": habit_id,
            "day": day_str,
            "value": payload.value,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        })
        return {"checked": True}

@app.get("/api/habits/{habit_id}/logs")
def get_logs(habit_id: str, start: Optional[str] = None, end: Optional[str] = None):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    filt = {"habit_id": habit_id}
    if start and end:
        filt["day"] = {"$gte": start, "$lte": end}
    logs = list(db["habitlog"].find(filt))
    for l in logs:
        l["id"] = str(l.pop("_id"))
    return logs

# Schema endpoint for Flames DB viewer
@app.get("/schema")
def get_schema():
    from schemas import User, Product, Habit, Habitlog
    return {
        "user": User.model_json_schema(),
        "product": Product.model_json_schema(),
        "habit": Habit.model_json_schema(),
        "habitlog": Habitlog.model_json_schema(),
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
