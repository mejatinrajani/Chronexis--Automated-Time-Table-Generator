# Timetable Generator - Project Overview

## Table of Contents
1. [Executive Summary](#executive-summary)
2. [Project Vision](#project-vision)
3. [What We Do](#what-we-do)
4. [How We Do It](#how-we-do-it)
5. [Reliability & Credibility](#reliability--credibility)
6. [Key Features](#key-features)
7. [Technology Stack](#technology-stack)

---

## Executive Summary

**Timetable Generator** is an intelligent scheduling application designed to automatically generate conflict-free, optimized timetables for educational institutions. It combines sophisticated constraint satisfaction algorithms with a modern, intuitive user interface to solve one of the most complex scheduling problems in academic management.

### At a Glance:
- **Purpose**: Automated academic timetable generation
- **Users**: Educational institutions, academic administrators, schedulers
- **Core Problem Solved**: Eliminates manual scheduling conflicts while optimizing resource utilization
- **License**: MIT License
- **Author**: Jatin Rajani (mejatinrajani.tech@gmail.com, +91 8791309542)

---

## Project Vision

The vision of Timetable Generator is to **empower educational institutions with intelligent automation** that:

1. **Eliminates Scheduling Complexity**: Automatically handles complex constraints that make manual scheduling error-prone and time-consuming
2. **Optimizes Resource Utilization**: Ensures classrooms, faculty, and learning spaces are used efficiently
3. **Enhances Educational Quality**: Allows educators to focus on curriculum design rather than scheduling logistics
4. **Provides Flexibility**: Supports various scheduling requirements across different educational systems
5. **Democratizes Scheduling**: Makes advanced constraint satisfaction algorithms accessible to institutions of all sizes

---

## What We Do

### The Core Problem
Academic scheduling is one of the most challenging combinatorial optimization problems:

- **Multiple Constraints**: Faculty availability, room capacities, subject duration requirements, student load balancing
- **Soft Constraints**: Minimizing free periods, avoiding fragmented schedules, balancing faculty workload
- **Resource Conflicts**: Preventing double-booking of rooms and faculty members
- **Manual Effort**: Traditionally requires weeks of manual work prone to human error

### The Solution
Our application uses **Google OR-Tools' Constraint Programming (CP) solver** combined with a modern full-stack interface:

1. **Input Phase**: Users define:
   - Working hours and time slots
   - Subjects and their requirements (duration, type - lecture/lab)
   - Faculty and their subject expertise
   - Rooms and their classifications
   - Student sections to schedule

2. **Processing Phase**: The solver:
   - Models all constraints mathematically
   - Searches for feasible solutions
   - Balances soft constraints for optimization
   - Returns a complete, conflict-free schedule

3. **Output Phase**: Users can:
   - View the generated schedule in multiple formats
   - Manually adjust and refine assignments
   - Export to Excel for institutional use
   - Track scheduling history

---

## How We Do It

### 1. **Intelligent Constraint Satisfaction**

#### Hard Constraints (Must be satisfied):
- **No Teacher Double-Booking**: A faculty member cannot be assigned to multiple sections simultaneously
- **No Room Conflicts**: A room cannot be used by multiple classes at the same time
- **Subject Duration Matching**: All required hours for each subject must be scheduled
- **Lab vs Theory Separation**: Lab sessions may require different room types

#### Soft Constraints (Optimized):
- **Load Balancing**: Faculty workload is distributed evenly
- **Minimal Free Periods**: Reduces gaps in student/teacher schedules
- **Quality Slots**: Avoids excessive fragmentation

### 2. **Architecture Overview**

The application is built as a **full-stack, two-tier system**:

```
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND (React + TypeScript)             │
│  - Interactive UI for input and schedule visualization       │
│  - Drag-and-drop interface for manual adjustments            │
│  - Real-time validation and conflict detection              │
│  - Excel export functionality                               │
└────────────────┬────────────────────────────────────────────┘
                 │  REST API (JSON)
┌────────────────▼────────────────────────────────────────────┐
│               BACKEND (FastAPI + Python)                    │
│  - RESTful API endpoints                                    │
│  - Constraint programming solver integration                │
│  - Database operations via Supabase                         │
│  - Time slot generation and validation                      │
└────────────────┬────────────────────────────────────────────┘
                 │  Database Operations
┌────────────────▼────────────────────────────────────────────┐
│           DATABASE (Supabase PostgreSQL)                    │
│  - User configurations                                      │
│  - Generated schedules and history                          │
│  - Run tracking and metadata                                │
└─────────────────────────────────────────────────────────────┘
```

### 3. **Data Flow**

```
User Input
    ↓
[Generate.tsx - Data Collection]
    ↓
REST API → /api/generate/
    ↓
[solver_logic.py - Solver]
    ├→ Create constraint model
    ├→ Define variables (slot assignments)
    ├→ Add constraints
    ├→ Run CP solver
    └→ Extract solution
    ↓
Supabase Database
    ├→ Save configuration
    ├→ Save run metadata
    └→ Store generated slots
    ↓
Response → Frontend
    ↓
[Timetable.tsx - Visualization]
    ├→ Map API data to grid
    ├→ Display interactive timetable
    └→ Allow manual adjustments
    ↓
Export to Excel / Save History
```

### 4. **Key Components & Their Responsibilities**

#### Backend Components:

| Component | File | Purpose |
|-----------|------|---------|
| **Main API** | `main.py` | FastAPI application, route definitions, CORS setup |
| **Solver Logic** | `solver_logic.py` | Constraint satisfaction algorithm, solution extraction |
| **Database Layer** | `database.py` | Supabase client initialization |
| **Data Models** | `main.py` (Pydantic) | Input/output schema validation |

#### Frontend Components:

| Component | File | Purpose |
|-----------|------|---------|
| **Input Interface** | `Generate.tsx` | Collect configuration (subjects, rooms, faculty) |
| **Excel Import** | `GenerateTimeTableUsingExcel.tsx` | Import faculty data from Excel files |
| **Visualization** | `Timetable.tsx` | Display, edit, and manage the generated schedule |
| **Data Mapping** | `dataMapper.ts` | Convert API response to UI-friendly format |
| **Excel Export** | `excelExport.ts` | Generate institutional-grade Excel files |
| **Validation** | `Validator.ts` | Check for conflicts and inconsistencies |

#### Django Backend (Extensible):

| Component | Purpose |
|-----------|---------|
| `core.academic` | Programs, semesters, sections, subjects |
| `core.infrastructure` | Room, building management |
| `core.people` | Students, faculty, staff |
| `core.planning` | Scheduling logic and planning |
| `core.times` | Time slot and calendar management |

---

## Reliability & Credibility

### What Makes This Solution Reliable?

#### 1. **Mathematically Sound**
- Uses **Google OR-Tools**, an industry-standard optimization library trusted by Fortune 500 companies
- Constraint Programming approach guarantees finding feasible solutions when they exist
- Validated through extensive test cases

#### 2. **Feasibility Checking**
Before attempting to solve, the system validates:
- Whether a solution is mathematically possible
- If all constraints can be satisfied
- Provides detailed error messages if constraints are infeasible

```python
# From solver_logic.py - Feasibility Check
def check_feasibility(data: MinimalData) -> Tuple[bool, str]:
    # Validates: slot availability, faculty capacity, room availability
    # Returns: (is_feasible, error_message)
```

#### 3. **Data Validation**
- **Frontend Validation**: Real-time checks using `Validator.ts`
  - Detects teacher clashes
  - Identifies room conflicts
  - Validates credit requirements
  - Categorizes issues as critical vs. warning

- **Backend Validation**: Pydantic models ensure data integrity
  - Type checking
  - Range validation
  - Schema compliance

#### 4. **Version Control & Testing**
- Multiple versions of solver maintained (`solver_logic.py`, `solver_logic_old_working.py`)
- Test suites in `solver_tests_different_cases/`
- Django test framework integration

#### 5. **Cloud Database Security**
- Uses **Supabase (PostgreSQL)** - enterprise-grade database
- Automatic backups and versioning
- Role-based access control
- Encrypted connections (SSL/TLS)

#### 6. **Error Handling & Logging**
- Try-catch blocks throughout codebase
- Detailed error messages for debugging
- Graceful degradation when services unavailable
- Console logging for monitoring

### Credibility Factors

1. **Open Source Foundation**: MIT Licensed, publicly auditable code
2. **Industry-Grade Tools**: Built on proven libraries (FastAPI, OR-Tools, React)
3. **Production Ready**: Database persistence, API rate limiting, CORS security
4. **Transparent Algorithms**: Well-commented code explaining constraint logic
5. **Academic Rigor**: Based on published scheduling optimization research

---

## Key Features

### 1. **Automatic Schedule Generation**
- Configure subjects, faculty expertise, rooms, and time windows
- Solver automatically generates conflict-free schedules
- Handles both theory and lab sessions

### 2. **Interactive Schedule Editor**
- Drag-and-drop interface for manual adjustments
- Real-time conflict detection with visual indicators
- Undo/redo functionality with history tracking
- Add/remove/modify individual slots

### 3. **Excel Integration**
- **Import**: Load faculty and subject data from Excel spreadsheets
- **Export**: Generate institutional-grade Excel files with formatting
- **Format**: Proper time zones, multiple sheets per section, color-coded headers

### 4. **Multiple Viewing Options**
- **Student View**: See their section's complete schedule
- **Teacher View**: See all classes they're assigned to
- **Room View**: See utilization of each classroom

### 5. **History & Versioning**
- Track all generated schedules
- Compare different scheduling runs
- Restore previous versions

### 6. **Validation & Quality Checks**
- Automatic detection of:
  - Faculty/room double-bookings
  - Incomplete subject requirements
  - Imbalanced workloads
- Color-coded severity indicators (Critical/Warning)

### 7. **Data Persistence**
- Save configurations for future reference
- Store complete scheduling history
- Track metadata (generation time, feasibility status)

---

## Technology Stack

### Frontend
| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Runtime** | Node.js/Bun | JavaScript runtime |
| **Framework** | React 18+ | UI component library |
| **Language** | TypeScript | Type-safe JavaScript |
| **Build Tool** | Vite | Fast module bundler |
| **Styling** | Tailwind CSS | Utility-first CSS framework |
| **UI Components** | Radix UI + shadcn/ui | Accessible component library |
| **State Management** | React Query | Server state management |
| **Routing** | React Router v6 | Client-side routing |
| **Notifications** | Sonner | Toast notifications |
| **Excel Generation** | ExcelJS | Client-side Excel manipulation |
| **Testing** | Vitest | Unit testing framework |
| **Linting** | ESLint | Code quality |

### Backend
| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Framework** | FastAPI | Modern Python web framework |
| **Server** | Uvicorn | ASGI web server |
| **Solver** | Google OR-Tools | Constraint optimization |
| **Database** | Supabase (PostgreSQL) | Cloud database |
| **ORM** | Supabase Python Client | Database abstraction |
| **Validation** | Pydantic | Data validation |
| **Environment** | python-dotenv | Configuration management |
| **Data Processing** | Pandas | Data analysis |
| **Webscraping/Structured Data** | - | Room for extension |

### Infrastructure
| Component | Technology |
|-----------|-----------|
| **Database** | Supabase PostgreSQL (Cloud) |
| **CORS** | Built-in FastAPI middleware |
| **Development** | Local Python venv |
| **Hosting** | Flexible (can deploy to Vercel, Heroku, Docker) |

### Optional/Extended Components
| Component | Status | Purpose |
|-----------|--------|---------|
| **Django Framework** | Partially Used | Academic models, extensibility |
| **Django Admin** | Available | Administrative interface |
| **Django Tests** | Implemented | Comprehensive test suite |

---

## Quality & Best Practices

### Code Quality
- ✅ Type hints throughout Python code
- ✅ TypeScript strict mode in frontend
- ✅ Component-based architecture
- ✅ Separation of concerns (utils, hooks, components)
- ✅ Comprehensive error handling

### Security
- ✅ CORS properly configured
- ✅ Environment variables for secrets
- ✅ SQL injection prevention (Supabase)
- ✅ Input validation (Pydantic)
- ✅ SSL/TLS for database connections

### Performance
- ✅ Lazy loading of components
- ✅ Pagination for large datasets (1000+ slots)
- ✅ Efficient constraint satisfaction algorithm
- ✅ React Query for caching
- ✅ CSS-in-JS optimizations with Tailwind

### Scalability
- ✅ Modular component structure
- ✅ Extensible database schema
- ✅ RESTful API design
- ✅ Cloud-based database with auto-scaling
- ✅ Stateless API (can run multiple instances)

---

## Success Metrics

This solution is successful when:

1. **Feasibility**: Generates valid, conflict-free schedules (100% success rate on feasible configurations)
2. **Speed**: Produces results within seconds for small-to-medium institutions (< 5 seconds)
3. **Quality**: Optimizes soft constraints (minimal free periods, balanced workloads)
4. **Usability**: Administrators with no technical background can use it effectively
5. **Reliability**: System uptime > 99%, data persistence without loss
6. **User Satisfaction**: Institutions find the schedules practical and implementable

---

## Use Cases

### Primary Users
- **Academic Administrators**: Responsible for course scheduling at universities/colleges
- **Schedule Coordinators**: Manage timetables for multiple departments/semesters
- **Department Heads**: Oversee faculty load distribution

### Typical Workflow
1. **Semester Planning Phase**: Define courses, faculty, rooms for upcoming semester
2. **Schedule Generation**: Run solver with constraints
3. **Review & Adjustment**: Manually tweak schedule with editor
4. **Approval**: Stakeholder review and final approval
5. **Publication**: Export and distribute to students/faculty
6. **History Retention**: Store for future reference and improvements

---

## Future Enhancements

Potential features for future versions:

- 🚀 **AI-Powered Suggestions**: ML model to suggest optimal adjustments
- 🚀 **Multi-Semester Planning**: Coordinate schedules across multiple terms
- 🚀 **Student Preference Integration**: Input student course preferences
- 🚀 **Conflict Resolution UI**: Interactive tools to resolve clashing constraints
- 🚀 **Mobile App**: Native mobile applications for viewing schedules
- 🚀 **Calendar Integration**: Sync with institutional calendar systems
- 🚀 **Reporting Dashboard**: Analytics on scheduling efficiency
- 🚀 **Internationalization**: Support for multiple languages

---

## Support & Contribution

For issues, questions, or contributions:
- **GitHub**: [Project Repository]
- **Email**: mejatinrajani.tech@gmail.com
- **Issues**: Report bugs and feature requests on GitHub Issues
- **Contributions**: See CONTRIBUTING.md for guidelines

---

## License

MIT License - See LICENSE.md for full details

Copyright © 2026 Jatin Rajani

This project is open source and available for both personal and commercial use.

---

**Last Updated**: March 2026
**Version**: 1.0
