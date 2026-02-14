import pytest
from django.db import IntegrityError
from core.planning.models import PlanningSession, PlanningSection, PlanningSubject
from core.academic.models import Program, Semester, AcademicYear, Subject, Section
from core.people.models import Faculty


@pytest.mark.django_db
class TestPlanningModels:

    @pytest.fixture
    def setup(self):
        prog = Program.objects.create(name="TestProg", code="TP")
        year = 2025
        ay = AcademicYear.objects.create(year=year, start_date=f"{year}-01-01", end_date=f"{year}-12-31")
        sem = Semester.objects.create(program=prog, academic_year=ay, number=4)
        fac = Faculty.objects.create(name="Dr Test", email="test@uni.edu")
        return prog, sem, fac

    def test_planning_session_creation(self, setup):
        prog, sem, _ = setup
        session = PlanningSession.objects.create(
            name="CSE 3rd Year 2025",
            program=prog,
            semester=sem,
            status="DRAFT"
        )
        assert str(session) == "CSE 3rd Year 2025"

    def test_planning_section_unique(self, setup):
        _, sem, _ = setup
        sec = Section.objects.create(semester=sem, name="X")
        session = PlanningSession.objects.create(name="Test", program=sem.program, semester=sem)

        PlanningSection.objects.create(planning_session=session, section=sec)

        with pytest.raises(IntegrityError):
            PlanningSection.objects.create(planning_session=session, section=sec)

    def test_planning_subject_unique(self, setup):
        _, sem, fac = setup
        sub = Subject.objects.create(code="CS999", name="TestSub", credits=3, hours_per_week=3)
        session = PlanningSession.objects.create(name="TestS", program=sem.program, semester=sem)

        PlanningSubject.objects.create(planning_session=session, subject=sub, assigned_faculty=fac)

        with pytest.raises(IntegrityError):
            PlanningSubject.objects.create(planning_session=session, subject=sub)