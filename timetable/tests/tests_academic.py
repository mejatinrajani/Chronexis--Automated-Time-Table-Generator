import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from core.academic.models import Program, AcademicYear, Semester, Section, Subject, SectionSubjectMap


@pytest.mark.django_db
class TestAcademicModels:

    def test_program_creation_and_str(self):
        program = Program.objects.create(
            name="B.Tech Computer Science",
            code="CSE",
            description="4 year undergraduate program"
        )
        assert str(program) == "B.Tech Computer Science"
        assert Program.objects.count() == 1

    def test_program_unique_code(self):
        Program.objects.create(name="First", code="CSE")
        with pytest.raises(IntegrityError):
            Program.objects.create(name="Second", code="CSE")

    def test_academic_year_creation(self):
        year = AcademicYear.objects.create(
            year=2025,
            start_date="2025-07-01",
            end_date="2026-06-30"
        )
        assert str(year) == "2025"
        assert AcademicYear.objects.latest('year') == year  # ordering test

    def test_semester_unique_together(self):
        prog = Program.objects.create(name="B.Tech", code="BT")
        year = AcademicYear.objects.create(year=2025, start_date="2025-01-01", end_date="2025-12-31")

        Semester.objects.create(program=prog, academic_year=year, number=3)

        with pytest.raises(IntegrityError):
            Semester.objects.create(program=prog, academic_year=year, number=3)

    def test_section_creation_and_unique(self):
        prog = Program.objects.create(name="Test Prog", code="TP")
        year = AcademicYear.objects.create(year=2025, start_date="2025-01-01", end_date="2025-12-31")
        sem = Semester.objects.create(program=prog, academic_year=year, number=5)
        
        sec1 = Section.objects.create(semester=sem, name="A", student_count=65)
        assert str(sec1).endswith("Section A")

        Section.objects.create(semester=sem, name="B")

        with pytest.raises(IntegrityError):
            Section.objects.create(semester=sem, name="A")

    def test_subject_creation(self):
        sub = Subject.objects.create(
            code="CS301",
            name="Data Structures",
            credits=4,
            hours_per_week=4,
            is_lab=False
        )
        assert str(sub).startswith("CS301")

    def test_section_subject_map_unique(self):
        # Setup
        prog = Program.objects.create(name="Test", code="TST")
        year = AcademicYear.objects.create(year=2025, start_date="2025-01-01", end_date="2025-12-31")
        sem = Semester.objects.create(program=prog, academic_year=year, number=3)
        sec = Section.objects.create(semester=sem, name="K")
        sub = Subject.objects.create(code="MAT101", name="Math", credits=3, hours_per_week=3)

        SectionSubjectMap.objects.create(section=sec, subject=sub, required_hours=3)

        with pytest.raises(IntegrityError):
            SectionSubjectMap.objects.create(section=sec, subject=sub, required_hours=4)