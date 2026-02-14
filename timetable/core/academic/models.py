from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

class Program(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=10, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

class AcademicYear(models.Model):
    year = models.IntegerField(
        validators=[MinValueValidator(1900), MaxValueValidator(2100)],
        unique=True
    )
    start_date = models.DateField()
    end_date = models.DateField()

    class Meta:
        ordering = ['-year']  # Most recent first

    def __str__(self):
        return str(self.year)

class Semester(models.Model):
    number = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)]
    )
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name='semesters')
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='semesters')

    class Meta:
        unique_together = ['program', 'academic_year', 'number']
        ordering = ['number']

    def __str__(self):
        return f"Semester {self.number} - {self.program.name}"

class Section(models.Model):
    name = models.CharField(max_length=5)  # e.g., A, B, AA
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='sections')
    student_count = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ['semester', 'name']
        ordering = ['name']

    def __str__(self):
        return f"{self.semester} - Section {self.name}"

class Subject(models.Model):
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=100)
    credits = models.PositiveSmallIntegerField()
    is_lab = models.BooleanField(default=False)
    hours_per_week = models.PositiveSmallIntegerField()  # Derived from credits, but explicit

    class Meta:
        ordering = ['code']

    def __str__(self):
        return f"{self.code} - {self.name}"

class SectionSubjectMap(models.Model):
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name='subject_maps')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='section_maps')
    required_hours = models.PositiveSmallIntegerField()  # Can override subject's hours_per_week

    class Meta:
        unique_together = ['section', 'subject']

    def __str__(self):
        return f"{self.section} - {self.subject}"