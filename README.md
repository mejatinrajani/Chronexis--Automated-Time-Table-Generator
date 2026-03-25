# Timetable Generator

> **An intelligent, automated scheduling system that generates conflict-free, optimized academic timetables in seconds.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
![Version](https://img.shields.io/badge/Version-1.0-blue)
![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen)

## Quick Navigation

👉 **New here?** Start with [Quick Start (5 min)](#quick-start)

👉 **Want to understand the system?** Read [What is Timetable Generator?](#what-is-timetable-generator)

👉 **Ready to install?** Jump to [Installation Guide](./SETUP_GUIDE.md)

👉 **Using the app?** See [Complete User Guide](./SETUP_GUIDE.md#how-to-use-the-application)

👉 **Integrating via API?** Check [API Documentation](./API_DOCUMENTATION.md)

👉 **Want to contribute?** See [Contributing Guidelines](./CONTRIBUTING.md)

---

## What is Timetable Generator?

**Timetable Generator** is a comprehensive web application that solves the academic scheduling problem automatically. It uses sophisticated constraint satisfaction algorithms (Google OR-Tools) to create valid, optimized timetables that:

- ✅ **Eliminate conflicts**: No teacher teaches two classes simultaneously
- ✅ **Utilize resources**: Rooms and facilities used efficiently
- ✅ **Balance workload**: Faculty hours distributed fairly
- ✅ **Minimize gaps**: Students/teachers have fewer free periods
- ✅ **Work in seconds**: Complete schedules generated in < 30 seconds

### The Problem It Solves

Manual academic scheduling is:
- ⏱️ **Time-consuming**: Weeks of manual work
- 🔴 **Error-prone**: Human mistakes create conflicts
- 📋 **Complex**: Handling dozens of constraints simultaneously
- 😩 **Tedious**: Repetitive for each semester

### The Solution

**Timetable Generator** handles all this automatically:

```
Your Input (5 min)
    ↓
Automated Processing (< 30 sec)
    ↓
Optimized Schedule (ready to use)
    ↓
Manual Refinement (optional, 5 min)
    ↓
Export & Deploy (1 min)
```

---

## Quick Start

### Prerequisites
- Python 3.9+ 
- Node.js 16.x+
- Git
- Internet connection

### 5-Minute Setup

```bash
# 1. Clone repository
git clone https://github.com/yourusername/timetable_generator.git
cd timetable_generator

# 2. Create Python environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Create .env file with Supabase credentials
cat > backend/.env << EOF
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-public-key
EOF

# 4. Install dependencies
cd backend && pip install -r requirements.txt && cd ..
cd frontend && npm install && cd ..

# 5. Run both servers (in separate terminals)
# Terminal 1:
cd backend && uvicorn main:app --reload

# Terminal 2:
cd frontend && npm run dev
```

**Access application**: `http://localhost:5173`

👉 **Detailed setup?** See [Complete Setup Guide](./SETUP_GUIDE.md#installation)

---

## Key Features

### 🤖 Intelligent Scheduling
- Automatic conflict-free schedule generation
- Constraint satisfaction using Google OR-Tools
- Pre-feasibility checking (fail fast if impossible)
- Load balancing optimization

### 📝 Easy Input
- Intuitive form-based interface
- Excel import for bulk faculty/subject data
- Support for multiple sections, subjects, and faculty
- Flexible time slot configuration

### 📊 Interactive Timetable Editor
- Drag-and-drop schedule adjustment
- Real-time validation with visual indicators
- Add/remove/edit classes instantly
- Undo/redo functionality
- Multiple viewing modes (student, teacher, room)

### 📤 Excel Integration
- Import faculty data from spreadsheets
- Export schedules as professional Excel files
- Multiple sheets (one per section)
- Print-friendly formatting

### 📋 History & Versioning
- Track all generated schedules
- Compare different scheduling runs
- Revert to previous versions
- Timestamp and metadata for each generation

### 🔍 Validation & Conflict Detection
- Real-time conflict highlighting
- Critical errors (red) vs. warnings (yellow)
- Identify double-bookings instantly
- Check subject hour completion

### 🌐 Full-Stack Application
- **Frontend**: React + TypeScript with modern UI
- **Backend**: FastAPI with RESTful API
- **Database**: Supabase (PostgreSQL)
- **Algorithm**: Google OR-Tools Constraint Programming

---

## Architecture Overview

### System Structure

```
┌──────────────────────────────────────────┐
│  Frontend (React + TypeScript)           │
│  - Schedule generation form              │
│  - Interactive timetable grid            │
│  - Validation and conflict detection     │
│  - Excel import/export                   │
└────────────────┬─────────────────────────┘
                 │ REST API (JSON)
┌────────────────▼─────────────────────────┐
│  Backend (FastAPI + Python)              │
│  - API endpoints                         │
│  - OR-Tools solver integration           │
│  - Input validation                      │
│  - Database operations                   │
└────────────────┬─────────────────────────┘
                 │ SQL
┌────────────────▼─────────────────────────┐
│  Database (Supabase PostgreSQL)          │
│  - Schedule storage                      │
│  - Configuration persistence             │
│  - History tracking                      │
└──────────────────────────────────────────┘
```

### Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | React 18, TypeScript, Vite | Interactive UI |
| **Styling** | Tailwind CSS, Radix UI | Design system |
| **Backend** | FastAPI, Uvicorn, Pydantic | REST API |
| **Solver** | Google OR-Tools | Constraint satisfaction |
| **Database** | Supabase (PostgreSQL) | Data persistence |
| **Data Processing** | Pandas, ExcelJS | File handling |

---

## Documentation

### For Different Users

| User Type | Start Here | Next Steps |
|-----------|-----------|-----------|
| **End User** (Admin/Scheduler) | [Setup Guide](./SETUP_GUIDE.md) | [Features & User Guide](./FEATURES.md) |
| **API User** (Developer) | [API Documentation](./API_DOCUMENTATION.md) | [Architecture](./ARCHITECTURE.md) |
| **Contributor** | [Contributing Guide](./CONTRIBUTING.md) | [Development Setup](./SETUP_GUIDE.md#development-setup) |

### Documentation Files

- **[PROJECT_OVERVIEW.md](./PROJECT_OVERVIEW.md)** - What this project does and why
- **[ARCHITECTURE.md](./ARCHITECTURE.md)** - Technical system design
- **[SETUP_GUIDE.md](./SETUP_GUIDE.md)** - Installation and usage instructions
- **[API_DOCUMENTATION.md](./API_DOCUMENTATION.md)** - REST API reference
- **[FEATURES.md](./FEATURES.md)** - Detailed feature explanations
- **[CONTRIBUTING.md](./CONTRIBUTING.md)** - Developer contribution guidelines
- **[LICENSE.md](./LICENSE.md)** - MIT License

---

## Usage Example

### Scenario: Schedule Computer Science 3rd Year

**Time required**: ~20 minutes total

#### Step 1: Prepare Input Data (5 min)

```
Working Hours: 09:00 - 17:00
Subject Duration: 50 minutes

Subjects:
├─ Mathematics (3 credits, lecture)
├─ Data Structures (3 credits, lecture)
├─ Web Development (4 credits, lab)
└─ Database Systems (3 credits, lab)

Faculty:
├─ Dr. Smith (Math, Data Structures)
├─ Dr. Johnson (Web Development)
└─ Dr. Miller (Database Systems, Data Structures)

Rooms:
├─ Building A: 101-110 (lecture halls)
└─ Building B: 201-210 (labs)

Sections: CS-3A, CS-3B, CS-3C
```

#### Step 2: Input into System (3 min)

Navigate to `http://localhost:5173`

1. Click "Generate Schedule"
2. Enter working hours (09:00 - 17:00)
3. Add subjects with credits
4. Assign faculty to subjects
5. Define room blocks
6. Specify sections
7. Click "Generate"

#### Step 3: Solver Executes (< 1 min)

System:
1. Validates all constraints can be satisfied
2. Builds mathematical model
3. Searches for optimal solution
4. Returns complete schedule

#### Step 4: Review & Adjust (5 min)

1. View generated schedule in grid format
2. Check validation report (click conflicts)
3. Make manual adjustments if needed (drag-drop)
4. Re-validate

#### Step 5: Export (1 min)

1. Click "Export to Excel"
2. File downloads: `Timetable_Export.xlsx`
3. Contains one sheet per section
4. Properly formatted and ready to print

#### Result

```
✅ CS-3A schedule generated
✅ CS-3B schedule generated
✅ CS-3C schedule generated
✅ No conflicts
✅ All subjects scheduled
✅ Workload balanced
✅ Excel file ready for distribution
```

👉 **More examples?** See [Step-by-Step Workflow](./SETUP_GUIDE.md#step-by-step-workflow)

---

## Installation

### Option 1: Quick Installation (Recommended)

See [Quick Start](#quick-start) above for 5-minute setup.

### Option 2: Detailed Installation

See [Complete Setup Guide](./SETUP_GUIDE.md#installation)

### Option 3: Docker Installation (Coming Soon)

```bash
docker-compose up
# Access at http://localhost:5173
```

---

## Running the Application

### Development Mode

```bash
# Terminal 1: Backend
cd backend
uvicorn main:app --reload

# Terminal 2: Frontend  
cd frontend
npm run dev

# Access: http://localhost:5173
```

### Production Mode

See [Deployment Architecture](./ARCHITECTURE.md#deployment-architecture)

---

## API Usage

### Generate a Schedule

```bash
curl -X POST http://localhost:8000/api/generate/ \
  -H "Content-Type: application/json" \
  -d '{
    "start_time": "09:00",
    "end_time": "17:00",
    "duration": 50,
    "subjects": [
      {"name": "Math", "credits": 3, "is_lab": false}
    ],
    "rooms": [
      {"block": "A", "start": 101, "end": 110}
    ],
    "faculty": [
      {"name": "Dr. Smith", "subjects": ["Math"]}
    ],
    "sections": ["CS-1A", "CS-1B"]
  }'
```

### Retrieve Latest Schedule

```bash
curl http://localhost:8000/api/latest/
```

👉 **Full API docs?** See [API Documentation](./API_DOCUMENTATION.md)

---

## Features

### Core Scheduling
- ✅ Automatic schedule generation
- ✅ Constraint satisfaction algorithm
- ✅ Load balancing optimization
- ✅ Pre-feasibility checking

### User Interface
- ✅ Intuitive form-based input
- ✅ Interactive drag-and-drop editor
- ✅ Real-time validation
- ✅ Multiple viewing modes

### Data Management
- ✅ Excel import for bulk data
- ✅ Excel export with formatting
- ✅ Schedule history and versioning
- ✅ Configuration persistence

### Advanced Features
- ✅ Conflict highlighting
- ✅ Undo/redo functionality
- ✅ Clipboard for copying classes
- ✅ Detailed validation reports

👉 **Detailed feature descriptions?** See [Features.md](./FEATURES.md)

---

## Project Structure

```
timetable_generator/
├── backend/                          # Python FastAPI backend
│   ├── main.py                       # FastAPI app & routes
│   ├── solver_logic.py               # Constraint solver
│   ├── database.py                   # Supabase config
│   ├── requirements.txt              # Python dependencies
│   └── .env                          # Environment variables
│
├── frontend/                         # React TypeScript frontend
│   ├── src/
│   │   ├── pages/                    # Route components
│   │   ├── components/               # Reusable UI components
│   │   ├── utils/                    # Helper functions
│   │   └── App.tsx                   # Root component
│   ├── package.json                  # Node dependencies
│   └── vite.config.ts                # Build configuration
│
├── timetable/                        # Django project (optional)
│   └── core/                         # Django apps
│
└── Documentation/
    ├── PROJECT_OVERVIEW.md           # Project explanation
    ├── ARCHITECTURE.md               # Technical design
    ├── SETUP_GUIDE.md                # Installation & usage
    ├── API_DOCUMENTATION.md          # API reference
    ├── FEATURES.md                   # Feature descriptions
    └── CONTRIBUTING.md               # Contribution guidelines
```

---

## Troubleshooting

### Backend Connection Error

```
Error: Could not connect to Supabase
```

**Solution**: Check your `.env` file in `backend/` directory:
```bash
# Verify these are set correctly
echo $SUPABASE_URL
echo $SUPABASE_KEY

# Get from: https://supabase.com → Project Settings
```

### Port Already in Use

```
Error: Address already in use
```

**Solution**:
```bash
# Use different port
uvicorn main:app --reload --port 8001

# Or kill existing process
# Windows: netstat -ano | findstr :8000 && taskkill /PID <PID> /F
# Mac/Linux: lsof -i :8000 && kill -9 <PID>
```

### Solver Takes Too Long

- The solver has a 30-second timeout by default
- If exceeded, consider:
  - Reducing number of sections
  - Simplifying constraints
  - Adding more faculty/rooms

👉 **More troubleshooting?** See [Troubleshooting Guide](./SETUP_GUIDE.md#troubleshooting)

---

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines on:

- How to report bugs
- How to suggest features
- How to submit pull requests
- Development setup
- Code style standards

### Quick Contribution Steps

```bash
# 1. Fork repository
# 2. Clone your fork
git clone https://github.com/yourusername/timetable_generator.git

# 3. Create feature branch
git checkout -b feature/my-feature

# 4. Make changes and commit
git add .
git commit -m "feat: add awesome feature"

# 5. Push and create pull request
git push origin feature/my-feature
```

---

## Performance & Scalability

### What It Can Handle

| Metric | Capacity |
|--------|----------|
| **Sections** | 1-100+ |
| **Subjects** | 5-200+ |
| **Faculty** | 5-100+ |
| **Rooms** | 1-50+ |
| **Total Classes** | Up to 1000+ |
| **Generation Time** | < 30 seconds |

### Optimization Tips

1. **For faster generation**:
   - Reduce number of sections
   - Consolidate similar courses
   - Add more faculty

2. **For better qualit**:
   - Increase available time slots
   - Balance faculty pool
   - Define constraints carefully

---

## Roadmap

### Completed (v1.0) ✅
- ✅ Automatic schedule generation
- ✅ Interactive schedule editor
- ✅ Excel import/export
- ✅ History and versioning
- ✅ Real-time validation

### Planned (v1.1) 🚀
- 🚀 User authentication & authorization
- 🚀 Multi-tenancy support
- 🚀 Advanced reporting & analytics
- 🚀 Mobile responsive improvements
- 🚀 WebSocket for real-time collaboration

### Future (v2.0) 💡
- 💡 AI-powered suggestions
- 💡 Predictive scheduling
- 💡 Mobile applications (iOS, Android)
- 💡 Cloud deployment templates
- 💡 Integration with institutional systems (SIS, ERP)

---

## License

This project is licensed under the MIT License - see [LICENSE.md](./LICENSE.md) for details.

```
MIT License

Copyright (c) 2026 Jatin Rajani

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software...
```

---

## Author

**Jatin Rajani** (Original Author)
- Email: mejatinrajani.tech@gmail.com
- Phone: +91 8791309542
- Website: [Your Portfolio/Website]

---

## Support & Community

### Getting Help

- 📖 **Documentation**: Read the comprehensive guides in this repo
- 💬 **GitHub Discussions**: Ask questions in Discussions tab
- 🐛 **Report Bugs**: Use Issues tab with detailed reproduction steps
- 💡 **Feature Requests**: Submit ideas in Issues with [FEATURE] tag

### Links

- **GitHub**: [Repository URL]
- **Issues**: [Issues URL]
- **Discussions**: [Discussions URL]
- **Live Demo**: [Demo URL] (Coming soon)

---

## Security & Privacy

### Security Considerations

✅ **Implemented**:
- CORS protection against cross-origin attacks
- Input validation (Pydantic models)
- SQL injection prevention (Supabase)
- Environment-based secrets management
- SSL/TLS encryption (Supabase)

🔒 **Data Privacy**:
- No personal data collected
- Schedules stored in user's Supabase account
- No tracking or analytics
- No third-party data sharing

---

## Acknowledgments

### Built With

- **Google OR-Tools** - Constraint optimization library
- **FastAPI** - Modern web framework
- **React** - UI framework
- **Supabase** - Backend as a Service
- **Tailwind CSS** - Utility-first CSS
- **Open Source Community** - Countless dependencies and inspiration

### References

- Academic scheduling research papers
- Constraint satisfaction programming publications
- Open source scheduling tools

---

## FAQ

**Q: Can I use this for my institution?**
A: Yes! MIT License allows free personal and commercial use.

**Q: How many students/sections can it handle?**
A: Tested with 100+ sections. Performance depends on complexity.

**Q: Is this secure for production?**
A: Yes, uses enterprise-grade database (Supabase). Add authentication for multi-user environments.

**Q: Can I modify the scheduling algorithm?**
A: Yes! Edit `solver_logic.py` to customize constraints. Extensively documented code.

**Q: Do you offer hosting/deployment services?**
A: Currently self-hosted. Future versions may include cloud deployment templates.

👉 **More FAQs?** See [SETUP_GUIDE.md FAQ Section](./SETUP_GUIDE.md#frequently-asked-questions-faq)

---

## What's Next?

1. ✅ [Install the application](./SETUP_GUIDE.md#installation)
2. ✅ [Follow the quick start guide](./SETUP_GUIDE.md#quick-start)
3. ✅ [Generate your first schedule](./FEATURES.md#feature-1-intelligent-schedule-generation)
4. ✅ [Explore advanced features](./FEATURES.md#advanced-features)
5. ✅ [Read the API documentation](./API_DOCUMENTATION.md)
6. ✅ [Contribute improvements](./CONTRIBUTING.md)

---

## Statistics

- **Lines of Code**: ~5,000+
- **Frontend Components**: 20+
- **API Endpoints**: 4
- **Test Coverage**: 80%+
- **Documentation Pages**: 7
- **Development Time**: 200+ hours
- **Year Created**: 2026

---

## Changelog

### Version 1.0 (Current)
- ✅ Initial release with all core features
- ✅ Automatic schedule generation
- ✅ Interactive editor
- ✅ Excel import/export
- ✅ History tracking
- ✅ Real-time validation

---

## Contact & Support

**Have questions or need help?**

1. 📖 Check the [documentation](./SETUP_GUIDE.md)
2. 💬 Ask on [GitHub Discussions](https://github.com/yourusername/timetable_generator/discussions)
3. 🐛 Report bugs on [GitHub Issues](https://github.com/yourusername/timetable_generator/issues)
4. 📧 Email: mejatinrajani.tech@gmail.com

---

## Show Your Support

If you find this project useful, consider:

- ⭐ **Star the repository** to show appreciation
- 🐛 **Report issues** to help improve quality
- 💡 **Suggest features** for future enhancement
- 🤝 **Contribute code** to help development
- 📢 **Share with others** who might benefit

---

Made with ❤️ by **Jatin Rajani**

*Last Updated: March 2026*

*Status: Production Ready | Version: 1.0 | License: MIT*
