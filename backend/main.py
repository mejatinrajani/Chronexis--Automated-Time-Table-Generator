import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, time
import solver_logic  # We will use functions from here!
from database import supabase

app = FastAPI()

origins = ["http://localhost:5173", "http://localhost:3000", "*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ... (Input Models: SubjectInput, RoomBlockInput, etc. REMAIN THE SAME) ...
class SubjectInput(BaseModel):
    name: str
    credits: int
    is_lab: bool

class RoomBlockInput(BaseModel):
    block: str
    start: int
    end: int

class FacultyInput(BaseModel):
    name: str
    subjects: List[str]

class GeneratePayload(BaseModel):
    start_time: str 
    end_time: str   
    duration: int   
    subjects: List[SubjectInput]
    rooms: List[RoomBlockInput]
    faculty: List[FacultyInput]
    sections: List[str]


# --- HELPER: Use Solver Logic to get Slots WITH Breaks ---
def get_solver_slots(start_str: str, end_str: str, duration: int) -> List[str]:
    """
    Uses the EXACT logic from solver_logic.py to generate slots.
    This ensures the list includes the LUNCH GAP automatically.
    """
    try:
        s_h, s_m = map(int, start_str.split(":"))
        e_h, e_m = map(int, end_str.split(":"))
        shift_start = time(s_h, s_m)
        shift_end = time(e_h, e_m)

        # 1. Calculate Lunch (Same as solver)
        lunch_breaks = solver_logic.calculate_lunch_break(shift_start, shift_end)
        
        # 2. Generate Slots (Same as solver)
        # We pass a dummy day (0 = Monday) just to get the time objects
        slots = solver_logic.generate_time_slots(
            working_days=[0], 
            day_names=["Mon"],
            shift_start=shift_start, 
            shift_end=shift_end,
            slot_duration_minutes=duration,
            break_periods=lunch_breaks
        )
        
        # 3. Extract just the start times as strings
        return [s.start_time.strftime("%H:%M") for s in slots]

    except Exception as e:
        print(f"Error calculating solver slots: {e}")
        return []

# --- ENDPOINTS ---

@app.post("/api/generate/")
def generate_schedule(payload: GeneratePayload):
    print(f"🚀 Generating for {len(payload.sections)} sections...")

    # 1. Save Config
    config_id = None
    try:
        config_res = supabase.table("timetable_configs").insert({
            "config_json": payload.dict()
        }).execute()
        config_id = config_res.data[0]['id']
    except Exception as e:
        print(f"⚠️ Config Save Failed: {e}")

    # 2. Run Solver
    generated_data = solver_logic.solve_custom_timetable(payload.dict())
    
    if not generated_data:
        raise HTTPException(status_code=400, detail="Solver failed to find a valid schedule.")

    # 3. Save Result
    try:
        run_res = supabase.table("timetable_runs").insert({
            "total_classes": len(generated_data),
            "config_id": config_id
        }).execute()
        new_run_id = run_res.data[0]['id']

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
                "credits": item["credits"],
                "duration": item.get("duration", 1) 
            })
        
        chunk_size = 500
        for i in range(0, len(slots_to_insert), chunk_size):
            supabase.table("timetable_slots").insert(slots_to_insert[i:i+chunk_size]).execute()
            
    except Exception as e:
        print(f"⚠️ DB Error: {e}")

    # 4. Return Data + CORRECT Slots with Gaps
    # We use the new helper function here
    full_time_slots = get_solver_slots(payload.start_time, payload.end_time, payload.duration)
    
    return {
        "schedule": generated_data,
        "time_slots": full_time_slots 
    }

@app.get("/api/latest/")
def get_latest_schedule():
    try:
        # 1. Get Latest Run
        runs = supabase.table("timetable_runs").select("*").order("created_at", desc=True).limit(1).execute()
        if not runs.data:
            return {"schedule": [], "time_slots": []}
        
        latest_run = runs.data[0]
        run_id = latest_run['id']
        config_id = latest_run.get('config_id')
        
        # 2. Fetch Slots
        slots_res = supabase.table("timetable_slots").select("*").eq("run_id", run_id).execute()
        
        formatted_schedule = []
        for item in slots_res.data:
            formatted_schedule.append({
                "id": f"{item['section']}-{item['subject']}-{item['id']}",
                "section": item["section"],
                "day": item["day"],
                "time": item["time"],
                "subject": item["subject"],
                "teacher": item["teacher"],
                "room": item["room"],
                "credits": item["credits"],
                "duration": item.get("duration", 1)
            })

        # 3. RECONSTRUCT TIME SLOTS FROM CONFIG
        full_time_slots = []
        if config_id:
            config_res = supabase.table("timetable_configs").select("config_json").eq("id", config_id).execute()
            if config_res.data:
                cfg = config_res.data[0]['config_json']
                # USE THE SOLVER LOGIC HERE TOO!
                full_time_slots = get_solver_slots(cfg['start_time'], cfg['end_time'], cfg['duration'])
        
        if not full_time_slots:
             full_time_slots = sorted(list(set(s['time'] for s in formatted_schedule)))

        return {
            "schedule": formatted_schedule,
            "time_slots": full_time_slots
        }

    except Exception as e:
        print(f"Error fetching latest: {e}")
        return {"schedule": [], "time_slots": []}
@app.get("/api/history/")
def get_history():
    try:
        # Fetch all runs, ordered by newest first
        response = supabase.table("timetable_runs").select("*").order("created_at", desc=True).execute()
        return response.data
    except Exception as e:
        print(f"Error fetching history list: {e}")
        return []

@app.get("/api/history/{run_id}")
def get_specific_run(run_id: int):
    try:
        # 1. Fetch Slots for this Run
        slots_res = supabase.table("timetable_slots").select("*").eq("run_id", run_id).execute()
        
        formatted_schedule = []
        for item in slots_res.data:
            formatted_schedule.append({
                "id": f"{item['section']}-{item['subject']}-{item['id']}",
                "section": item["section"],
                "day": item["day"],
                "time": item["time"],
                "subject": item["subject"],
                "teacher": item["teacher"],
                "room": item["room"],
                "credits": item["credits"],
                "duration": item.get("duration", 1)
            })

        # 2. Fetch Config to Reconstruct Time Slots (The Fix for the "Missing Columns" bug)
        full_time_slots = []
        
        # Get the config_id for this run
        run_info = supabase.table("timetable_runs").select("config_id").eq("id", run_id).single().execute()
        
        if run_info.data and run_info.data.get('config_id'):
            config_id = run_info.data['config_id']
            config_res = supabase.table("timetable_configs").select("config_json").eq("id", config_id).execute()
            
            if config_res.data:
                cfg = config_res.data[0]['config_json']
                # Recalculate slots using the same logic as the solver
                full_time_slots = get_solver_slots(cfg['start_time'], cfg['end_time'], cfg['duration'])
        
        # Fallback if no config exists (legacy runs)
        if not full_time_slots:
             full_time_slots = sorted(list(set(s['time'] for s in formatted_schedule)))

        # 3. Return BOTH
        return {
            "schedule": formatted_schedule,
            "time_slots": full_time_slots
        }

    except Exception as e:
        print(f"Error fetching history run {run_id}: {e}")
        return {"schedule": [], "time_slots": []}
if __name__ == "__main__":

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)