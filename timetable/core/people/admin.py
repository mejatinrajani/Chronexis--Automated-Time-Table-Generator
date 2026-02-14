from django.contrib import admin
from .models import Faculty, FacultySubject

class FacultySubjectInline(admin.TabularInline):
    model = FacultySubject
    extra = 1

@admin.register(Faculty)
class FacultyAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'department', 'max_load_per_week')
    inlines = [FacultySubjectInline] # Lets you add qualified subjects inside the Faculty page