from django.contrib import admin
from .models import Day, TimeSlot, Break

class TimeSlotInline(admin.TabularInline):
    model = TimeSlot
    extra = 1

@admin.register(Day)
class DayAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_working_day')
    inlines = [TimeSlotInline] # Add slots (9:00, 10:00) directly inside the Day