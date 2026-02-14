from django.db import models

class Faculty(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    department = models.CharField(max_length=50)
    max_load_per_week = models.PositiveSmallIntegerField(default=20)  # Hours

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

class FacultySubject(models.Model):
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE, related_name='subjects')
    subject = models.ForeignKey('academic.Subject', on_delete=models.CASCADE, related_name='faculties')
    preference = models.PositiveSmallIntegerField(default=1)  # 1-5 scale

    class Meta:
        unique_together = ['faculty', 'subject']

    def __str__(self):
        return f"{self.faculty} - {self.subject}"

class FacultyAvailability(models.Model):
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE, related_name='availabilities')
    day_of_week = models.PositiveSmallIntegerField(choices=[(i, day) for i, day in enumerate(['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'], 1)])
    start_time = models.TimeField()
    end_time = models.TimeField()

    class Meta:
        ordering = ['day_of_week', 'start_time']

    def __str__(self):
        return f"{self.faculty} available on day {self.day_of_week}"