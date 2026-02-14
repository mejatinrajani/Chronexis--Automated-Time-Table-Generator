from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db import transaction
from .models import PlanningSession, TimetableEntry
from core.academic.models import Section, Subject
from core.people.models import Faculty
from core.infrastructure.models import Room
from core.times.models import Day

# Import the logic we just created
from .solver.adapter import build_data_for_session
from .solver.solver_prototype import solve_minimal_timetable

def generate_timetable(request, session_id):
    """
    Triggers the constraint solver for a specific planning session.
    """
    session = get_object_or_404(PlanningSession, pk=session_id)

    if request.method == "POST":
        try:
            # 1. PREPARE DATA (Adapter)
            print(f"Fetching data for Session: {session.name}...")
            solver_input = build_data_for_session(session_id)
            
            # Check if we actually have data to solve
            if not solver_input.sections or not solver_input.faculty:
                messages.error(request, "Error: Missing Sections or Faculty data. Please populate the academic/people apps first.")
                return redirect('planning_dashboard') # Replace with your actual dashboard URL name

            # 2. RUN SOLVER (Engine)
            print("Starting OR-Tools Solver...")
            # Note: This might take 10-30 seconds. In production, use Celery!
            result_json = solve_minimal_timetable(solver_input)

            if result_json:
                # 3. SAVE RESULTS (Transaction ensures all or nothing)
                with transaction.atomic():
                    save_timetable_to_db(session, result_json)
                    
                    # Update status
                    session.status = 'GENERATED'
                    session.save()
                    
                messages.success(request, f"Timetable generated successfully for {session.name}!")
                return redirect('view_timetable', session_id=session.id)
            else:
                messages.error(request, "Solver failed: Could not find a feasible schedule. Check your constraints (e.g., too many classes, not enough rooms).")
        
        except Exception as e:
            print(f"CRITICAL ERROR: {e}")
            messages.error(request, f"An internal error occurred: {str(e)}")

    return render(request, 'planning/confirm_generate.html', {'session': session})


def view_timetable(request, session_id):
    """
    Displays the generated timetable for a session.
    """
    session = get_object_or_404(PlanningSession, pk=session_id)
    
    # Fetch entries and sort by Day then Time
    entries = TimetableEntry.objects.filter(planning_session=session).select_related(
        'section', 'subject', 'faculty', 'room', 'day'
    ).order_by('day__id', 'start_time')

    # Group by Section for easier display in template
    timetable_by_section = {}
    for entry in entries:
        sec_name = entry.section.name
        if sec_name not in timetable_by_section:
            timetable_by_section[sec_name] = []
        timetable_by_section[sec_name].append(entry)

    return render(request, 'planning/view_timetable.html', {
        'session': session,
        'timetable': timetable_by_section
    })


def save_timetable_to_db(session, json_data):
    """
    Parses the JSON output from the solver and creates TimetableEntry rows.
    """
    print("Saving results to database...")
    
    # 1. Clear old entries for this session to avoid duplicates
    TimetableEntry.objects.filter(planning_session=session).delete()
    
    entries_to_create = []

    # 2. Iterate through the JSON structure
    # Expected JSON: [{'section': 'CS-3A', 'days': [{'day': 'Mon', 'entries': [...]}]}]
    for sec_data in json_data:
        sec_name = sec_data['section']
        
        # Find the Section object (Assuming unique name within the semester/program)
        # You might need to filter by session.semester if names aren't globally unique
        try:
            section_obj = Section.objects.get(name=sec_name, semester=session.semester)
        except Section.DoesNotExist:
            print(f"Warning: Section {sec_name} not found in DB. Skipping.")
            continue

        for day_data in sec_data['days']:
            day_name = day_data['day']
            try:
                day_obj = Day.objects.get(name=day_name)
            except Day.DoesNotExist:
                print(f"Warning: Day {day_name} not found. Skipping.")
                continue

            for entry in day_data['entries']:
                # Skip free slots or breaks if you don't want to save them
                if entry['subject'] == "FREE" or entry['subject'] == "LUNCH BREAK":
                    continue

                # Parse time range "09:00 - 09:50"
                t_parts = entry['time'].split(' - ')
                start_t = t_parts[0]
                end_t = t_parts[1]

                # Fetch related objects safely
                try:
                    sub_obj = Subject.objects.get(code=entry['subject'])
                    fac_obj = Faculty.objects.get(name=entry['faculty'])
                    room_obj = Room.objects.get(name=entry['room'])
                except Exception as e:
                    print(f"Error linking data for {entry}: {e}")
                    continue

                entries_to_create.append(TimetableEntry(
                    planning_session=session,
                    section=section_obj,
                    day=day_obj,
                    start_time=start_t,
                    end_time=end_t,
                    subject=sub_obj,
                    faculty=fac_obj,
                    room=room_obj
                ))
    
    # 3. Bulk Create for performance
    TimetableEntry.objects.bulk_create(entries_to_create)
    print(f"Saved {len(entries_to_create)} timetable entries.")