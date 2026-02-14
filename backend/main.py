from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import solver_logic
from database import supabase
import uvicorn

app = FastAPI()

# Enable CORS for Frontend
origins = ["http://localhost:5173", "http://localhost:3000", "*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- MODELS ---
class TimetableEntry(BaseModel):
    id: str
    section: str
    day: str
    time: str
    subject: str
    teacher: str
    room: str
    credits: int

# --- API ENDPOINTS ---

@app.get("/")
def home():
    return {"message": "Timetable Solver with Supabase is Running"}

@app.get("/api/get-schedule/")
def generate_and_save_schedule():
    """
    1. Runs Solver (Wait ~300s).
    2. Saves result to Supabase.
    3. Returns JSON to Frontend.
    """
    print("⏳ Starting Solver...")
    generated_data = solver_logic.solve_timetable()
    
    if not generated_data:
        raise HTTPException(status_code=400, detail="Solver failed to find a solution.")

    print(f"✅ Solver finished. Saving {len(generated_data)} slots to Supabase...")

    try:
        # A. Create a new 'Run' entry
        run_response = supabase.table("timetable_runs").insert({
            "total_classes": len(generated_data)
        }).execute()
        
        # Get the ID of the run we just created
        new_run_id = run_response.data[0]['id']

        # B. Prepare slots for bulk insert
        slots_to_insert = []
        for item in generated_data:
            slots_to_insert.append({
                "run_id": new_run_id,
                "section": item["section"],
                "day": item["day"],
                "time": item["time"],
                "subject": item["subject"],
                "teacher": item["teacher"],
                "room": item["room"],
                "credits": item["credits"]
            })

        # C. Bulk Insert (Supabase handles this efficiently)
        supabase.table("timetable_slots").insert(slots_to_insert).execute()
        
        print(f"💾 Saved successfully! Run ID: {new_run_id}")
        
        return generated_data

    except Exception as e:
        print(f"❌ Database Error: {e}")
        # Even if DB fails, return the data to user so they don't lose it
        return generated_data

@app.get("/api/history/")
def get_history():
    """Returns a list of all past generated timetables."""
    response = supabase.table("timetable_runs").select("*").order("created_at", desc=True).execute()
    return response.data

@app.get("/api/history/{run_id}")
def get_specific_run(run_id: int):
    """Returns the slots for a specific past run."""
    # 1. Fetch the slots
    response = supabase.table("timetable_slots").select("*").eq("run_id", run_id).execute()
    data = response.data
    
    # 2. Transform back to Frontend Format (Adding the 'id' field React needs)
    formatted_data = []
    for item in data:
        formatted_data.append({
            "id": f"{item['section']}-{item['subject']}-{item['id']}", # Recreate a unique key
            "section": item["section"],
            "day": item["day"],
            "time": item["time"],
            "subject": item["subject"],
            "teacher": item["teacher"],
            "room": item["room"],
            "credits": item["credits"]
        })
        
    return formatted_data

if __name__ == "__main__":
    print("🚀 Starting The Server...")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)