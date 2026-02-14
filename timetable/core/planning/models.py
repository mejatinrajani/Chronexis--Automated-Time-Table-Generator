from django.db import models
from core.academic.models import Section, Subject
from core.people.models import Faculty
from core.infrastructure.models import Room 
from core.times.models import Day

class PlanningSession(models.Model):
    name = models.CharField(max_length=100)
    program = models.ForeignKey('academic.Program', on_delete=models.CASCADE)
    semester = models.ForeignKey('academic.Semester', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=[('DRAFT', 'Draft'), ('GENERATED', 'Generated'), ('VALIDATED', 'Validated')])

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name

class PlanningSection(models.Model):
    planning_session = models.ForeignKey(PlanningSession, on_delete=models.CASCADE, related_name='sections')
    section = models.ForeignKey('academic.Section', on_delete=models.CASCADE)

    class Meta:
        unique_together = ['planning_session', 'section']

class PlanningSubject(models.Model):
    planning_session = models.ForeignKey(PlanningSession, on_delete=models.CASCADE, related_name='subjects')
    subject = models.ForeignKey('academic.Subject', on_delete=models.CASCADE)
    assigned_faculty = models.ForeignKey('people.Faculty', on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        unique_together = ['planning_session', 'subject']




# --- Paste this Class at the bottom ---
class TimetableEntry(models.Model):
    """
    Stores the final generated schedule (Output of the Solver).
    """
    planning_session = models.ForeignKey(PlanningSession, on_delete=models.CASCADE, related_name='timetable_entries')
    section = models.ForeignKey(Section, on_delete=models.CASCADE)
    
    # Time details
    day = models.ForeignKey(Day, on_delete=models.CASCADE)
    start_time = models.TimeField()
    end_time = models.TimeField()
    
    # Assignment details (Can be null if it's a break or free slot)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, null=True, blank=True)
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE, null=True, blank=True)
    room = models.ForeignKey(Room, on_delete=models.CASCADE, null=True, blank=True)
    
    class Meta:
        ordering = ['day', 'start_time']
        verbose_name_plural = "Timetable Entries"

    def __str__(self):
        return f"{self.section} - {self.day} {self.start_time}"