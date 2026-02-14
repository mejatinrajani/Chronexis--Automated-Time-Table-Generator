from django.db import models

class Day(models.Model):
    name = models.CharField(max_length=10, unique=True)  # e.g., Monday
    is_working_day = models.BooleanField(default=True)

    class Meta:
        ordering = ['id']  # Assume ID 1-7 for Mon-Sun

    def __str__(self):
        return self.name

class TimeSlot(models.Model):
    day = models.ForeignKey(Day, on_delete=models.CASCADE, related_name='slots')
    start_time = models.TimeField()
    end_time = models.TimeField()
    index = models.PositiveSmallIntegerField()  # Order in day

    class Meta:
        unique_together = ['day', 'index']
        ordering = ['day', 'index']

    def __str__(self):
        return f"{self.day} {self.start_time}-{self.end_time}"

class Break(models.Model):
    day = models.ForeignKey(Day, on_delete=models.CASCADE, related_name='breaks')
    start_time = models.TimeField()
    end_time = models.TimeField()

    class Meta:
        ordering = ['day', 'start_time']

    def __str__(self):
        return f"Break on {self.day} {self.start_time}-{self.end_time}"