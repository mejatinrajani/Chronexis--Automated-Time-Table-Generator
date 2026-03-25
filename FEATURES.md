# Timetable Generator - Features & User Guide

## Table of Contents

1. [Feature Overview](#feature-overview)
2. [Core Scheduling Features](#core-scheduling-features)
3. [User Interface Features](#user-interface-features)
4. [Data Management Features](#data-management-features)
5. [Advanced Features](#advanced-features)
6. [Integrations](#integrations)
7. [Accessibility Features](#accessibility-features)
8. [Performance Features](#performance-features)

---

## Feature Overview

Timetable Generator is a **comprehensive scheduling solution** with features organized into several categories:

```
┌─────────────────────────────────────────────────┐
│     TIMETABLE GENERATOR - FEATURE MAP           │
├─────────────────────────────────────────────────┤
│                                                 │
│  Core Features          UI Features             │
│  ├─ Auto Generation     ├─ Drag & Drop         │
│  ├─ Validation          ├─ Conflict Detection   │
│  ├─ Optimization        ├─ History Tracking     │
│  └─ Constraints         └─ Multi-view Display   │
│                                                 │
│  Data Features          Business Features       │
│  ├─ Excel Import        ├─ Report Generation    │
│  ├─ Excel Export        ├─ Analytics            │
│  ├─ Database Persist    └─ Version Control      │
│  └─ Configuration Save                          │
│                                                 │
└─────────────────────────────────────────────────┘
```

---

## Core Scheduling Features

### Feature 1: Intelligent Schedule Generation

**What it is:**  
Automatically creates conflict-free timetables using advanced constraint satisfaction algorithms.

**How it works:**
1. You provide constraints (subjects, rooms, faculty, time windows)
2. System models problem mathematically
3. Solver searches for valid solution
4. Returns optimized schedule in seconds

**Key capabilities:**

| Capability | Description |
|-----------|-------------|
| **Hard Constraints** | No double-booking of faculty/rooms |
| **Soft Constraints** | Minimize free periods, balance workload |
| **Flexible Duration** | Support 50-min, 60-min, 90-min slots |
| **Lab/Lecture Mix** | Automatically segregate based on room type |
| **Multi-section** | Handle dozens of sections simultaneously |
| **Real-time** | Generate in < 30 seconds for most cases |

**Parameters you control:**
- ⏰ Working hours (09:00-17:00, customizable)
- 📚 Subjects (name, credits, type)
- 🏫 Rooms (building, capacity range)
- 👨‍🏫 Faculty (name, expertise)
- 👥 Sections (student groups to schedule)

**Example:**
```
Input Configuration:
├─ Time: 09:00-17:00
├─ 3 Subjects × 3 Sections = 9 total "courses"
├─ 2 Faculty (with expertise overlap)
├─ 6 Rooms
└─ 5 Working days

Output:
Each section gets 3 distinct time slots for each subject
No teacher has two classes at the same time
No room is used twice simultaneously
Workload balanced between faculty
```

### Feature 2: Constraint Management

**Hard Constraints** (Must satisfy):

1. **No Teacher Double-Booking**
   - Each faculty member can only teach one class at a time
   - Display: 🔴 Red error if violated
   - Automatic enforcement: Solver won't create conflicts

2. **No Room Double-Booking**
   - Each room can host one class at a time
   - Display: 🔴 Red error if violated
   - Automatic enforcement: All assignments are unique

3. **Subject Hour Fulfillment**
   - Every subject must be scheduled the required number of hours
   - For "Math (3 credits)" → Must schedule 3 hours
   - Display: 🟡 Yellow warning until fulfilled

4. **Room Type Matching**
   - Lecture classes in lecture halls
   - Lab classes in laboratory spaces
   - Automatic enforcement: Room assignment respects type

**Soft Constraints** (Optimized):

1. **Minimal Free Periods**
   - Reduces gaps in schedules
   - Students/faculty stay engaged
   - Improves campus utilization
   - Weight: Highly optimized

2. **Balanced Faculty Workload**
   - Distribute teaching hours evenly
   - Prevent overload for any teacher
   - Weight: Medium optimization
   - Example: If one teacher has 10 hrs, others get ~10 hrs too

3. **Compact Scheduling**
   - Avoid fragmentation (scattered classes)
   - Prefer consecutive time slots
   - Weight: Low optimization
   - Example: Math 09:00-10:30 and 10:40-11:30 (consecutive)

### Feature 3: Feasibility Checking

**Automatic Validation** before solving:

```
Before solver runs:
├─ Do we have enough time slots? ✓
├─ Is each faculty competent for assigned subjects? ✓
├─ Are there enough rooms of each type? ✓
└─ Can workload be distributed? ✓

If any fails → "Solver failed to find valid schedule"
If all pass → Attempt solving
```

**What it checks:**

```python
def check_feasibility(data):
    # 1. Slot Availability
    #    Problem: Physics needs 2-hour slots, available only 1-hour
    #    Result: INFEASIBLE ❌

    # 2. Resource Capacity
    #    Problem: 9 sections need 27 rooms, only 6 available
    #    Result: INFEASIBLE ❌

    # 3. Faculty Capability
    #    Problem: No faculty teaches "Quantum Physics"
    #    Result: INFEASIBLE ❌

    # 4. Type Matching
    #    Problem: Chemistry Lab needs lab room, only lecture halls exist
    #    Result: INFEASIBLE ❌

    # All checks pass → FEASIBLE ✓
```

---

## User Interface Features

### Feature 1: Dashboard

**Purpose:** Central hub for schedule management

**Components:**

1. **Statistics Cards**
   - Total Classes: Number of classes generated
   - Sections: How many student groups
   - Time Slots: Available scheduling slots
   - Days Active: Working days per week

2. **Quick Actions**
   - Generate New Schedule
   - View Current Timetable
   - Check History

3. **Recent Activity Feed**
   - "Timetable for Section A updated" - 1h ago
   - "New schedule generated" - 3h ago
   - "Configuration saved" - 1 day ago

**Use Case:** Quick overview for administrators

### Feature 2: Schedule Generation Form

**Purpose:** Input data for new schedule

**Sections:**

#### Working Hours Section
```
Start Time: [09:00] ← HH:MM format
End Time: [17:00]   ← HH:MM format
Duration: [50]      ← Minutes
```
Controls available hours and slot duration

#### Subjects Section
```
[+] Add Subject
├─ Name: [Mathematics]
├─ Credits: [3]
└─ Is Lab?: [ ] Unchecked (Lecture)

[+] Add Subject
├─ Name: [Physics Lab]
├─ Credits: [4]
└─ Is Lab?: [✓] Checked (Lab)
```
Define all courses to schedule

#### Rooms Section
```
[+] Add Room Block
├─ Block: [A]      ← Building identifier
├─ Start: [101]    ← First room number
└─ End: [110]      ← Last room number
```
Specify available classroom ranges

#### Faculty Section
```
[+] Add Faculty
├─ Name: [Dr. Smith]
├─ [ ] Mathematics
├─ [✓] Physics Lab
└─ [ ] Chemistry

[+] Add Faculty
├─ Name: [Dr. Jones]
├─ [✓] Mathematics
├─ [ ] Physics Lab
└─ [✓] Chemistry
```
Define faculty and their teaching areas

#### Sections Section
```
Prefix: [CS-3]
Range: [A] to [E] → Auto-generates: CS-3A, CS-3B, CS-3C, CS-3D, CS-3E

Or Custom:
[+] CS-3AA
[+] CS-3BB
[+] CS-3F
```
Specify student sections to schedule

**Validation Indicators:**
```
✅ All required fields filled
❌ At least one subject required
❌ At least one faculty required
❌ At least one section required
```

### Feature 3: Interactive Timetable Grid

**Display Format:**

```
                Monday    Tuesday   Wednesday  Thursday  Friday
09:00-10:30    [Math]    [Phys]    [Chem]    [Math]    [Phys]
10:40-12:10    [Phys]    [Math]    [Math]    [Chem]    [Math]
[LUNCH BREAK]
13:00-14:30    [Chem]    [Math]    [Phys]    [Phys]    [Chem]
14:40-16:10    [Math]    [Chem]    [Math]    [Math]    [Phys]
16:20-17:50    [Phys]    [Math]    [Phys]    [Chem]    [Math]
```

**Each Cell Contains:**
```
┌────────────────────┐
│   SUBJECT          │
│   Dr. Smith        │
│   Room 102         │
│   (Duration: 1.5h) │
└────────────────────┘
```

**Interactive Elements:**

1. **Dragging**
   - Pick up a class
   - Drag to new time slot
   - Drop to reassign
   - Useful for manual adjustments

2. **Clicking**
   - View full class details
   - Edit subject, teacher, or room
   - Save changes

3. **Multi-Select**
   - Hold Shift + Click to select multiple classes
   - Move together or delete together

4. **Tooltip on Hover**
   - Show full subject name
   - Display teacher name
   - Show room number
   - Indicate duration

### Feature 4: Conflict Highlighting

**Visual Indicators:**

```
🟢 Green Slot     - Valid, no issues
🟡 Yellow Slot    - Warning (soft constraint violated)
🔴 Red Slot       - Critical error (hard constraint violated)
⚫ Black Slot      - Empty/break time
```

**Example Conflicts Detected:**

1. **Teacher Clash (Red)**
   ```
   Monday 10:00: Math with Dr. Smith (Room 101)
   Monday 10:00: Physics with Dr. Smith (Room 105)
   ❌ CONFLICT: Dr. Smith can't be in two places!
   ```

2. **Room Conflict (Red)**
   ```
   Tuesday 14:00: Math (Room 102)
   Tuesday 14:00: Chemistry (Room 102)
   ❌ CONFLICT: Room 102 double-booked!
   ```

3. **Incomplete Subject (Yellow)**
   ```
   Mathematics assigned: 2 hours
   Mathematics required: 3 hours
   ⚠️ WARNING: Missing 1 hour
   ```

**Color Legend Panel:**
```
Color Key:
🟢 Valid Schedule
🟡 Needs Attention
🔴 Must Fix
⚪ Free/Break Time
```

### Feature 5: Section Tabs

**Multiple Section Viewing:**

```
Tabs at top:
[CS-1A] [CS-1B] [CS-1C] ← Click to switch
└─ Shows timetable for selected section
```

**Features:**
- Quick switching between sections
- Each section has independent schedule
- Tab names match student groups
- Scrollable if many sections

**Use Case:**
```
Admin wants to see:
1. Click "CS-1A" tab → View CS-1A schedule
2. Check for conflicts
3. Click "CS-1B" tab → View CS-1B schedule
4. Make adjustments
5. Continue through all sections
```

---

## Data Management Features

### Feature 1: Excel Import

**Supported Format:**

| Faculty Name | Subject | Credits | Is Lab |
|---|---|---|---|
| Dr. Smith | Mathematics | 3 | NO |
| Dr. Smith | Physics | 3 | NO |
| Dr. Johnson | Chemistry | 4 | YES |

**Process:**

```
1. Click "Generate with Excel"
2. Select file from computer
3. System parses file
4. Auto-fills:
   - Faculty list with names
   - Subject list with credits and type
5. You manually add:
   - Room blocks
   - Sections
6. Click Generate
```

**Advantages:**
- ✅ Bulk import (50+ faculty in 1 file)
- ✅ Eliminates typos
- ✅ Faster than manual entry
- ✅ Reuse same file each semester

**Supported File Types:**
- .xlsx (Excel modern format) - **Recommended**
- .xls (Excel legacy format)
- .csv (Comma-separated values)

**Example File:**
```excel
Faculty Name,Subject,Credits,Is Lab
Dr. Alice Smith,Advanced Mathematics,4,FALSE
Dr. Alice Smith,Calculus,3,FALSE
Dr. Bob Johnson,Physics Lab,4,TRUE
Dr. Bob Johnson,Quantum Physics,3,FALSE
Dr. Carol White,Chemistry Lab,4,TRUE
Dr. Carol White,Organic Chemistry,3,FALSE
Dr. Carol White,Physics Lab,4,FALSE
```

### Feature 2: Excel Export

**Generates Professional File:**

```
File: Timetable_Export.xlsx
├─ Sheet 1: CS-1A
│  ├─ Header row: Times in 12-hour format
│  ├─ Column headers highlighted in blue
│  ├─ Data rows for each day
│  ├─ Multi-hour cells merged
│  └─ Print-friendly layout
│
├─ Sheet 2: CS-1B
│  └─ (same format)
│
├─ Sheet 3: CS-1C
│  └─ (same format)
│
└─ Sheet 4: Summary
   ├─ Total classes
   ├─ Faculty hours
   └─ Room utilization
```

**Formatting:**

1. **Headers**
   - Blue background, white text
   - Times in 12-hour format (09:00 AM)
   - Rotated for column headers
   - Height: 45px (readable)

2. **Data Cells**
   - White background for regular classes
   - Gray background for lunch breaks
   - Black text
   - Merged cells for multi-hour classes
   - Padding: 10px

3. **Content**
   - Subject name (bold)
   - Teacher name
   - Room number
   - Each on separate line (wrapped text)

4. **Printing**
   - One section per page
   - Fits on standard paper
   - All days visible
   - All time slots visible

**Export Button Location:**
```
Timetable Page → Top Right Corner
[⬇️ Export to Excel] [📋 Copy] [🔄 History]
```

### Feature 3: History & Versioning

**What's Tracked:**

```
Each generate operation saves:
├─ Run ID (automatically assigned)
├─ Timestamp (when generated)
├─ Configuration used
│  └─ All input parameters
├─ Generated schedule
│  └─ All classes with assignments
└─ Metadata
   └─ Total classes, feasibility status
```

**Access History:**

```
1. On Timetable page, click "📋 History" button
2. Modal opens with list:
   
   Run #5 - 2026-03-25 10:30 AM - 87 classes
   Run #4 - 2026-03-25 09:15 AM - 84 classes
   Run #3 - 2026-03-24 14:20 PM - 81 classes
   
3. Click a run to load that schedule
4. Can view/export that version
```

**Timeline Example:**
```
10:30 AM: First generation attempt
         └─ Result: Conflict detected

10:35 AM: Adjusted parameters, re-generated
         └─ Result: Success ✓ (Run #5)

09:15 AM (Previous day): Earlier schedule
         └─ Keep for comparison
```

**Use Cases:**
- Compare two scheduling approaches
- Revert to earlier version if changes break things
- Track schedule evolution
- Audit trail for stakeholders

### Feature 4: Configuration Saving

**What Gets Saved:**

```
Each configuration includes:
├─ Working hours (start/end/duration)
├─ Subject list with credits
├─ Room blocks with ranges
├─ Faculty with expertise
└─ Section list
```

**Auto-Save:**
- Automatically saved when schedule generated
- Can manually save entered config without generating
- Configuration ID stored in database

**Reuse Later:**
```
Semester 1 configuration:
├─ Physics (3 credits)
├─ Chemistry (4 credits)  
├─ Dr. Smith, Dr. Johnson
├─ Building A: 101-110
└─ Sections: A, B, C

Semester 2 (similar structure):
1. Load previous config
2. Update faculty names or subjects
3. Keep same building, sections
4. Generate new schedule
```

---

## Advanced Features

### Feature 1: Real-Time Validation

**Continuous Checking:**

As you edit the schedule, system constantly validates:

```
After each change:
1. Check for teacher clashes
2. Check for room conflicts
3. Check credit completion
4. Update color indicators
5. Show validation report
```

**Validation Report Panel:**

```
┌─────────────────────────────────┐
│  VALIDATION REPORT              │
├─────────────────────────────────┤
│                                 │
│ 🟢 Teacher Assignments          │
│    No clashes detected          │
│                                 │
│ 🔴 Room Utilization             │
│    Room 102: Conflict at 10:00  │
│    └─ Fix: Move Physics to 10:40│
│                                 │
│ 🟡 Subject Completion           │
│    Math: 2/3 hours scheduled    │
│    Chemistry: 4/4 hours ✓       │
│                                 │
│ STATUS: ⚠️ Needs Fixes           │
│                                 │
└─────────────────────────────────┘
```

**Interactive:**
- Click error to highlight problem cells
- Get suggestion for fix
- Implement and re-validate

### Feature 2: Clipboard Feature

**Copy/Paste Classes:**

```
1. Right-click class cell
2. Options:
   ├─ Copy to Clipboard
   ├─ Paste (fills in details)
   ├─ Delete
   └─ Edit

3. Paste same class multiple times:
   - Change time slot only
   - Change section only
   - Useful for repeated patterns
```

**Use Case:**
```
Math needs to be:
- 09:00-10:30 Monday (CS-1A)
- 09:00-10:30 Tuesday (CS-1B)
- 09:00-10:30 Wednesday (CS-1C)

Instead of entering 3 times:
1. Create first entry
2. Copy to clipboard
3. Paste in other slots
4. Change date/section
```

### Feature 3: Undo/Redo

**Change History:**

```
Click [↶ Undo] to revert last change
Click [↷ Redo] to restore reverted change
```

**What's Tracked:**
- Add/remove classes
- Move classes
- Edit details
- Each keystroke tracked
- Full edit history maintained

**Keyboard Shortcuts:**
```
Ctrl+Z (Windows) or Cmd+Z (Mac) → Undo
Ctrl+Y or Ctrl+Shift+Z → Redo
```

---

## Integrations

### Feature 1: Supabase Database

**What's Integrated:**
- ✅ Schedule persistence
- ✅ Configuration storage
- ✅ History tracking
- ✅ Real-time updates (future)

**How It Works:**
```
User action → Frontend → Backend → Supabase
                                      ↓
                         Stored in cloud database
                         ↓
User retrieves later ← Frontend ← Backend ← Supabase
```

### Feature 2: Google OR-Tools

**What's Integrated:**
- Constraint Programming solver
- Mathematical optimization
- Solution search algorithm

**In Plain Language:**
```
Input (constraints) → OR-Tools solver → Output (schedule)
```

---

## Accessibility Features

### Feature 1: Keyboard Navigation

```
Tab           - Move between form fields
Enter         - Submit form or click button
Escape        - Close dialogs/modals
Space         - Check/uncheck modals
Arrows        - Navigate grids (when implemented)
```

### Feature 2: Color Indicators

All colors have additional indicators:
```
🟢 Green = Checkmark symbol + green
🟡 Yellow = Warning symbol + yellow
🔴 Red = Error symbol + red
```

Not relying on color alone for visibility

### Feature 3: Screen Reader Support

Components include:
```
Proper HTML semantic structure
ARIA labels for buttons
Form labels linked to inputs
Error announcements for screen readers
```

### Feature 4: Mobile Responsive

Frontend adapts to screen sizes:
```
Desktop (1200px+)    → Full grid view
Tablet (768px-1199)  → Stacked layout
Mobile (< 768px)     → Simplified view
```

---

## Performance Features

### Feature 1: Lazy Loading

```
Frontend:
├─ Components load on demand
├─ Images load when visible
└─ Code splitting by route

Backend:
├─ Database pagination (1000 records at a time)
├─ Efficient queries with indexing
└─ Connection pooling
```

### Feature 2: Caching

```
Browser Cache:
├─ Static files (JS, CSS)
├─ Last schedule viewed
└─ User preferences

API Cache:
├─ History list (5 min)
├─ Configuration data (30 min)
└─ Time slots (1 hour)
```

### Feature 3: Optimization

```
Solver:
├─ Pre-feasibility checks (fail fast)
├─ Intelligent pre-assignment (reduces search space)
└─ Timeout limits (max 30 sec search)

Frontend:
├─ React Query for state management
├─ Memoization for expensive computations
└─ Virtual scrolling for large lists (future)
```

---

## Feature Matrix: What Can You Do?

| Task | Feature | Time | Difficulty |
|------|---------|------|------------|
| Generate schedule | Auto-generation | 5-30 sec | Easy |
| View schedule | Grid Display | Instant | Easy |
| Move a class | Drag-drop | 2 sec | Very Easy |
| Add new class | Manual entry | 30 sec | Easy |
| Import faculty | Excel Import | 1 min | Easy |
| Export schedule | Excel Export | 5 sec | Easy |
| Fix conflicts | Validation + editing | 5-15 min | Medium |
| Compare versions | History viewing | 1 min | Easy |
| Fine-tune schedule | Manual adjustments | 10-30 min | Medium |
| Analyze workload | Validation report | 2 min | Easy |

---

## Feature Usage Examples

### Scenario 1: Quick Schedule Generation

**Goal:** Create schedule for CS-3 in 20 minutes

**Steps:**
1. Go to Generate page (1 min)
2. Fill working hours + 5 subjects (3 min)
3. Define 2 faculty members (2 min)
4. Add room blocks (1 min)
5. Set sections: CS-3A to CS-3C (1 min)
6. Click Generate (30 sec)
7. Wait for solver (5-10 sec)
8. Review result (2 min)
9. Export to Excel (1 min)
10. Done! ✓ (12 min total)

### Scenario 2: Fine-Tuning Generated Schedule

**Goal:** Fix conflicts in auto-generated schedule

**Steps:**
1. View timetable (2 min)
2. Open validation panel (1 min)
3. See: "Dr. Smith booked in 2 classes at 10:00"
4. Drag Physics class from 10:00 to 10:40 (15 sec)
5. Validate again (2 sec)
6. See: Yellow warning "Math needs 1 more hour"
7. Add Math class at 15:00 (30 sec)
8. Validate → Green ✓
9. Export (1 min)
10. Done! ✓ (5 min total)

### Scenario 3: Using Excel Workflow

**Goal:** Import faculty from previous semester, adjust

**Steps:**
1. Prepare Excel file with faculty + subjects (5 min)
2. Go to "Generate with Excel" (1 min)
3. Upload file (10 sec)
4. System auto-fills faculty + subjects (1 sec)
5. Manually add rooms, sections (3 min)
6. Click Generate (20 sec)
7. Get result instantly (5 sec)
8. Minor tweaks if needed (5 min)
9. Export (1 min)
10. Done! ✓ (16 min total)

---

**Last Updated**: March 2026
**Feature Version**: 1.0
**Status**: All core features implemented
