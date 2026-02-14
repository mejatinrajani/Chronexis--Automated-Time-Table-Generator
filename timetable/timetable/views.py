from django.shortcuts import render, get_object_or_404, redirect
from core.planning.models import PlanningSession
from .solver_adapter import build_data_for_session
from scheduler.solver.prototype_with_real_data import solve_minimal_timetable
from core.planning.models import TimetableEntry  
from core.academic.models import Section, Subject
from core.people.models import Faculty
from core.infrastructure.models import Room
from core.times.models import Day

def generate_timetable(request, session_id):
    session = get_object_or_404(PlanningSession, pk=session_id)
    
    if request.method == "POST":
        # 1. Adapter: Convert DB data to Solver data
        solver_data = build_data_for_session(session_id)
        
        # 2. Engine: Run the algorithms
        # Note: solve_minimal_timetable needs to return the JSON/Dict, not print it!
        result_json = solve_minimal_timetable(solver_data) 
        
        if result_json:
            # 3. Save: Parse JSON and save to TimetableEntry
            save_results_to_db(session, result_json)
            
            # Update Status
            session.status = 'GENERATED'
            session.save()
            
            return redirect('view_timetable', session_id=session.id)
            
    return render(request, 'timetable/confirm_generate.html', {'session': session})

def save_results_to_db(session, json_data):
    """
    Parses the JSON output from OR-Tools and saves it to Django models.
    """
    # Clear old entries for this session
    TimetableEntry.objects.filter(planning_session=session).delete()
    
    for section_data in json_data:
        sec_name = section_data['section']
        sec_obj = Section.objects.get(name=sec_name, semester=session.semester)
        
        for day_data in section_data['days']:
            day_name = day_data['day']
            day_obj = Day.objects.get(name=day_name)
            
            for entry in day_data['entries']:
                if entry['subject'] == 'FREE' or entry['subject'] == 'LUNCH BREAK':
                    continue
                
                # Parse times "09:00 - 09:50"
                t_str = entry['time'].split(' - ')
                start_t = t_str[0]
                end_t = t_str[1]
                
                # Fetch related objects
                # Note: Using name/code lookups. Ensure uniqueness!
                sub_obj = Subject.objects.get(code=entry['subject'])
                fac_obj = Faculty.objects.get(name=entry['faculty'])
                room_obj = Room.objects.get(name=entry['room'])
                
                TimetableEntry.objects.create(
                    planning_session=session,
                    section=sec_obj,
                    day=day_obj,
                    start_time=start_t,
                    end_time=end_t,
                    subject=sub_obj,
                    faculty=fac_obj,
                    room=room_obj
                )