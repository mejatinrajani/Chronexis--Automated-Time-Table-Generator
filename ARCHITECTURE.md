# Timetable Generator - Technical Architecture

## Table of Contents
1. [System Overview](#system-overview)
2. [Architecture Diagram](#architecture-diagram)
3. [Frontend Architecture](#frontend-architecture)
4. [Backend Architecture](#backend-architecture)
5. [Database Design](#database-design)
6. [API Design](#api-design)
7. [Solver Algorithm](#solver-algorithm)
8. [Data Flow](#data-flow)
9. [Security Architecture](#security-architecture)
10. [Deployment Architecture](#deployment-architecture)

---

## System Overview

The Timetable Generator is a **three-tier web application** with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────┐
│                      PRESENTATION TIER                      │
│         Frontend: React + TypeScript (Browser)              │
│  - User Input Collection                                    │
│  - Schedule Visualization                                  │
│  - Interactive Editing                                     │
│  - Export/Reporting                                        │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP/REST (JSON)
┌────────────────────────▼────────────────────────────────────┐
│                      APPLICATION TIER                       │
│        Backend: FastAPI + Python                           │
│  - REST API Endpoints                                      │
│  - Request Validation                                      │
│  - Business Logic                                          │
│  - Constraint Solver Integration                           │
│  - Database Operations                                     │
└────────────────────────┬────────────────────────────────────┘
                         │ SQL Protocol
┌────────────────────────▼────────────────────────────────────┐
│                       DATA TIER                             │
│        Supabase (PostgreSQL) + Cloud Storage               │
│  - Timetable Configurations                                │
│  - Generated Schedules                                     │
│  - Execution History                                       │
│  - User Data (if extended)                                 │
└─────────────────────────────────────────────────────────────┘
```

### Technology Rationale

| Choice | Reason |
|--------|--------|
| **FastAPI** | Fast, automatic API documentation, built-in validation |
| **React** | Rich ecosystem, component reusability, large community |
| **TypeScript** | Type safety, better developer experience, fewer runtime errors |
| **OR-Tools** | Proven, industry-standard constraint solver |
| **Supabase** | Serverless PostgreSQL, real-time support, easy auth extension |

---

## Frontend Architecture

### Directory Structure

```
frontend/
├── src/
│   ├── pages/                    # Route components (page-level)
│   │   ├── Index.tsx             # Home/landing page
│   │   ├── Login.tsx             # Authentication page
│   │   ├── Signup.tsx            # User registration
│   │   ├── Dashboard.tsx         # Main dashboard/overview
│   │   ├── Generate.tsx          # Schedule generation form
│   │   ├── GenerateTimeTableUsingExcel.tsx  # Excel import
│   │   ├── Timetable.tsx         # Schedule viewer/editor
│   │   ├── TeacherTimetable.tsx  # Faculty schedule view
│   │   ├── RoomSchedule.tsx      # Room utilization view
│   │   ├── Profile.tsx           # User profile
│   │   └── NotFound.tsx          # 404 page
│   │
│   ├── components/               # Reusable UI components
│   │   ├── AppButton.tsx         # Custom button
│   │   ├── AppSidebar.tsx        # Navigation sidebar
│   │   ├── AuthCard.tsx          # Login/signup card
│   │   ├── ClipboardArea.tsx     # Slot clipboard
│   │   ├── DashboardLayout.tsx   # Layout wrapper
│   │   ├── DeleteZone.tsx        # Drag-drop delete zone
│   │   ├── DraggableSlot.tsx     # Draggable time slot
│   │   ├── HeaderBar.tsx         # Top navigation
│   │   ├── HistoryModal.tsx      # Version history viewer
│   │   ├── InputField.tsx        # Form input
│   │   ├── Modal.tsx             # Generic modal
│   │   ├── NavLink.tsx           # Navigation link
│   │   ├── SectionTabs.tsx       # Section switcher
│   │   ├── TimetableGrid.tsx     # Schedule grid display
│   │   └── ui/                   # Shadcn UI components (auto-generated)
│   │
│   ├── hooks/                    # Custom React hooks
│   │   ├── use-mobile.tsx        # Mobile device detection
│   │   └── use-toast.ts          # Toast notification hook
│   │
│   ├── utils/                    # Utility functions
│   │   ├── dataMapper.ts         # API response to grid conversion
│   │   ├── dragState.ts          # Drag-drop state management
│   │   ├── excelExport.ts        # Excel file generation
│   │   ├── roomMapper.ts         # Room data transformation
│   │   ├── teacherMapper.ts      # Faculty data transformation
│   │   └── Validator.ts          # Schedule validation rules
│   │
│   ├── lib/                      # Shared libraries
│   │   └── utils.ts              # Helper functions (cn, etc.)
│   │
│   ├── test/                     # Test files
│   │   └── *.test.ts             # Unit/integration tests
│   │
│   ├── App.tsx                   # Root component
│   ├── main.tsx                  # React entry point
│   ├── vite-env.d.ts             # Vite type definitions
│   ├── App.css                   # Global styles
│   └── index.css                 # Base CSS
│
├── public/                       # Static assets
├── vite.config.ts               # Vite configuration
├── tsconfig.json                # TypeScript configuration
├── tailwind.config.ts           # Tailwind CSS configuration
├── eslint.config.js             # ESLint rules
└── package.json                 # Dependencies & scripts
```

### Frontend Data Flow

```
User Interaction
      ↓
Component State (useState/useContext)
      ↓
Event Handler
      ↓
Validation (Validator.ts)
      ↓
API Call (fetch)
      ↓
Response Processing (dataMapper.ts)
      ↓
State Update
      ↓
Re-render
      ↓
UI Update
```

### Component Hierarchy

```
App
├── BrowserRouter
│   ├── Route: /login → Login
│   ├── Route: /signup → Signup
│   ├── Route: /dashboard → Dashboard
│   ├── Route: /generate → Generate
│   │   └── Uses: InputField, AppButton
│   ├── Route: /generate-with-excel → GenerateTimeTableUsingExcel
│   ├── Route: /student-timetable → Timetable
│   │   ├── TimetableGrid
│   │   ├── SectionTabs
│   │   ├── DraggableSlot (multiple)
│   │   ├── DashboardLayout
│   │   └── HistoryModal
│   ├── Route: /teacher-timetable → TeacherTimetable
│   ├── Route: /room's-schedule → RoomSchedule
│   └── Route: /profile → Profile
│
└── Providers:
    ├── QueryClientProvider (React Query)
    ├── TooltipProvider (Radix UI)
    ├── Toaster (Sonner)
    └── Sonner (Alternative Toaster)
```

### Key Utilities Explained

#### dataMapper.ts
Converts API response format to grid format for UI display:

```typescript
// Input (from API)
{
  id: "CS-1-Math-001",
  section: "CS-1",
  day: "Monday",
  start_time: "09:00",
  end_time: "10:30",
  subject: "Mathematics",
  teacher: "Dr. Smith",
  room: "101",
  credits: 3,
  duration: 2
}

// Output (for Grid)
GridData[section][day][time] = {
  subject: "Mathematics",
  teacher: "Dr. Smith",
  room: "101",
  credits: 3,
  duration: 2 // spans multiple time slots
}
```

#### Validator.ts
Detects scheduling conflicts in real-time:

- **Teacher Clashes**: Same teacher in two places at same time
- **Room Conflicts**: Same room double-booked
- **Credit Mismatches**: Subject hours not fulfilled
- **Severity Levels**: Critical (must fix) vs Warning (advisory)

#### excelExport.ts
Generates Excel files with:
- Multiple sheets (one per section)
- Formatted headers with time ranges
- Color coding (lunch breaks highlighted)
- Configurable column widths

---

## Backend Architecture

### Directory Structure

```
backend/
├── main.py                      # FastAPI app & routes
├── database.py                  # Supabase client
├── solver_logic.py              # Constraint satisfaction algorithm
├── solver_logic_old_working.py  # Backup of proven version
├── requirements.txt             # Python dependencies
├── .env                         # Environment variables (secrets)
│
└── solver_tests_different_cases/  # Test files
    ├── nice_scheduling_solver.py
    └── v9_latest_solver_with_detailed_explanation.py
```

### API Endpoint Architecture

FastAPI structure with organized routes:

```python
app = FastAPI()

# CORS Configuration
app.add_middleware(CORSMiddleware, ...)

# Routes:
@app.post("/api/generate/")
def generate_schedule(payload: GeneratePayload)
    # 1. Validate input
    # 2. Call solver
    # 3. Save to database
    # 4. Return result

@app.get("/api/latest/")
def get_latest_schedule()
    # Retrieve most recent generation

@app.get("/api/history/")
def get_history()
    # List all previous generations

@app.get("/api/history/{run_id}")
def get_specific_run(run_id: int)
    # Get specific historical run

@app.get("/api/config/{config_id}")
def get_config(config_id: int)
    # Retrieve saved configuration
```

### FastAPI Request/Response Cycle

```
HTTP Request (JSON)
    ↓
CORS Middleware (validate origin)
    ↓
Pydantic Model Validation (schema, types)
    ↓
Route Handler
    ├→ Business Logic
    ├→ Database Operations
    └→ Solver Invocation
    ↓
Response Model Creation
    ↓
HTTP Response (JSON 200/400/500)
```

### Pydantic Models (Data Validation)

```python
class SubjectInput(BaseModel):
    name: str
    credits: int
    is_lab: bool

class RoomBlockInput(BaseModel):
    block: str      # Building identifier
    start: int      # Room number range start
    end: int        # Room number range end

class FacultyInput(BaseModel):
    name: str
    subjects: List[str]  # Subject names they teach

class GeneratePayload(BaseModel):
    start_time: str              # "HH:MM" format
    end_time: str                # "HH:MM" format
    duration: int                # Minutes (e.g., 50)
    subjects: List[SubjectInput]
    rooms: List[RoomBlockInput]
    faculty: List[FacultyInput]
    sections: List[str]          # ["CS-1A", "CS-1B", ...]
```

### Database Integration

#### Supabase Tables Schema

**timetable_configs**
```sql
CREATE TABLE timetable_configs (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    config_json JSONB NOT NULL,  -- Stores complete GeneratePayload
    created_at TIMESTAMP DEFAULT NOW()
);
```

**timetable_runs**
```sql
CREATE TABLE timetable_runs (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    total_classes INT,
    config_id BIGINT REFERENCES timetable_configs(id),
    created_at TIMESTAMP DEFAULT NOW()
);
```

**timetable_slots**
```sql
CREATE TABLE timetable_slots (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    run_id BIGINT NOT NULL REFERENCES timetable_runs(id),
    section VARCHAR(50),
    day VARCHAR(20),
    start_time VARCHAR(5),       -- "HH:MM" format
    end_time VARCHAR(5),
    subject VARCHAR(100),
    teacher VARCHAR(100),
    room VARCHAR(10),
    credits INT,
    total_credits INT,
    duration INT,                -- Number of slots this occupies
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### Database Operations Pattern

```python
# Insert configuration
config_res = supabase.table("timetable_configs").insert({
    "config_json": payload.dict()
}).execute()
config_id = config_res.data[0]['id']

# Insert run metadata
run_res = supabase.table("timetable_runs").insert({
    "total_classes": len(generated_data),
    "config_id": config_id
}).execute()
new_run_id = run_res.data[0]['id']

# Bulk insert slots (chunked for performance)
chunk_size = 500
for i in range(0, len(slots_to_insert), chunk_size):
    supabase.table("timetable_slots").insert(
        slots_to_insert[i:i+chunk_size]
    ).execute()

# Retrieve with pagination
all_slots = []
page_size = 1000
start = 0
while True:
    response = supabase.table("timetable_slots") \
        .select("*") \
        .eq("run_id", run_id) \
        .range(start, start + page_size - 1) \
        .execute()
    if not response.data:
        break
    all_slots.extend(response.data)
    if len(response.data) < page_size:
        break
    start += page_size
```

---

## Database Design

### Entity Relationship Diagram

```
┌─────────────────────┐
│  timetable_configs  │
├─────────────────────┤
│ id (PK)             │
│ config_json (JSON)  │
│ created_at          │
└──────────┬──────────┘
           │ (1:1)
           │
┌──────────▼─────────────┐
│   timetable_runs       │
├────────────────────────┤
│ id (PK)                │
│ total_classes          │
│ config_id (FK)         │
│ created_at             │
└──────────┬─────────────┘
           │ (1:Many)
           │
┌──────────▼─────────────────┐
│   timetable_slots           │
├─────────────────────────────┤
│ id (PK)                     │
│ run_id (FK)                 │
│ section, day                │
│ start_time, end_time        │
│ subject, teacher, room      │
│ credits, duration           │
│ created_at                  │
└─────────────────────────────┘
```

### Indexing Strategy

For optimal query performance:

```sql
CREATE INDEX idx_runs_created_at ON timetable_runs(created_at DESC);
CREATE INDEX idx_slots_run_id ON timetable_slots(run_id);
CREATE INDEX idx_slots_section_day ON timetable_slots(section, day);
CREATE INDEX idx_slots_teacher ON timetable_slots(teacher);
CREATE INDEX idx_slots_room ON timetable_slots(room);
```

---

## API Design

### RESTful Principles

| Method | Endpoint | Purpose | Return |
|--------|----------|---------|--------|
| **POST** | `/api/generate/` | Create new schedule | `{schedule: Array, time_slots: Array}` |
| **GET** | `/api/latest/` | Fetch most recent schedule | `{schedule: Array, time_slots: Array}` |
| **GET** | `/api/history/` | List all generations | `Array of run metadata` |
| **GET** | `/api/history/{run_id}` | Get specific generation | `{schedule: Array, time_slots: Array}` |
| **GET** | `/api/config/{config_id}` | Retrieve saved config | `{config_json: Object}` |

### Request/Response Examples

#### Generate Schedule (POST /api/generate/)

**Request:**
```json
{
  "start_time": "09:00",
  "end_time": "17:00",
  "duration": 50,
  "subjects": [
    {
      "name": "Mathematics",
      "credits": 3,
      "is_lab": false
    }
  ],
  "rooms": [
    {
      "block": "AB",
      "start": 101,
      "end": 110
    }
  ],
  "faculty": [
    {
      "name": "Dr. Smith",
      "subjects": ["Mathematics"]
    }
  ],
  "sections": ["CS-1A", "CS-1B"]
}
```

**Successful Response (200):**
```json
{
  "schedule": [
    {
      "id": "CS-1A-Mathematics-001",
      "section": "CS-1A",
      "day": "Monday",
      "start_time": "09:00",
      "end_time": "10:30",
      "subject": "Mathematics",
      "teacher": "Dr. Smith",
      "room": "101",
      "credits": 3,
      "total_credits": 3,
      "duration": 2
    }
  ],
  "time_slots": ["09:00", "09:50", "11:00", "12:00", "13:00", "14:00", "15:00", "16:00"]
}
```

**Error Response (400):**
```json
{
  "detail": "Solver failed to find a valid schedule."
}
```

---

## Solver Algorithm

### High-Level Overview

The solver uses **Constraint Programming (CP)** to model scheduling as a mathematical optimization problem.

```
Steps:
1. MODEL: Define decision variables
   - Assignment of (subject, teacher, room, section, time slot)

2. CONSTRAINTS: Add hard constraints
   - No teacher double-booking
   - No room double-booking
   - All subject hours must be scheduled
   - Lab/lecture type matching

3. OBJECTIVES: Add soft constraints to optimize
   - Minimize free periods
   - Balance faculty workload
   - Avoid fragmented schedules

4. SOLVE: Run CP solver
   - Uses branch-and-bound algorithm
   - Explores solution space efficiently
   - Returns first feasible solution

5. EXTRACT: Convert solution to output format
```

### Key Algorithm Components (from solver_logic.py)

#### 1. Time Slot Generation
```python
def generate_time_slots(
    working_days: List[int],
    day_names: List[str],
    shift_start: time,
    shift_end: time,
    slot_duration_minutes: int = 50,
    break_periods: List[Tuple[time, time]] = None
) -> List[Slot]:
    """
    Generates valid time slots avoiding break periods.
    
    Example:
    Input: 09:00-17:00, duration=50min, lunch=12:00-13:00
    Output: [09:00-09:50, 09:50-10:40, ...skips lunch..., 13:00-13:50, ...]
    """
```

#### 2. Feasibility Checking
```python
def check_feasibility(data: MinimalData) -> Tuple[bool, str]:
    """
    Pre-solver validation. Catches impossible schedules early.
    
    Checks:
    - Enough slots for each subject duration
    - Each section has enough total slots
    - Faculty capacity not exceeded
    - Room types available for subjects
    """
```

#### 3. Pre-assignment (Load Balancing)
```python
def preassign_resources(data: MinimalData) -> Tuple[teacher_map, room_map]:
    """
    Intelligently pre-assigns teachers and rooms based on:
    - Faculty competencies
    - Subject requirements
    - Load balancing (prevents one teacher overload)
    """
```

#### 4. Constraint Satisfaction
```python
def solve_custom_timetable(payload: dict) -> List[dict]:
    """
    Main solver function.
    
    Process:
    1. Parse input payload
    2. Create MinimalData structure
    3. Check feasibility
    4. Pre-assign resources
    5. Create CP model
    6. Add all constraints
    7. Solve
    8. Extract and format solution
    """
```

### Constraint Model Variables

```python
# For each (section, subject, teacher, room, slot)
assignment[s, sub, t, r, slot] = Binary Variable (0 or 1)
  # 1 if this combination is assigned, 0 otherwise

# For each teacher and slot
teacher_available[t, slot] = Constraint
  # At most one section with this teacher at this slot

# For each room and slot
room_available[r, slot] = Constraint
  # At most one section in this room at this slot

# For each section and subject
subject_hours[sec, sub] = Constraint
  # Total slots for this subject matches required hours
```

---

## Data Flow

### Complete End-to-End Flow

```
FRONTEND (User Interaction)
│
├─1. User fills form (Generate.tsx)
│   ├─ Start/End time: "09:00" - "17:00"
│   ├─ Subjects: [{name, credits, is_lab}]
│   ├─ Rooms: [{block, start, end}]
│   ├─ Faculty: [{name, subjects}]
│   └─ Sections: ["CS-1A", "CS-1B", "CS-1C"]
│
├─2. Frontend Validation
│   ├─ Check all fields filled
│   ├─ No duplicate subjects
│   └─ Sections not empty
│
├─3. POST /api/generate/ with payload
│
BACKEND (Processing)
│
├─4. Pydantic Validation
│   ├─ Type checking
│   ├─ Format validation
│   └─ Range checks
│
├─5. Solver Execution (solver_logic.py)
│   ├─ Create time slots
│   ├─ Check feasibility
│   ├─ Create CP model
│   ├─ Add constraints
│   └─ Run solver
│
├─6. Database Save
│   ├─ INSERT config → timetable_configs
│   ├─ INSERT run metadata → timetable_runs
│   └─ BULK INSERT slots → timetable_slots (chunked)
│
├─7. Response Formatting
│   ├─ Extract solution
│   ├─ Get time slots array
│   └─ Return JSON
│
FRONTEND (Display)
│
└─8. Visualization
    ├─ Parse API response
    ├─ Convert to grid (dataMapper.ts)
    ├─ Display in TimetableGrid.tsx
    ├─ Enable interactions:
    │   ├─ Drag-drop edits
    │   ├─ Add/remove slots
    │   ├─ Validate in real-time
    │   └─ Export to Excel
    └─ Save interactions back to database
```

---

## Security Architecture

### Frontend Security

```
┌──────────────────────────────────┐
│   Browser Security Model         │
├──────────────────────────────────┤
│ ✓ Same-Origin Policy (CSRF)      │
│ ✓ Content Security Policy (CSP)  │
│ ✓ XSS Protection (React escaping)│
│ ✓ Input validation (Pydantic)    │
└──────────────────────────────────┘
```

### Backend Security

```
Infrastructure Layer
    ↓
┌──────────────────────────────────┐
│ 1. CORS Middleware               │
│    - Restrict origins to known   │
│    - Allow only specific methods │
│    - Prevent CSRF attacks        │
└──────────────────────────────────┘
    ↓
┌──────────────────────────────────┐
│ 2. Input Validation (Pydantic)   │
│    - Type checking               │
│    - Range validation            │
│    - Format checking             │
│    - SQL injection prevention    │
└──────────────────────────────────┘
    ↓
┌──────────────────────────────────┐
│ 3. Database Security             │
│    - Parametrized queries        │
│    - Supabase SSL/TLS            │
│    - Environment-based secrets   │
│    - Row-level security (RLS)    │
└──────────────────────────────────┘
    ↓
┌──────────────────────────────────┐
│ 4. Error Handling                │
│    - No sensitive data in errors │
│    - Generic error messages      │
│    - Detailed logging internally │
└──────────────────────────────────┘
```

### Secrets Management

```
Environment Variables (.env - NOT in git)
    ├─ SUPABASE_URL: Cloud database URL
    ├─ SUPABASE_KEY: API key
    └─ (Future) JWT_SECRET, DB_PASSWORD, etc.

Configuration (.env.dev for Django)
    ├─ DEBUG: Boolean
    ├─ SECRET_KEY: Django secret
    ├─ ALLOWED_HOSTS: List of domains
    └─ DATABASE_URL: Connection string
```

---

## Deployment Architecture

### Current (Development)

```
Developer Laptop
├─ Frontend Dev Server (Vite: localhost:5173)
├─ Backend Dev Server (FastAPI: localhost:8000)
└─ Database (Supabase Cloud)
```

### Recommended Production

```
┌─────────────────────────────────┐
│   User's Browser                │
│   - React SPA                   │
└──────────────┬──────────────────┘
               │ HTTPS
┌──────────────▼──────────────────┐
│   CDN (for static assets)       │
│   - HTML, JS, CSS, Images       │
└──────────────┬──────────────────┘
               │
┌──────────────▼──────────────────┐
│   Load Balancer / API Gateway   │
└──────────────┬──────────────────┘
               │
┌──────────────▼──────────────────┐
│   App Server (Auto-scaled)      │
│   - FastAPI instances           │
│   - Docker containers           │
│   - Multiple replicas           │
└──────────────┬──────────────────┘
               │ SQL over TLS
┌──────────────▼──────────────────┐
│   Supabase PostgreSQL           │
│   - Hot replicas                │
│   - Automated backups           │
│   - Connection pooling          │
└─────────────────────────────────┘
```

### Containerization (Docker)

```dockerfile
# Dockerfile (Backend)
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0"]
```

```dockerfile
# Dockerfile (Frontend)
FROM node:20-alpine as build
WORKDIR /app
COPY package.json .
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
```

---

## Performance Considerations

### Frontend Optimization

```typescript
// 1. Code Splitting
const Timetable = lazy(() => import('./pages/Timetable'));

// 2. Query Caching
const { data } = useQuery(['schedule', runId], fetchSchedule, {
  staleTime: 5 * 60 * 1000, // 5 minutes
});

// 3. Memoization
const memoizedGrid = useMemo(() => mapApiToGrid(data), [data]);

// 4. Virtual Scrolling (for large grids)
// Consider react-window for very large timetables

// 5. Lazy Image Loading
<img loading="lazy" src={imageUrl} />
```

### Backend Optimization

```python
# 1. Database Pagination
response = supabase.table("timetable_slots") \
    .select("*") \
    .eq("run_id", run_id) \
    .range(0, 999) \
    .execute()

# 2. Connection Pooling
# Supabase auto-manages pool of 25-100 connections

# 3. Caching (future enhancement)
# from functools import lru_cache
# @lru_cache(maxsize=128)
# def get_solver_slots(...):

# 4. Async Operations (future)
# Currently synchronous; can be async with async/await
```

### Solver Performance

```python
# Pre-solve pruning reduces search space
check_feasibility(data)  # Fail fast if impossible

# Intelligent pre-assignment
preassign_resources(data)  # Reduce variables

# Timeouts to prevent long runs
solver.Solve(strategy, max_seconds=30)
```

---

## Monitoring & Observability

### Logging Strategy

```python
import logging

logger = logging.getLogger(__name__)

logger.info(f"Generating schedule for {len(sections)} sections")
logger.warning(f"Feasibility check failed: {reason}")
logger.error(f"Database error: {exception}", exc_info=True)
```

### Metrics to Track

- **API Response Time**: Time to generate schedule
- **Solver Success Rate**: % of feasible configurations solved
- **Database Query Time**: Latency for reads/writes
- **Error Rate**: % of failed requests
- **User Engagement**: Active users, feature usage

### Future Observability

- Use APM tools (DataDog, New Relic, Sentry)
- Set up proper logging aggregation
- Monitor database performance
- Track user behavior analytics

---

## Scalability Roadmap

### Phase 1 (Current)
- ✅ Single backend instance
- ✅ Cloud database (Supabase)
- ✅ Basic CORS configuration

### Phase 2 (Near-term)
- Horizontal scaling with load balancer
- Async task queue for long-running solves
- Redis cache for frequent queries
- User authentication & authorization

### Phase 3 (Medium-term)
- Multi-tenancy for multiple institutions
- Real-time collaboration (WebSockets)
- Advanced reporting & analytics
- Mobile application

### Phase 4 (Long-term)
- Machine learning for schedule optimization
- AI-powered conflict resolution
- Predictive scheduling
- Global platform for educational institutions

---

## Technology Decisions & Trade-offs

| Decision | Chosen | Alternative | Why |
|----------|--------|-------------|-----|
| **Language** | Python + TypeScript | Java, Go, Node.js | Optimal for ML/scientific computing + web dev |
| **Framework** | FastAPI | Django, Flask | Modern, fast, auto-documentation |
| **Frontend** | React | Vue, Angular, Svelte | Large ecosystem, React Query for state mgmt |
| **Database** | Supabase | MongoDB, Firebase | SQL better for relational scheduling data |
| **Solver** | OR-Tools | PuLP, Pyomo, CPLEX | Industry standard, well-maintained, free |
| **Styling** | Tailwind | Bootstrap, Material | Utility-first, highly customizable |
| **Deployment** | Containerized | Serverless, bare metal | Balance between control and simplicity |

---

## Future Architecture Considerations

1. **Microservices**: Separate solver, database, and API services
2. **Event-Driven**: Use message queues (RabbitMQ, Kafka) for async processing
3. **GraphQL**: Replace REST API for complex querying
4. **Caching Layer**: Redis for frequently accessed schedules
5. **Real-time**: WebSockets for collaborative editing
6. **Multi-cloud**: Support AWS, GCP, Azure in addition to Supabase

---

**Last Updated**: March 2026
**Architecture Version**: 1.0
