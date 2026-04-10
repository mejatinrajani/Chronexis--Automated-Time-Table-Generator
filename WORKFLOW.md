# 🚀 FINAL INSTRUCTIONS - How to Use Your Timetable Generator

## The Simplest Way (2 Files to Double-Click)

### Step 1: Start Backend
Double-click this file:
```
start_backend.bat
```

You should see a window with:
```
Uvicorn running on http://127.0.0.1:8000
```

**Keep this window open!**

### Step 2: Generate Timetable
In a new Command Prompt, double-click:
```
send_request.bat
```

You'll see output like:
```
Sending request...
[Response JSON output]
Done!
```

### Step 3: View Results
Open your browser:
```
http://localhost:8080
```

Go to: **Dashboard → Latest Schedule**

You'll see the complete timetable with all 20 sections scheduled!

---

## Alternative: Using PowerShell (One Command)

```powershell
# Terminal 1: Start backend
cd C:\Users\mejat\timetable_generator\backend
python main.py

# Terminal 2: Generate timetable
cd C:\Users\mejat\timetable_generator
.\generate_timetable.ps1
```

---

## Alternative: Using Python

```powershell
# Terminal 1: Start backend
cd C:\Users\mejat\timetable_generator\backend
python main.py

# Terminal 2: Run Python test
cd C:\Users\mejat\timetable_generator
python test_api.py
```

---

## 📊 What You're Testing

**Configuration: 20 Sections with 0.8x Room Capacity**

Rooms:
- Theory: 16 rooms (THEORY-101 to THEORY-116)
- Lab: 48 rooms (LAB-1 to LAB-48)

Sections: A, B, C, D, E, F, G, H, I, J, K, L, M, N, O, P, Q, R, S, T

Subjects (per section):
- Mathematics (4 slots)
- Physics (3 slots)
- Chemistry (3 slots)
- English (2 slots)
- Data Science (3 slots)
- OOP (3 slots)
- Physics Lab (2 slots)
- Chemistry Lab (2 slots)
- DS Lab (1 slot)

**Result: ~540 scheduled classes**

---

## ✅ Success Looks Like

### In Backend Terminal:
```
  🔍 Running feasibility checks…
✅ Feasibility passed.

👩‍🏫 Resources pre-assigned.

📐 Total instances: 540  |  Linked lab groups: 60

Building H0 (linked lab subgroup sync)…
Building H1 (section no-overlap)…
Building H2 (teacher no-overlap)…
Building H3 (room no-overlap)…
Building H4 (intra-subject ordering)…
Building H5 (max 2 same-subject/day)…
Building H6 (lab sessions on different days)…
Building H7 (theory cap ≤ 6/day)…

Building soft objective…
  Objective terms: 540

🚀 Starting CP-SAT solver…

✅ OPTIMAL  |  Objective: 123.0  |  Wall time: 45.2s
```

### In Browser:
```
Dashboard should show:
- Timetable grid with all days and times
- All 20 sections on left sidebar
- Click any class to see details
- Green = Theory, Red/Purple = Lab
```

### In cURL Response:
```json
{
  "schedule": [
    {"section": "A", "subject": "Mathematics", "day": "Monday", ...},
    {"section": "A", "subject": "Physics", "day": "Monday", ...},
    ...
    (540 total entries)
  ],
  "time_slots": ["08:00", "08:50", "09:40", ..., "17:10"]
}
```

---

## ⚠️ Common Issues

| Issue | Fix |
|-------|-----|
| **"Connection refused"** | start_backend.bat not running, or use different port |
| **"Port 8000 in use"** | Kill process on port 8000 or restart computer |
| **"Solver failed"** | Add more rooms in payload, or more faculty |
| **Empty browser** | Wait 1-2 seconds, refresh, or check port 8080 |
| **Slow response** | Solver takes 1-5 minutes, be patient |
| **Empty schedule** | Check browser console for errors |

---

## 📝 Customizing Requests

To change the configuration, edit:
```
payload_20_sections.json
```

Then run:
```
send_request.bat
```

### Examples:

**Increase Rooms (easier scheduling):**
```json
"rooms": [
  {"block": "THEORY", "start": 101, "end": 125},  // 25 instead of 16
  {"block": "LAB", "start": 1, "end": 60}         // 60 instead of 48
]
```

**Add More Sections:**
```json
"sections": ["A", "B", "C", ..., "Z", "AA", "BB"]  // 28 sections
```

**Adjust Working Hours:**
```json
"start_time": "09:00",
"end_time": "17:00"
```

---

## 🎯 What Happens Behind the Scenes

1. **Solver receives your config**
   - 20 sections, 9 subjects, ~9 faculty
   - ~540 total class slots needed
   - 16 theory rooms, 48 lab rooms

2. **Pre-processing (seconds)**
   - Splits sections into subgroups
   - Pre-assigns teachers to sections
   - Assigns lab breakout groups

3. **Constraint Modeling (seconds)**
   - Creates CP-SAT model
   - Defines hard constraints (no overlaps)
   - Defines soft constraints (optimization goals)

4. **Optimization (minutes)**
   - Solver tries different combinations
   - Minimizes unused rooms
   - Spreads classes across week
   - Balances teacher load

5. **Solution Extraction (seconds)**
   - Converts solution to readable format
   - Saves to database
   - Returns to frontend

---

## 📚 Documentation Files

After running successfully, check these for more info:

- **QUICK_START.md** - Detailed setup guide
- **CHANGES_SUMMARY.md** - What was changed and why
- **README_SETUP.md** - Complete reference
- **WORKFLOW.md** - This file

---

## 🎉 You're Ready!

Everything is clean, tested, and ready to go.

Just:
1. Double-click `start_backend.bat`
2. Double-click `send_request.bat`
3. View results at `http://localhost:8080`

**That's it!** 🚀

---

**Questions?** All documented in QUICK_START.md
