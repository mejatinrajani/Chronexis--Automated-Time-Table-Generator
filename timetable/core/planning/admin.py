from django.contrib import admin
from .models import PlanningSession, TimetableEntry

@admin.register(PlanningSession)
class PlanningSessionAdmin(admin.ModelAdmin):
    list_display = ('name', 'semester', 'status', 'created_at')

@admin.register(TimetableEntry)
class TimetableEntryAdmin(admin.ModelAdmin):
    list_display = ('section', 'day', 'start_time', 'subject', 'faculty', 'room')
    list_filter = ('planning_session', 'section', 'day')