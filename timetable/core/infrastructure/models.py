from django.db import models

class Room(models.Model):
    name = models.CharField(max_length=50, unique=True)
    capacity = models.PositiveIntegerField()
    is_lab = models.BooleanField(default=False)
    location = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

# Lab is just a specialized Room, but we can use Room with is_lab=True; if needed, extend later.