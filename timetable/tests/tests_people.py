import pytest
from django.db import IntegrityError
from core.people.models import Faculty, FacultySubject, FacultyAvailability
from core.academic.models import Subject  # needed for relation


@pytest.mark.django_db
class TestPeopleModels:

    @pytest.fixture
    def subject(self):
        return Subject.objects.create(code="CS101", name="Intro", credits=3, hours_per_week=3)

    def test_faculty_creation(self):
        fac = Faculty.objects.create(
            name="Dr. Rajesh Kumar",
            email="rajesh@college.edu",
            department="CSE",
            max_load_per_week=18
        )
        assert str(fac) == "Dr. Rajesh Kumar"

    def test_faculty_unique_email(self):
        Faculty.objects.create(name="A", email="same@college.edu")
        with pytest.raises(IntegrityError):
            Faculty.objects.create(name="B", email="same@college.edu")

    def test_faculty_subject_relation(self, subject):
        fac = Faculty.objects.create(name="Prof X", email="x@college.edu")
        FacultySubject.objects.create(faculty=fac, subject=subject, preference=5)

        with pytest.raises(IntegrityError):
            FacultySubject.objects.create(faculty=fac, subject=subject, preference=3)

    def test_faculty_availability_creation(self):
        fac = Faculty.objects.create(name="Dr Y", email="y@college.edu")
        avail = FacultyAvailability.objects.create(
            faculty=fac,
            day_of_week=1,  # Monday
            start_time="09:00:00",
            end_time="17:00:00"
        )
        assert "Monday" in str(avail) or "day 1" in str(avail).lower()