# Contributing to Timetable Generator

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing to the Timetable Generator project.

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [Development Setup](#development-setup)
4. [Making Changes](#making-changes)
5. [Submitting Changes](#submitting-changes)
6. [Code Style Guidelines](#code-style-guidelines)
7. [Commit Message Guidelines](#commit-message-guidelines)
8. [Pull Request Process](#pull-request-process)
9. [Reporting Bugs](#reporting-bugs)
10. [Suggesting Enhancements](#suggesting-enhancements)
11. [Development Workflow](#development-workflow)

---

## Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inspiring community for all.

### Our Standards

Examples of behavior that creates a positive environment:
- 🤝 Using welcoming and inclusive language
- 📚 Being respectful of differing opinions
- ✅ Accepting constructive criticism
- 🎯 Focusing on what is best for the community
- 💪 Showing empathy towards other community members

Examples of unacceptable behavior:
- 🚫 Harassment or intimidation
- 🚫 Discriminatory jokes or language
- 🚫 Personal attacks
- 🚫 Unwelcome sexual attention
- 🚫 Publishing private information without consent

### Enforcement

Instances of abusive, harassing, or otherwise unacceptable behavior may be reported by contacting the project maintainer at mejatinrajani.tech@gmail.com.

---

## Getting Started

### Prerequisites

Before you begin, ensure you have:
- Git installed ([download](https://git-scm.com/))
- GitHub account ([sign up](https://github.com/signup))
- Basic understanding of the project
- Familiarity with Git workflow (fork, branch, pull request)

### Steps to Get Started

1. **Read the documentation**
   - Read [PROJECT_OVERVIEW.md](./PROJECT_OVERVIEW.md) to understand the project
   - Read [ARCHITECTURE.md](./ARCHITECTURE.md) to understand technical design
   - Read [README.md](./README.md) for quick overview

2. **Fork the repository**
   ```bash
   # Go to GitHub
   # Click "Fork" button
   # You now have your own copy
   ```

3. **Clone your fork**
   ```bash
   git clone https://github.com/yourusername/timetable_generator.git
   cd timetable_generator
   ```

4. **Add upstream remote**
   ```bash
   git remote add upstream https://github.com/original-owner/timetable_generator.git
   git remote -v  # Verify both origin and upstream
   ```

5. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

---

## Development Setup

### Backend Setup

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

# Install dependencies (with dev tools)
cd backend
pip install -r requirements.txt
pip install pytest pytest-cov black flake8 mypy

# Verify installation
python -c "import fastapi; print('FastAPI OK')"
python -c "import ortools; print('OR-Tools OK')"
```

### Frontend Setup

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Install dev dependencies
npm install --save-dev @testing-library/react @testing-library/jest-dom vitest

# Verify installation
npm list react
npm list vite
```

### Database Setup

```bash
# Create .env file in backend/
cat > backend/.env << EOF
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-public-key
DEBUG=True
EOF
```

### Verify Setup

```bash
# Test backend
cd backend
python -m pytest
# Should run tests successfully

# Test frontend
cd ../frontend
npm run test
# Should run tests successfully

# Test startup
# Terminal 1:
cd backend
uvicorn main:app --reload
# Should show "Uvicorn running on http://127.0.0.1:8000"

# Terminal 2:
cd frontend
npm run dev
# Should show "Local: http://localhost:5173"
```

---

## Making Changes

### Working on a Feature

```bash
# 1. Update your local repository
git fetch upstream
git rebase upstream/main

# 2. Create feature branch
git checkout -b feature/descriptive-name
# Examples:
# feature/add-email-notifications
# feature/improve-solver-speed
# feature/fix-room-conflict-detection

# 3. Make your changes
# Edit files in your editor
# Keep changes focused (one feature per branch)

# 4. Test your changes
cd backend && pytest  # Python tests
cd ../frontend && npm run test  # Frontend tests
npm run lint  # Lint frontend
npm run type-check  # TypeScript check

# 5. Commit with meaningful message
git add .
git commit -m "feat: add new feature description"
# See commit guidelines below

# 6. Push to your fork
git push origin feature/descriptive-name

# 7. Create Pull Request on GitHub
```

### File Organization

#### Backend Changes

- **Algorithm changes**: `backend/solver_logic.py`
- **API changes**: `backend/main.py`
- **Database changes**: `backend/database.py`, then migrations
- **Tests**: `backend/test_*.py`

#### Frontend Changes

- **Page components**: `frontend/src/pages/`
- **UI components**: `frontend/src/components/`
- **Utilities**: `frontend/src/utils/`
- **Styles**: `frontend/src/*.css` or component-specific CSS
- **Tests**: `frontend/src/**/*.test.ts`

#### Documentation Changes

- **Project info**: `PROJECT_OVERVIEW.md`
- **Technical design**: `ARCHITECTURE.md`
- **User guide**: `SETUP_GUIDE.md`
- **API reference**: `API_DOCUMENTATION.md`
- **Features**: `FEATURES.md`

### Branch Naming Convention

```
feature/      - New feature
  feature/add-user-authentication

fix/          - Bug fix
  fix/resolve-room-conflict-detection

docs/         - Documentation improvement
  docs/add-api-examples

refactor/     - Code refactoring
  refactor/optimize-solver-performance

test/         - Test improvements
  test/add-integration-tests

chore/        - Maintenance tasks
  chore/update-dependencies
```

### Keep Your Branch Updated

```bash
# Before working or before submitting PR:
git fetch upstream
git rebase upstream/main

# If conflicts occur:
# 1. Resolve conflicts in your editor
# 2. Mark files as resolved
git add resolved-file.ts
# 3. Continue rebase
git rebase --continue
```

---

## Code Style Guidelines

### Python Code Style

We follow **PEP 8** with some customizations:

```python
# 1. Line Length: Max 100 characters
# Too long:
teacher_schedule[day][time][teacher] = [section for section in sections if should_assign(section, teacher)]
# Better:
available_assignments = [
    section for section in sections
    if should_assign(section, teacher)
]
teacher_schedule[day][time][teacher] = available_assignments

# 2. Type Hints (required)
def generate_schedule(
    payload: GeneratePayload,
    timeout: int = 30
) -> List[Dict[str, Any]]:
    """Generate timetable schedule."""
    pass

# 3. Docstrings (Google style)
def check_feasibility(data: MinimalData) -> Tuple[bool, str]:
    """
    Check if schedule generation is mathematically possible.
    
    Args:
        data: MinimalData containing all constraints
        
    Returns:
        Tuple of (is_feasible: bool, error_message: str)
        
    Raises:
        ValueError: If data is invalid
    """
    pass

# 4. Variable Naming
# Good:
teacher_count = 10
is_lab_subject = True
valid_time_slots = []

# Avoid:
tc = 10
is_lab = True  
slots = []

# 5. Functions: Small and focused
# Good: One responsibility
def validate_subject_hours(subjects: List[Subject]) -> List[str]:
    """Validate that all subjects have positive hours."""
    errors = []
    for subject in subjects:
        if subject.hours <= 0:
            errors.append(f"{subject.name} has invalid hours")
    return errors

# 6. Comments: Explain WHY, not WHAT
# Good comment - explains why:
# OR-Tools requires integer variables for slot assignments
schedule_vars = [model.NewIntVar(...) for _ in range(num_slots)]

# Bad comment - just repeats code:
# Create a list of integer variables
schedule_vars = [model.NewIntVar(...) for _ in range(num_slots)]
```

**Format code automatically:**
```bash
cd backend
black .  # Auto-format all Python files

# Lint check
flake8 .

# Type checking
mypy solver_logic.py
```

### TypeScript/React Code Style

We follow **TypeScript strict mode**:

```typescript
// 1. Type annotations (always)
// Good:
const sections: string[] = ["CS-1A", "CS-1B"];
const generateSchedule = (payload: GeneratePayload): Promise<Schedule> => {
  return fetch('/api/generate/', { body: JSON.stringify(payload) });
};

// Avoid:
const sections = ["CS-1A", "CS-1B"];
const generateSchedule = (payload) => { ... };

// 2. React Components: Use functional components with hooks
// Good:
const ScheduleGrid: React.FC<ScheduleGridProps> = ({ data, onUpdate }) => {
  const [gridData, setGridData] = useState<GridData>(data);
  
  const handleDrop = useCallback((section: string, time: string) => {
    // Handle drop logic
  }, []);
  
  return (
    <div className="grid-container">
      {/* JSX */}
    </div>
  );
};

// 3. File naming: PascalCase for components, camelCase for utilities
// Components:
- components/TimetableGrid.tsx
- components/DraggableSlot.tsx

// Utilities:
- utils/dataMapper.ts
- utils/excelExport.ts

// 4. Props interface naming
interface ScheduleGridProps {
  data: GridData;
  onUpdate: (newData: GridData) => void;
  isLoading?: boolean;
}

// 5. Component structure
const Component: React.FC<Props> = ({ prop1, prop2 }) => {
  // 1. State declarations
  const [state, setState] = useState(initialState);
  const [loading, setLoading] = useState(false);
  
  // 2. Hooks
  useEffect(() => {
    // Side effects
  }, [dependencies]);
  
  // 3. Event handlers
  const handleClick = () => {};
  const handleSubmit = (e: React.FormEvent) => {};
  
  // 4. Render
  return (
    <div>
      {/* JSX */}
    </div>
  );
};
```

**Format code automatically:**
```bash
cd frontend
npm run lint -- --fix  # Auto-fix ESLint issues

# Format with Prettier (if configured):
npx prettier --write src/
```

---

## Commit Message Guidelines

### Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- **feat**: A new feature
- **fix**: A bug fix
- **docs**: Documentation only
- **style**: Changes that don't affect code meaning (formatting, missing semicolons, etc.)
- **refactor**: Code change that neither fixes a bug nor adds a feature
- **perf**: Code change that improves performance
- **test**: Adding or updating tests
- **chore**: Changes to build process, dependencies, or tooling

### Examples

```bash
# Feature
git commit -m "feat(solver): add constraint for lab room types"

# Bug fix
git commit -m "fix(validation): resolve teacher double-booking detection"

# Documentation
git commit -m "docs(readme): improve setup instructions"

# Refactoring
git commit -m "refactor(api): simplify schedule serialization"

# With body
git commit -m "feat(excel): add support for conditional formatting

- Add color coding for lunch breaks
- Support merged cells for multi-hour classes
- Improve column width calculation

Closes #42"
```

### Commit Message Best Practices

1. **Use imperative mood** ("add" not "added" or "adds")
2. **Don't capitalize** the first letter
3. **Limit subject line** to 50 characters
4. **Separate subject from body** with blank line
5. **Wrap body** at 72 characters
6. **Reference issues** in footer: `Closes #123`, `Fixes #456`

---

## Pull Request Process

### Before Creating PR

- [ ] Code follows project style guidelines
- [ ] All tests pass (`pytest` in backend, `npm test` in frontend)
- [ ] No console warnings or errors
- [ ] Updated relevant documentation
- [ ] Commit messages follow guidelines
- [ ] Branch is up to date with main (`git rebase upstream/main`)

### Creating PR

1. **Push your branch to your fork**
   ```bash
   git push origin feature/your-feature
   ```

2. **Create Pull Request on GitHub**
   - Go to original repository
   - Click "New Pull Request"
   - Select `main` as base, your branch as compare
   - Fill in PR description (see template below)

3. **PR Description Template**
   ```markdown
   ## Description
   Briefly describe what this PR does.
   
   ## Type of Change
   - [ ] Bug fix
   - [ ] New feature
   - [ ] Breaking change
   - [ ] Documentation update
   
   ## Related Issues
   Closes #issue-number
   
   ## Testing
   Describe how changes were tested:
   - [ ] Tested locally
   - [ ] Added/updated tests
   - [ ] Manual testing steps: ...
   
   ## Screenshots (if applicable)
   [Add screenshots of UI changes]
   
   ## Checklist
   - [ ] My code follows style guidelines
   - [ ] I have tested this change
   - [ ] Documentation is updated
   - [ ] No console errors
   - [ ] Tests pass
   ```

4. **Respond to Feedback**
   - Review comments from maintainers
   - Make requested changes
   - Push updates to same branch (they auto-update PR)
   - Re-request review after changes

5. **Getting Merged**
   - Wait for at least one approval
   - All checks must pass
   - Maintainer will merge when ready

### After Merge

```bash
# Update your local copy
git checkout main
git pull upstream main

# Delete your feature branch locally
git branch -d feature/your-feature

# Delete from remote
git push origin --delete feature/your-feature
```

---

## Testing

### Running Tests

```bash
# Backend tests
cd backend
pytest              # Run all tests
pytest -v           # Verbose output
pytest test_solver.py  # Run specific file
pytest -k "test_feasibility"  # Run tests matching pattern
pytest --cov        # Coverage report

# Frontend tests
cd frontend
npm run test        # Run all tests
npm run test:watch  # Watch mode (re-run on changes)
npm run test -- src/pages/Generate.test.tsx  # Specific file
```

### Writing Tests

**Backend (pytest)**
```python
import pytest
from solver_logic import check_feasibility, MinimalData

class TestSolverFeasibility:
    """Tests for feasibility checking."""
    
    def test_feasible_configuration(self):
        """Should return True for valid configuration."""
        data = MinimalData(
            sections=["CS-1A"],
            subjects=["Math"],
            slots=[...],
            faculty=["Dr. Smith"],
            rooms=["101"],
            room_types={"101": "lecture"},
            subject_types={"Math": "lecture"},
            subject_durations={"Math": 1},
            competencies={"Math": ["Dr. Smith"]},
            unavailability={},
            hours={"CS-1A": {"Math": 1}},
            scheduling_style="weekly"
        )
        
        is_feasible, message = check_feasibility(data)
        assert is_feasible is True
        assert message == ""
    
    def test_infeasible_no_faculty(self):
        """Should return False if no faculty teaches subject."""
        data = MinimalData(
            # ... missing Dr. Smith for Math
        )
        
        is_feasible, message = check_feasibility(data)
        assert is_feasible is False
        assert "no teachers" in message.lower()
```

**Frontend (vitest/React Testing Library)**
```typescript
import { render, screen, fireEvent } from '@testing-library/react';
import { Generate } from './Generate';

describe('Generate', () => {
  it('should render form with all fields', () => {
    render(<Generate />);
    
    expect(screen.getByLabelText(/start time/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/subjects/i)).toBeInTheDocument();
  });
  
  it('should submit form with valid data', async () => {
    render(<Generate />);
    
    const startInput = screen.getByLabelText(/start time/i);
    fireEvent.change(startInput, { target: { value: '09:00' } });
    
    const submitButton = screen.getByRole('button', { name: /generate/i });
    fireEvent.click(submitButton);
    
    // expect fetch to be called
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/generate/'),
      expect.any(Object)
    );
  });
});
```

---

## Reporting Bugs

### Bug Report Template

```markdown
**Describe the bug**
A clear description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Go to '...'
2. Click on '....'
3. See error

**Expected behavior**
What you expected to happen.

**Actual behavior**
What actually happened.

**Screenshots**
If applicable, add screenshots.

**Environment**
- OS: [Windows 10, macOS, Ubuntu]
- Python/Node version
- Browser [Chrome, Firefox]

**Error Messages**
Include any error messages from console or logs.

**Additional context**
Any additional information.
```

### Creating Bug Report

1. Go to [Issues](https://github.com/yourusername/timetable_generator/issues)
2. Click "New Issue"
3. Click "Bug report"
4. Fill in template
5. Click "Submit new issue"

---

## Suggesting Enhancements

### Feature Request Template

```markdown
**Is your feature request related to a problem?**
Describe the problem. Ex. I'm always frustrated when [...]

**Describe the solution you'd like**
Clear and concise description of what you want to happen.

**Describe alternatives you've considered**
Any alternative solutions or features you've considered.

**Additional context**
Any other context or screenshots about the request.

**Estimate of effort**
- [ ] Small (1-4 hours)
- [ ] Medium (1-2 days)
- [ ] Large (1+ week)
```

### Creating Feature Request

1. Go to [Issues](https://github.com/yourusername/timetable_generator/issues)
2. Click "New Issue"
3. Click "Feature request"
4. Fill in template
5. Click "Submit new issue"

---

## Development Workflow Example

### Complete Workflow from Start to Merge

```bash
# 1. Setup (one time)
git clone https://github.com/yourusername/timetable_generator.git
cd timetable_generator
git remote add upstream https://github.com/original/timetable_generator.git

# 2. Check what needs doing
# Go to GitHub Issues
# Find issue to work on
# Comment: "I can work on this"

# 3. Update and create branch
git fetch upstream
git checkout upstream/main
git checkout -b fix/issue-description

# 4. Install and verify
python -m venv venv
source venv/bin/activate
cd backend && pip install -r requirements.txt
cd ../frontend && npm install
# Start both servers to verify setup works

# 5. Make changes
# Edit files in your editor
# Test changes locally

# 6. Commit changes
git add .
git commit -m "fix(solver): correct room assignment logic"

# 7. Tests and formatting
cd backend
pytest  # Make sure tests pass
black .  # Format code
flake8 .  # Check for issues
mypy solver_logic.py  # Type check

cd ../frontend
npm test -- --coverage  # Run tests
npm run lint -- --fix  # Format and lint

# 8. Update main if needed
git fetch upstream
git rebase upstream/main
# Resolve any conflicts

# 9. Push to fork
git push origin fix/issue-description

# 10. Create PR on GitHub
# Go to GitHub
# Click "Compare & pull request"
# Fill in template
# Submit

# 11. Respond to reviews
# Read feedback
# Make changes
# Co mmit and push (same branch)

# 12. After merge
git checkout main
git pull upstream main
git branch -d fix/issue-description
git push origin --delete fix/issue-description
```

---

## Resources

### Documentation
- [Project Overview](./PROJECT_OVERVIEW.md)
- [Architecture](./ARCHITECTURE.md)
-[Setup Guide](./SETUP_GUIDE.md)
- [API Documentation](./API_DOCUMENTATION.md)

### External Resources
- [Git Documentation](https://git-scm.com/doc)
- [Python PEP 8 Style Guide](https://pep8.org/)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)
- [React Documentation](https://react.dev/)
- [FastAPI Guide](https://fastapi.tiangolo.com/)

### Tools
- Code Editor: [VS Code](https://code.visualstudio.com/) (recommended)
- Version Control: [Git](https://git-scm.com/)
- Communication: [GitHub Discussions](https://github.com/features/discussions)

---

## Questions?

Don't hesitate to ask! You can:

- 📧 Email: mejatinrajani.tech@gmail.com
- 💬 [GitHub Discussions](https://github.com/yourusername/timetable_generator/discussions)
- 🐛 [GitHub Issues](https://github.com/yourusername/timetable_generator/issues)

---

## Thank You!

Your contributions make this project better! Even small fixes, documentation improvements, or bug reports are valuable. We appreciate your effort and look forward to working with you!

---

**Last Updated**: March 2026
**Version**: 1.0
