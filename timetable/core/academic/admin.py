from django.contrib import admin
from .models import Program, AcademicYear, Semester, Section, Subject, SectionSubjectMap

@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    list_display = ('name', 'code')

@admin.register(Semester)
class SemesterAdmin(admin.ModelAdmin):
    list_display = ('program', 'academic_year', 'number')

class SectionSubjectInline(admin.TabularInline):
    model = SectionSubjectMap
    extra = 1

@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ('name', 'semester', 'student_count')
    inlines = [SectionSubjectInline] # Lets you add subjects directly inside a Section

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'credits', 'is_lab')
    search_fields = ('name', 'code')

@admin.register(AcademicYear)
class AcademicYearAdmin(admin.ModelAdmin):
    list_display = ('year', 'start_date', 'end_date')
    ordering = ('-year',)