# 🚀 Quick Start Guide - Timetable Generator

## ✅ What Was Changed

1. **solver_logic.py** - Cleaned up:
   - ❌ Removed `build_stress_test()` function 
   - ❌ Removed `validate_and_print()` function
   - ❌ Removed `if __name__ == "__main__":` block
   - ✅ Added `solve_custom_timetable()` wrapper for API compatibility
   - ✅ Core solver logic **unchanged** - all scheduling algorithms remain intact

2. **main.py** - Already configured correctly:
   - Calls `solver_logic.solve_custom_timetable()`
   - Handles database storage automatically
   - Provides API endpoints

3. **database.py** - No changes needed:
   - Supabase integration ready

## 🎯 How to Use

### Step 1: Start the Backend
```powershell
cd backend
python main.py
```
You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### Step 2: Generate Timetable via API

Run the PowerShell script from the project root:
```powershell
.\generate_timetable.ps1
```

**OR** Use curl directly (Windows PowerShell):
```powershell
curl -X POST "http://127.0.0.1:8000/api/generate/" `
  -H "Content-Type: application/json" `
  -d '@payload.json'
```

**OR** Use curl (Linux/Mac):
```bash
curl -X POST "http://127.0.0.1:8000/api/generate/" \
  -H "Content-Type: application/json" \
  -d @payload.json
```

### Step 3: View Results

**Option A: In Frontend UI**
```
Open: http://localhost:8080
Navigate to Dashboard → Latest Schedule
```

**Option B: Via API**
```
GET http://127.0.0.1:8000/api/latest/
```

## 📊 Example: 20 Sections with 0.8x Room Capacity

### Room Budget Calculation:
- **Sections**: 20
- **Theory rooms**: floor(0.8 × 20) = **16 rooms** (101-116)
- **Lab rooms**: floor(0.8 × 20 × 3) = **48 rooms** (1-48)
  - (Each section has 3 lab subgroups, requiring separate rooms)

### Example Payload (JSON):
```json
{
  "start_time": "08:00",
  "end_time": "18:00",
  "duration": 50,
  "sections": ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T"],
  "subjects": [
    {"name": "Mathematics", "is_lab": false, "credits": 4},
    {"name": "Physics", "is_lab": false, "credits": 3},
    {"name": "Chemistry", "is_lab": false, "credits": 3},
    {"name": "English", "is_lab": false, "credits": 2},
    {"name": "Data Science", "is_lab": false, "credits": 3},
    {"name": "OOP", "is_lab": false, "credits": 3},
    {"name": "Physics Lab", "is_lab": true, "credits": 2},
    {"name": "Chemistry Lab", "is_lab": true, "credits": 2},
    {"name": "DS Lab", "is_lab": true, "credits": 1}
  ],
  "rooms": [
    {"block": "THEORY", "start": 101, "end": 116},
    {"block": "LAB", "start": 1, "end": 48}
  ],
  "faculty": [
    {"name": "Dr. Smith", "subjects": ["Mathematics"]},
    {"name": "Dr. Johnson", "subjects": ["Physics"]},
    {"name": "Dr. Williams", "subjects": ["Chemistry"]},
    {"name": "Prof. Brown", "subjects": ["English"]},
    {"name": "Prof. Davis", "subjects": ["Data Science"]},
    {"name": "Prof. Miller", "subjects": ["OOP"]},
    {"name": "Lab Tech A", "subjects": ["Physics Lab"]},
    {"name": "Lab Tech B", "subjects": ["Chemistry Lab"]},
    {"name": "Lab Tech C", "subjects": ["DS Lab"]}
  ]
}
```

## 🔄 Workflow

1. **POST** `/api/generate/` with timetable config
   - Solver runs
   - Results saved to database
   - Returns schedule + time_slots

2. **GET** `/api/latest/` 
   - Fetches most recent timetable
   - Frontend displays in grid view

3. **GET** `/api/history/`
   - Lists all past runs
   - Can load any previous timetable

## 📝 API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/generate/` | Create new timetable |
| GET | `/api/latest/` | Get most recent timetable |
| GET | `/api/history/` | List all timetables |
| GET | `/api/history/{run_id}` | Get specific timetable |

## 🛠️ Customization

### Modify Room Capacity
In your payload, change:
```json
"rooms": [
  {"block": "THEORY", "start": 101, "end": 120},  // 20 rooms (1x capacity)
  {"block": "LAB", "start": 1, "end": 60}         // 60 rooms (1x capacity)
]
```

### Add More Faculty
```json
"faculty": [
  {"name": "Dr. New", "subjects": ["Mathematics"]},
  ...
]
```

### Adjust Working Hours
```json
"start_time": "09:00",
"end_time": "17:00",
"duration": 45  // 45-minute slots instead of 50
```

## ✨ Features Preserved

- ✅ Lab sessions as consecutive 2-slot blocks
- ✅ Faculty availability constraints
- ✅ Section-specific lab subgroups
- ✅ Scales to 75+ sections
- ✅ CP-SAT optimization
- ✅ Soft constraints (spreading, load balancing)
- ✅ Hard constraints (no overlaps, unavailability)

## 🐛 Troubleshooting

**Error: "Solver failed to find a valid schedule"**
- Add more rooms
- Add more faculty
- Reduce credit requirements per section

**Error: "Connection refused"**
- Check backend is running: `python main.py`
- Check port 8000 is available

**Error: "SUPABASE_URL/SUPABASE_KEY not found"**
- Create `.env` file in backend folder
- Add: `SUPABASE_URL=...` and `SUPABASE_KEY=...`

---

**That's it! Your timetable generator is ready to use.** 🎉
