# Timetable Generator - Complete Setup & User Guide

## Table of Contents

### For New Users
1. [Quick Start (5 minutes)](#quick-start)
2. [System Requirements](#system-requirements)
3. [Installation](#installation)
4. [First Time Setup](#first-time-setup)

### For Users
5. [How to Use the Application](#how-to-use-the-application)
6. [Step-by-Step Workflow](#step-by-step-workflow)
7. [Features Explained](#features-explained)
8. [Troubleshooting](#troubleshooting)

### For Developers
9. [Development Setup](#development-setup)
10. [Project Structure](#project-structure)
11. [Running Tests](#running-tests)

---

## Quick Start

### Prerequisites Checklist
- [ ] Windows/Mac/Linux computer
- [ ] Google Chrome, Firefox, or Edge browser
- [ ] Stable internet connection
- [ ] Python 3.8+ (for backend)
- [ ] Node.js/Bun (for frontend)

### 5-Minute Setup

```bash
# 1. Clone the repository
git clone <repository-url>
cd timetable_generator

# 2. Create and activate Python environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Set up Supabase credentials
# Create a .env file in backend/ directory with:
# SUPABASE_URL=your_supabase_url
# SUPABASE_KEY=your_supabase_key

# 4. Install Python dependencies
cd backend
pip install -r requirements.txt
cd ..

# 5. Install Node dependencies
cd frontend
npm install  # or: bun install
cd ..

# 6. Start the application
# Terminal 1: Start backend
cd backend
uvicorn main:app --reload

# Terminal 2: Start frontend
cd frontend
npm run dev  # or: bun dev
```

**Access the application**: Open browser to `http://localhost:5173`

---

## System Requirements

### Minimum Requirements

| Component | Requirement |
|-----------|-------------|
| **OS** | Windows 10+, macOS 10.14+, Linux (Ubuntu 18.04+) |
| **RAM** | 4 GB |
| **Disk Space** | 2 GB (for dependencies) |
| **Internet** | Broadband (for Supabase connectivity) |
| **Browser** | Chrome 90+, Firefox 88+, Safari 14+, Edge 90+ |

### Recommended Requirements

| Component | Recommendation |
|-----------|----------------|
| **OS** | Windows 11 Pro, macOS 12+, Ubuntu 20.04+ |
| **RAM** | 8 GB |
| **Disk Space** | 5 GB |
| **Internet** | 10 Mbps+ connection |
| **CPU** | Multi-core processor (4+ cores) |

### Software Requirements

```
Python:   3.9, 3.10, or 3.11
Node.js:  16.x, 18.x, or 20.x
npm/bun:  Latest version
Git:      2.30 or higher
```

### Network Requirements

- **Outbound HTTPS**: Required for Supabase connectivity
- **Localhost Access**: For development (127.0.0.1:5173, :8000)
- **Firewall**: May need to allow localhost access

---

## Installation

### Step 1: Clone Repository

```bash
# Clone from GitHub
git clone https://github.com/yourusername/timetable_generator.git

# Navigate to project
cd timetable_generator

# Verify structure
ls -la  # Should see: backend/, frontend/, timetable/, LICENSE.md, etc.
```

### Step 2: Set Up Backend

#### Install Python

**Windows:**
```bash
# Download from python.org or use Windows Store
# Verify installation:
python --version
```

**macOS:**
```bash
# Using Homebrew
brew install python@3.11

# Verify:
python3 --version
```

**Linux (Ubuntu):**
```bash
sudo apt update
sudo apt install python3.11 python3.11-venv
python3.11 --version
```

#### Create Python Virtual Environment

```bash
# Navigate to project root
cd timetable_generator

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate

# macOS/Linux:
source venv/bin/activate

# Verify activation (prompt should show (venv))
which python  # macOS/Linux
where python  # Windows
```

#### Install Backend Dependencies

```bash
cd backend

# Install required packages
pip install -r requirements.txt

# Expected packages:
# - fastapi
# - uvicorn
# - ortools
# - supabase
# - pandas
# - python-dotenv

# Verify installation:
python -c "import fastapi; print(fastapi.__version__)"
```

#### Configure Environment Variables

Create `.env` file in `backend/` directory:

```bash
# backend/.env

# Supabase Credentials (Get from supabase.com)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-public-key

# Optional: Database connection string
DATABASE_URL=postgresql://user:password@host/db

# Optional: Server configuration
DEBUG=False
SECRET_KEY=your-secret-key-here
```

**How to get Supabase credentials:**

1. Go to [supabase.com](https://supabase.com)
2. Click "Sign Up"
3. Create a new organization and project
4. In project settings, copy:
   - Project URL → SUPABASE_URL
   - Anon/public key → SUPABASE_KEY
5. Create the required tables (or they auto-create on first write)

### Step 3: Set Up Frontend

#### Install Node.js

**Windows/macOS:**
- Download from [nodejs.org](https://nodejs.org)
- Choose LTS version (currently 20.x)
- Run installer and follow prompts
- Verify: `node --version` and `npm --version`

**Linux (Ubuntu):**
```bash
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs
node --version
```

#### Option A: Use npm

```bash
cd frontend

# Install dependencies
npm install

# Verify installation:
npm list react  # Should show React version
```

#### Option B: Use Bun (Faster)

```bash
# Install Bun (one-time)
curl -fsSL https://bun.sh/install | bash

cd frontend

# Install dependencies with Bun
bun install

# Verify:
bun --version
```

### Step 4: Verify Installation

```bash
# Check Python
python --version
pip list | grep fastapi

# Check Node
node --version
npm --version

# Check Git
git --version

# Check project structure
tree -L 2 timetable_generator/  # Shows directory structure
```

---

## First Time Setup

### 1. Database Initialization

The database tables auto-create on first API call. To verify:

```bash
# Start backend (see instructions below)
cd backend && uvicorn main:app --reload

# In browser, visit:
# http://localhost:8000/docs

# You should see Swagger UI with available endpoints
```

### 2. Test Backend

```bash
# Make a test API call
curl -X POST http://localhost:8000/api/generate/ \
  -H "Content-Type: application/json" \
  -d '{
    "start_time": "09:00",
    "end_time": "17:00",
    "duration": 50,
    "subjects": [
      {
        "name": "Math",
        "credits": 3,
        "is_lab": false
      }
    ],
    "rooms": [
      {
        "block": "A",
        "start": 101,
        "end": 105
      }
    ],
    "faculty": [
      {
        "name": "Dr. Smith",
        "subjects": ["Math"]
      }
    ],
    "sections": ["CS-1A"]
  }'

# Expected response: 200 OK with generated schedule JSON
```

### 3. Test Frontend

```bash
# Start frontend
cd frontend
npm run dev  # or: bun dev

# Open browser: http://localhost:5173
# You should see the login/home page
```

### 4. Create Test Data

After both are running:

1. Navigate to `http://localhost:5173`
2. Click "Generate" in the demo interface
3. Fill in sample data:
   - **Subjects**: Math, Physics (3 credits each)
   - **Rooms**: Block A (101-105)
   - **Faculty**: Dr. Smith (teaches Math, Physics)
   - **Sections**: CS-1A, CS-1B
   - **Time**: 09:00 - 17:00, 50-min slots
4. Click "Generate Schedule"
5. View result in the timetable viewer

---

## How to Use the Application

### User Interface Overview

```
┌─────────────────────────────────────────────┐
│     TIMETABLE GENERATOR - Navigation        │
├─────────────────────────────────────────────┤
│ Home │ Dashboard │ Generate │ View │ Export │
├─────────────────────────────────────────────┤
│                                             │
│  [Main Content Area]                        │
│  - Input Forms                              │
│  - Schedule Display Grid                    │
│  - Interactive Elements                     │
│                                             │
└─────────────────────────────────────────────┘
```

### Main Pages

#### 1. **Home Page** (`/`)
- Introduction to the application
- Quick links to main features
- Call-to-action buttons

**What you can do:**
- Read about the application
- Click "Get Started" to begin

#### 2. **Dashboard** (`/dashboard`)
- Overview of scheduled timetables
- Quick statistics
- Recent activity

**What you can do:**
- View summary statistics
- Access quick actions
- See recent changes

#### 3. **Generate Page** (`/generate`)
- **Purpose**: Create a new schedule
- **Time**: ~5-10 minutes to fill and generate

**What you need to provide:**
```
Working Hours Section:
├─ Start Time: 09:00 (HH:MM format)
├─ End Time: 17:00 (HH:MM format)
└─ Duration: 50 (minutes per slot)

Subjects Section:
├─ Subject Name: "Mathematics"
├─ Credits: 3 (for course load)
└─ Is Lab?: No (checkbox)

Rooms Section:
├─ Building Block: "A" (building identifier)
├─ Room Number Range: 101 - 110
└─ (Can add multiple blocks)

Faculty Section:
├─ Faculty Name: "Dr. Smith"
├─ Select Subjects: [Math, Physics]
└─ (Can add multiple faculty)

Sections Section:
├─ Section Prefix: "CS-3"
├─ Section Range: A to E (generates A,B,C,D,E)
└─ Or add custom sections like "3AA"
```

**Step-by-step:**
1. Fill "Start Time" and "End Time"
2. Add at least one subject with name and credits
3. Add at least one room block
4. Add at least one faculty member
5. Assign subjects to faculty (checkboxes)
6. Define sections (auto-generate or custom)
7. Click "Generate Schedule"
8. Wait for solver to find solution
9. View result on next page

#### 4. **Generate with Excel** (`/generate-with-excel`)
- **Purpose**: Import faculty+subject data from Excel file
- **Time**: ~2 minutes

**Excel File Format (Required columns):**
```
| Faculty Name | Subject       | Credits | Is Lab |
|--------------|---------------|---------|--------|
| Dr. Smith    | Mathematics   | 3       | No     |
| Dr. Smith    | Physics       | 3       | No     |
| Dr. Johnson  | Chemistry     | 4       | Yes    |
| Dr. Johnson  | Physics       | 3       | No     |
```

**Steps:**
1. Prepare Excel file with above format
2. Click "Upload File"
3. System auto-fills Faculty and Subjects
4. Manually add Rooms and Sections
5. Click "Generate"

#### 5. **Student Timetable** (`/student-timetable`)
- **Purpose**: View and edit generated schedule
- **Time**: Interactive, no time limit

**Features:**
- Grid view with Days (rows) × Time Slots (columns)
- Each cell = one class assignment
- Click slot to see details: Subject, Teacher, Room, Duration
- Drag-drop to move classes (for manual adjustments)
- Add new slots with "+" button
- Delete slots with trash icon
- Validate schedule for conflicts
- Export to Excel

**Interactions:**
```
┌─────────────────────────────────────────┐
│ Monday │ Tuesday │ Wednesday │ ...      │
├─────────────────────────────────────────┤
│        │         │           │          │
│ 09:00  │ Math    │ Physics   │ ...      │ ← Draggable cells
│        │ Dr.Smith│ Dr.Jones  │          │
│        │ Room101 │ Room102   │          │
│        │         │           │          │
├─────────────────────────────────────────┤
│ 10:00  │ ...     │ ...       │ ...      │
├─────────────────────────────────────────┤
```

#### 6. **Teacher Timetable** (`/teacher-timetable`)
- **Purpose**: View schedule from faculty perspective
- Shows all classes for a selected teacher
- Helps detect overload

#### 7. **Room Schedule** (`/room's-schedule`)
- **Purpose**: View room utilization
- See when each room is occupied
- Check for double-bookings

#### 8. **Profile** (`/profile`)
- User account settings (future feature)
- Preferences and configuration

---

## Step-by-Step Workflow

### Scenario: Schedule a 3rd Year Computer Science Program

**Timeline**: ~20 minutes

#### Step 1: Gather Information (5 min)
Collect these details:

**Working Hours:**
- Start: 09:00 AM
- End: 05:00 PM
- Each class duration: 50 minutes (with 10-min buffer)

**Subjects (per semester):**
- Mathematics-III (3 credits, lecture)
- Data Structures (3 credits, lecture)
- Web Development (4 credits, lab)
- Database Systems (3 credits, lab)

**Rooms Available:**
- Building A: 101-110 (lecture halls, capacity 60)
- Building B: 201-210 (labs, capacity 30)

**Faculty & Expertise:**
- Dr. Smith: Math-III, Data Structures
- Dr. Johnson: Web Development
- Dr. Miller: Database Systems, Data Structures

**Student Sections:**
- CS-3A, CS-3B, CS-3C (3 sections)

#### Step 2: Prepare Input Data (2 min)

Create spreadsheet or prepare form:

```
Subjects:
├─ Mathematics-III (3 credits, NO lab)
├─ Data Structures (3 credits, NO lab)
├─ Web Development (4 credits, YES lab)
└─ Database Systems (3 credits, YES lab)

Rooms:
├─ Block A: 101-110 (lectures)
└─ Block B: 201-210 (labs)

Faculty:
├─ Dr. Smith: [Math-III, Data Structures]
├─ Dr. Johnson: [Web Development]
└─ Dr. Miller: [Database Systems, Data Structures]

Sections:
├─ CS-3A
├─ CS-3B
└─ CS-3C
```

#### Step 3: Input into System (5 min)

**Option A: Manual Input**

1. Navigate to `/generate`
2. Fill form:
   - Start Time: `09:00`
   - End Time: `17:00`
   - Duration: `50`
3. Add Subjects:
   - Click "Add Subject"
   - Mathematics-III, 3 credits, unchecked
   - Repeat for others
4. Add Rooms:
   - Click "Add Room"
   - Block: A, Start: 101, End: 110
   - Repeat for Block B
5. Add Faculty:
   - Click "Add Faculty"
   - Dr. Smith, select [Math-III, Data Structures]
   - Repeat for others
6. Sections:
   - Prefix: CS-3
   - Range: A to C (auto-generates)
7. Click "Generate Schedule"

**Option B: Excel Import**

1. Create Excel: 4 columns (Faculty Name, Subject, Credits, Is Lab)
2. Navigate to `/generate-with-excel`
3. Upload file
4. System auto-fills Faculty + Subjects
5. Manually add Rooms and Sections
6. Click "Generate"

#### Step 4: Wait for Solver (< 30 sec)

System will:
- Validate all constraints are satisfiable
- Run optimization algorithm
- Return feasible schedule or error

**If successful:**
→ Proceed to Step 5

**If error:**
→ See [Troubleshooting: Solver Errors](#troubleshooting)

#### Step 5: Review Generated Schedule (5 min)

1. Automatically redirected to `/student-timetable`
2. See grid with all sections
3. Check each section's schedule
4. Look for visual issues:
   - Red indicators = conflicts
   - Yellow = warnings
   - Green = valid

**Validation Report:**
The system shows:
- ✅ No teacher double-bookings
- ✅ No room conflicts
- ✅ All subjects scheduled
- ✅ Balanced workload (if applicable)

#### Step 6: Manual Adjustments (optional, 5 min)

If needed, manually edit:

1. **Move a class**: Drag from one slot to another
2. **Add a class**: Click "+" button, fill details
3. **Delete a class**: Click trash icon
4. **Change teacher**: Edit and save
5. **Validate**: Auto-checks after each change

#### Step 7: Export for Distribution (1 min)

1. Click "Export to Excel" button
2. File downloads as `Timetable_Export.xlsx`
3. Send to students/faculty
4. Each section gets its own Excel sheet
5. Formatted with proper headers and colors

#### Step 8: Save & Archive (done automatically)

- Schedule auto-saves to database
- Appears in history for future reference
- Can reload and re-generate anytime

---

## Features Explained

### Feature 1: Intelligent Schedule Generation

**What it does:**
- Takes complex constraints (subjects, rooms, faculty, time)
- Finds a valid, optimized schedule automatically
- Uses mathematical optimization (Google OR-Tools)

**How long it takes:**
- Small institution (< 10 sections): 1-5 seconds
- Medium institution (10-50 sections): 5-30 seconds
- Large institution (> 50 sections): 30-120 seconds

**What "optimal" means:**
- No conflicts (hard requirement)
- Minimal free periods (soft optimization)
- Balanced teacher workload (soft optimization)
- Avoids fragmented schedules (soft optimization)

**When it might fail:**
- More subjects than available slots
- More classes than available rooms
- Constraints mathematically impossible
→ Error message: "Solver failed to find valid schedule"
→ Solution: Reduce classes or add more resources

### Feature 2: Interactive Schedule Editor

**What you can do:**
- ✏️ **Drag-and-drop**: Move classes between time slots
- ➕ **Add new class**: Add ad-hoc assignments
- 🗑️ **Delete class**: Remove from schedule
- 🔄 **Undo/Redo**: Revert changes
- 📝 **Edit details**: Change subject, teacher, room
- ⏱️ **Check validation**: Real-time conflict detection

**Good for:**
- Fine-tuning autogenerated schedules
- Handling last-minute changes
- Accommodating special requests
- Balancing improvised constraints

**Example workflow:**
```
Generated Schedule
    ↓
[Review and identify issues]
    ↓
[Manually adjust problem areas]
    ↓
[Validate to confirm fixes]
    ↓
[Export final version]
```

### Feature 3: Real-Time Validation

**What it checks:**
1. **Teacher Clashes**: Same faculty two places same time?
   - Display: 🔴 Critical - "Dr. Smith in 2 classes at 10:00 AM"

2. **Room Conflicts**: Same room double-booked?
   - Display: 🔴 Critical - "Room 101 occupied by Math & Physics"

3. **Credit Requirements**: All subject hours satisfied?
   - Display: 🟡 Warning - "Math needs 3 hours, only 2 scheduled"

4. **Load Imbalance**: Teacher overworked?
   - Display: 🟡 Warning - "Dr. Smith: 25 hours (very high)"

**Color coding:**
```
🟢 Green   = All constraints satisfied
🟡 Yellow  = Warnings (advisory, can proceed)
🔴 Red     = Critical errors (must fix)
```

**How to use:**
1. System validates continuously
2. Check validation panel on right side
3. Click error to highlight problematic cells
4. Fix and re-validate

### Feature 4: Excel Integration

#### A. Import Faculty Data

**Prepare Excel file:**
```
Faculty Name         Subject              Credits  Is Lab
─────────────────────────────────────────────────────────
Dr. Smith            Mathematics          3        FALSE
Dr. Smith            Physics              3        FALSE
Dr. Johnson          Chemistry            4        TRUE
Dr. Johnson          Physics              3        FALSE
```

**Upload to system:**
1. Go to `/generate-with-excel`
2. Click "Upload File" or drag-drop
3. System parses data
4. Auto-fills Faculty and Subjects fields
5. You add Rooms and Sections manually

**Advantages:**
- Faster than manual entry
- No typos in faculty names
- Bulk import for large institutions
- Data integrity

#### B. Export Schedule to Excel

**Generates professional file:**
```
Excel File: Timetable_Export.xlsx
├─ Sheet: CS-3A
│  ├─ Day/Time header row
│  ├─ Columns for each time slot
│  ├─ Rows for each day
│  └─ Cells with: Subject, Teacher, Room
│
├─ Sheet: CS-3B
│  └─ (similarly formatted)
│
└─ Sheet: CS-3C
   └─ (similarly formatted)
```

**Features:**
- ✅ Proper formatting (colors, fonts)
- ✅ Multiple sheets (one per section)
- ✅ Lunch break marked separately
- ✅ Merged cells for multi-hour classes
- ✅ Print-friendly layout
- ✅ Time displayed in 12-hour format

### Feature 5: Schedule History

**What is stored:**
- Every schedule generated
- Timestamp of generation
- Configuration used
- Statistics (total classes, etc.)

**How to access:**
1. Click "History" button on Timetable page
2. See list of all previous runs
3. Click entry to load that schedule
4. Compare different versions

**Use cases:**
- Compare multiple scheduling approaches
- Revert to previous version if needed
- Audit trail for changes
- Reference for future semesters

### Feature 6: Multiple Viewing Modes

**Student View** (`/student-timetable`)
- Shows one section at a time
- Grid: Days × Time Slots
- Click tabs to switch sections
- Focus on student's own schedule

**Teacher View** (`/teacher-timetable`)
- Shows one teacher at a time
- Display: All classes they teach
- Different formats:
  - Grid view (traditional table)
  - List view (chronological)
  - Week view (calendar)

**Room View** (`/room's-schedule`)
- Shows one room at a time
- Display: All classes in that room
- Identifies empty slots (gaps)
- Usage statistics

---

## Troubleshooting

### Backend Issues

#### Problem: "Could not connect to Supabase"

**Error message:**
```
Error connecting to database
⚠️ DB Error Full
```

**Causes:**
1. Incorrect SUPABASE_URL or SUPABASE_KEY
2. No internet connection
3. Supabase account expired

**Solution:**
1. Check `.env` file:
   ```bash
   cat backend/.env
   ```
2. Verify credentials at supabase.com
3. Check internet connection:
   ```bash
   ping google.com
   ```
4. Restart backend:
   ```bash
   python -m uvicorn main:app --reload
   ```

#### Problem: "ModuleNotFoundError: No module named 'fastapi'"

**Causes:**
- Dependencies not installed
- Wrong virtual environment

**Solution:**
```bash
# Activate correct environment
source venv/bin/activate  # macOS/Linux
# or: venv\Scripts\activate  # Windows

# Install dependencies
cd backend
pip install -r requirements.txt

# Verify:
python -c "import fastapi; print('OK')"
```

#### Problem: Port 8000 already in use

**Error message:**
```
Address already in use
OSError: [Errno 48] Address already in use
```

**Solution:**
```bash
# Option 1: Use different port
uvicorn main:app --reload --port 8001

# Option 2: Kill process using port 8000
# Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# macOS/Linux:
lsof -i :8000
kill -9 <PID>
```

### Frontend Issues

#### Problem: "Module not found" errors

**Error message:**
```
ERROR in ./src/pages/Generate.tsx
Module not found: Can't resolve '@/components/...'
```

**Causes:**
- Node modules not installed
- Alias configuration broken

**Solution:**
```bash
cd frontend

# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install  # or: bun install

# Restart dev server
npm run dev
```

#### Problem: Port 5173 already in use

**Solution:**
```bash
# Use alternative port
npm run dev -- --port 5174

# Or kill process
# Windows:
netstat -ano | findstr :5173
taskkill /PID <PID> /F

# macOS/Linux:
lsof -i :5173
kill -9 <PID>
```

#### Problem: "Cannot find API endpoint"

**Error message:**
```
Failed to fetch http://localhost:8000/api/generate/
```

**Causes:**
- Backend not running
- Wrong API URL in code
- CORS not configured

**Solution:**
1. Verify backend is running:
   ```bash
   # Check in browser: http://localhost:8000/docs
   # Should show Swagger UI
   ```
2. If backend is off:
   ```bash
   cd backend
   uvicorn main:app --reload
   ```
3. Check CORS in backend/main.py:
   ```python
   origins = ["http://localhost:5173", "*"]
   ```

### Solver Issues

#### Problem: "Solver failed to find valid schedule"

**Error message:**
```
{
  "detail": "Solver failed to find a valid schedule."
}
```

**Causes:**
1. **Over-constrained**: Too many classes, too few time slots
2. **Impossible requirements**: Subject hours exceed available slots
3. **Resource shortage**: More rooms needed than available

**Solutions:**

**A. Check feasibility manually:**
```
Math:
- 3 sections
- Math needs 3 hours/week per section
- Total needed: 3 × 3 = 9 hours
- Available slots: 5 days × 8 hours/day = 40 slots
- Status: ✅ FEASIBLE

→ Problem is elsewhere
```

**B. Reduce constraints:**
- Use fewer sections (split into parts)
- Reduce subjects (combine or remove)
- Add more classrooms
- Extend working hours

**C. Check faculty availability:**
- Ensure each faculty teaches at least one subject
- Verify no faculty has impossible workload

#### Problem: "Solver taking too long"

**Causes:**
- Very large institution (> 1000 classes)
- Complex constraints
- Solver stuck in search

**Solution:**
```python
# Edit backend/main.py
# Add timeout:
solver.Solve(strategy, max_seconds=30)  # Max 30 seconds

# Also optimize solver parameters:
solver.SolveWithLogSearch(...)
```

### Data Issues

#### Problem: "Import file format incorrect"

**Error message:**
```
Error parsing Excel file
File must have columns: Faculty Name, Subject, Credits, Is Lab
```

**Causes:**
- Column names don't match exactly
- Data types incorrect (Credits must be number)
- Extra/missing columns

**Solution:**
Prepare file exactly:
```
| Faculty Name | Subject    | Credits | Is Lab |
|---|---|---|---|
| Dr. Smith | Math | 3 | FALSE |
| Dr. Smith | Physics | 3 | FALSE |
```

**Column requirements:**
- Faculty Name: Text
- Subject: Text
- Credits: Number (3, 4, 5)
- Is Lab: Yes/No or TRUE/FALSE or text

#### Problem: "Duplicate section names"

**Error message:**
```
Section 'CS-1A' defined twice
```

**Causes:**
- Auto-generated (A-C) overlaps with custom ("CS-1A", "CS-1B")
- Manual typo

**Solution:**
- Clear auto-generation OR custom, choose one
- Or ensure no duplicates:
  ```
  Auto-generated: CS-3A, CS-3B, CS-3C
  Custom: CS-3D, CS-3E (different names)
  ```

### Validation Issues

#### Problem: "Critical errors - cannot export"

**Error message:**
```
🔴 CRITICAL: Faculty Dr. Smith booked in 2 classes at 10:00 AM
```

**Causes:**
- Manual drag-drop created conflict
- Invalid data entry
- System state corrupted

**Solution:**
1. Click error to highlight problem cells
2.   Manually drag problematic class to free slot
3. Validate again
4. If unresolvable, reload from history:
   - Click "History" button
   - Select previous valid version
   - Re-do manual edits

#### Problem: "Too many warnings - export not recommended"

**What this means:**
- Schedule has non-critical issues
- Still valid, but suboptimal
- E.g., some subjects incomplete, load imbalanced

**Solution:**
1. Review warnings individually
2. Try to fix the most critical ones
3. If acceptable, proceed with export
4. Export includes note: "Schedule has warnings"

### Database Issues

#### Problem: "Data not saving to database"

**Error message:**
```
⚠️ DB Error Full
```

**Causes:**
- Supabase connection lost
- Rate limit exceeded (write quota)
- Permission denied

**Solution:**
1. Check Supabase status:
   - Visit supabase.com dashboard
   - Verify project is active

2. Check connection:
   ```bash
   python -c "import supabase; print('OK')"
   ```

3. Wait a minute, retry
   - Supabase may have temporary issues
   - Auto-retry should kick in

4. Check browser console for errors:
   - Press F12
   - Go to Console tab
   - Look for red errors

#### Problem: "Cannot retrieve old schedules from history"

**Causes:**
- Database corrupted
- Old entries deleted
- Connection issue

**Solution:**
```python
# Test database directly:
python
>>> from database import supabase
>>> result = supabase.table("timetable_runs").select("*").execute()
>>> print(result.data)

# If empty: No history stored (first time use)
# If errors: Database connection issue
```

### General Issues

#### Problem: "Blank white screen"

**Causes:**
- React app didn't load
- JavaScript error
- Missing dependencies

**Solution:**
1. Check browser console (F12 → Console)
2. Look for red error messages
3. Hard refresh: Ctrl+Shift+R (or Cmd+Shift+R)
4. Clear browser cache:
   - Settings → Privacy → Clear browsing data
   - Check "Cookies and cached images"
   - Clear

4. Restart frontend:
   ```bash
   npm run dev
   ```

#### Problem: "Slow performance"

**Causes:**
- Large dataset
- Browser cache full
- Too many open tabs

**Solution:**
1. Clear browser cache
2. Reduce number of sections (split into batches)
3. Use Firefox/Chrome (better performance)
4. Close other applications
5. More RAM helps (minimize other programs)

#### Problem: "Can't find help"

**Resources:**
1. **Built-in Help**: Hover over icons for tooltips
2. **API Docs**: http://localhost:8000/docs (Swagger UI)
3. **This Guide**: GitHub README and docs/
4. **Code Comments**: Look in relevant `.tsx` or `.py` files
5. **GitHub Issues**: Report bugs or ask questions

---

## Development Setup

### For Contributors

#### 1. Fork & Clone

```bash
# Fork repository on GitHub
# Then clone your fork:
git clone https://github.com/yourusername/timetable_generator.git
cd timetable_generator

# Add upstream remote:
git remote add upstream https://github.com/original-owner/timetable_generator.git
```

#### 2. Create Feature Branch

```bash
git checkout -b feature/my-feature
# or for bug fix:
git checkout -b fix/bug-description
```

#### 3. Install Dev Dependencies

```bash
# Backend dev tools
cd backend
pip install -r requirements.txt
pip install pytest pytest-cov black flake8

# Frontend dev tools
cd ../frontend
npm install
# Includes: eslint, vitest, prettier (auto-installed)
```

#### 4. Run Tests

```bash
# Python tests
cd backend
pytest

# Frontend tests
cd ../frontend
npm run test

# Type checking
npx tsc --noEmit
```

#### 5. Code Quality

```bash
# Python formatting
black backend/

# Python linting
flake8 backend/

# Frontend linting
npm run lint

# Frontend type check
npm run type-check
```

#### 6. Commit & Push

```bash
git add .
git commit -m "feat: add new feature" # or "fix:", "docs:", etc.
git push origin feature/my-feature
```

#### 7. Create Pull Request

- Go to GitHub
- Click "Compare & pull request"
- Fill in description
- Request review from maintainers

### Development Workflow

```
┌──────────────────────┐
│  Development Cycle   │
└──────────────────────┘
         ↓
1. Create feature branch
         ↓
2. Make code changes
         ↓
3. Run tests locally
         ↓
4. Fix any failures
         ↓
5. Code quality checks
         ↓
6. Commit with message
         ↓
7. Push to your fork
         ↓
8. Create pull request
         ↓
9. Address review comments
         ↓
10. Merge to main
```

---

## Project Structure

```
timetable_generator/
│
├── backend/
│   ├── main.py                    # FastAPI app entry point
│   ├── database.py                # Supabase configuration
│   ├── solver_logic.py            # Constraint satisfaction algorithm
│   ├── requirements.txt           # Python dependencies
│   ├── .env                       # Environment variables (secrets)
│   └── solver_tests_different_cases/
│       └── *.py                   # Test/example solvers
│
├── frontend/
│   ├── src/
│   │   ├── pages/                 # Page components (routes)
│   │   ├── components/            # Reusable components
│   │   ├── hooks/                 # Custom React hooks
│   │   ├── utils/                 # Helper functions
│   │   ├── lib/                   # Shared libraries
│   │   ├── App.tsx                # Root component
│   │   └── main.tsx               # Entry point
│   ├── public/                    # Static assets
│   ├── package.json               # Node dependencies
│   └── vite.config.ts             # Build configuration
│
├── timetable/                     # Django project (optional)
│   ├── core/                      # Core Django apps
│   ├── manage.py                  # Django management
│   └── settings.py                # Django configuration
│
├── PROJECT_OVERVIEW.md            # What is this project
├── ARCHITECTURE.md                # Technical details
├── SETUP_GUIDE.md                 # This file
├── API_DOCUMENTATION.md           # API reference
├── CONTRIBUTING.md                # For contributors
├── LICENSE.md                     # MIT License
└── README.md                      # Quick reference

```

### File Purposes

| File/Folder | Purpose |
|---|---|
| `main.py` | FastAPI application, all routes |
| `solver_logic.py` | Mathematical solver, constraints, algorithm |
| `database.py` | Supabase client initialization |
| `App.tsx` | React root component, routing setup |
| `pages/` | Each file = one page/route |
| `components/` | Reusable UI elements |
| `utils/` | Helper functions (validation, export, etc.) |
| `package.json` | npm dependencies, build scripts |
| `vite.config.ts` | Frontend build configuration |
| `tsconfig.json` | TypeScript configuration |
| `tailwind.config.ts` | Tailwind CSS theming |

---

## Running Tests

### Python Tests

```bash
cd backend

# Run all tests
pytest

# Run specific test file
pytest test_solver.py

# Run with coverage
pytest --cov=. --cov-report=html

# Verbose output
pytest -v
```

### Frontend Tests

```bash
cd frontend

# Run tests once
npm run test

# Watch mode (re-run on changes)
npm run test:watch

# Coverage report
npm run test:coverage
```

### Manual Testing Checklist

```
[ ] Backend starts without errors
[ ] Frontend loads on http://localhost:5173
[ ] Can fill and submit generate form
[ ] Schedule render in grid correctly
[ ] Can drag-drop slots
[ ] Validation detects conflicts
[ ] Can export to Excel
[ ] Excel file downloads and opens
[ ] History populates after generation
[ ] Can load previous schedules
[ ] No console errors (F12)
```

---

## Next Steps

### After Installation

1. ✅ Verify both backend and frontend running
2. ✅ Test with sample data (see "First Time Setup")
3. ✅ Read [How to Use](#how-to-use-the-application)
4. ✅ Try generating a schedule
5. ✅ Export to Excel
6. ✅ Make manual adjustments
7. ✅ Explore all pages and features

### For Production Deployment

See [ARCHITECTURE.md - Deployment Section](./ARCHITECTURE.md#deployment-architecture)

### For Development

See [Development Setup](#development-setup) section above

### Getting Help

- 📖 **Documentation**: Read this guide
- 💬 **GitHub Issues**: Ask questions or report bugs
- 🔧 **API Docs**: Visit http://localhost:8000/docs when backend running
- 📝 **Code Comments**: Check source files for detailed comments

---

## Frequently Asked Questions (FAQ)

**Q: Can I use this for my institution?**
A: Yes! It's open source (MIT License). You can use, modify, and distribute freely.

**Q: How many students/classes can it handle?**
A: Tested up to 100+ sections with hundreds of classes. Performance depends on complexity.

**Q: Can I customize the constraints?**
A: Yes! Edit `solver_logic.py` to add/modify constraints for your needs. See code comments.

**Q: How do I add my own subjects/faculty?**
A: Through the Generate page. Data is stored in Supabase, reusable for future schedules.

**Q: Can multiple people use it simultaneously?**
A: Currently single-user design. Future versions could add multi-user with authentication.

**Q: What if the solver takes too long?**
A: Set timeout in `main: py` (currently None). Or reduce complexity (fewer sections).

**Q: Is my data secure?**
A: Uses Supabase PostgreSQL with SSL/TLS encryption. No real storage until you share explicitly.

**Q: Can I self-host instead of using Supabase?**
A: Yes! Replace Supabase with your own PostgreSQL. Modify `database.py` to use `psycopg2`.

**Q: How do I update/upgrade the software?**
A: `git pull origin main` to get latest updates. May need to `pip install -r requirements.txt` again.

---

**Last Updated**: March 2026
**Version**: 1.0
**Status**: Production Ready
