from scheduler.solver.prototype_with_real_data import MinimalData, Slot 
from core.academic.models import SectionSubjectMap, Section, Subject
from core.people.models import Faculty, FacultySubject
from core.infrastructure.models import Room
from core.times.models import TimeSlot, Day
from core.planning.models import PlanningSession
def build_data_for_session(session_id):
    """
    Fetches data from Django DB for a specific PlanningSession 
    and converts it to MinimalData for the solver.
    """
    session = PlanningSession.objects.get(id=session_id)
    
    # 1. GET SECTIONS (Scoped to this planning session)
    # Assuming PlanningSession links to Sections via PlanningSection
    relevant_sections = [ps.section for ps in session.sections.all()]
    section_names = [s.name for s in relevant_sections]
    
    # 2. GET SUBJECTS & DURATIONS
    # We fetch all subjects linked to these sections
    all_subject_maps = SectionSubjectMap.objects.filter(section__in=relevant_sections)
    unique_subjects = set(sm.subject for sm in all_subject_maps)
    
    subject_list = [sub.code for sub in unique_subjects] # Using Code as ID (e.g. "CS101")
    
    subject_types = {}
    subject_durations = {}
    
    for sub in unique_subjects:
        # Map DB "is_lab" to Solver "LAB"/"THEORY"
        s_type = "LAB" if sub.is_lab else "THEORY"
        subject_types[sub.code] = s_type
        # Default duration is 1, labs might be 2 (You might need logic here)
        subject_durations[sub.code] = 2 if sub.is_lab else 1 

    # 3. GET HOURS (The Course Load)
    # This maps Section -> {Subject: Hours}
    hours = {s_name: {} for s_name in section_names}
    
    for sm in all_subject_maps:
        sec_name = sm.section.name
        sub_code = sm.subject.code
        hours[sec_name][sub_code] = sm.required_hours

    # 4. GET FACULTY & COMPETENCIES
    # We only care about faculty who teach the relevant subjects
    competencies = {} # {Subject_Code: [Faculty_Names]}
    
    for sub in unique_subjects:
        qualified_faculty = FacultySubject.objects.filter(subject=sub)
        competencies[sub.code] = [fs.faculty.name for fs in qualified_faculty]
        
    # Get list of all unique faculty names involved
    faculty_list = list(set([
        fs.faculty.name 
        for sub in unique_subjects 
        for fs in FacultySubject.objects.filter(subject=sub)
    ]))

    # 5. GET ROOMS
    rooms = Room.objects.all()
    room_names = [r.name for r in rooms]
    room_types = {r.name: ("LAB" if r.is_lab else "THEORY") for r in rooms}

    # 6. GET SLOTS (From `times` app)
    # We need to convert DB TimeSlots into the Solver's `Slot` object
    db_slots = TimeSlot.objects.all().select_related('day')
    solver_slots = []
    
    # Map DB Day Names to IDs (0=Mon, 1=Tue...)
    day_map = {d.name: i for i, d in enumerate(Day.objects.all())} # Adjust based on your Day model
    
    for idx, ts in enumerate(db_slots):
        # Skip non-working days if necessary
        if not ts.day.is_working_day:
            continue
            
        day_idx = day_map.get(ts.day.name, 0)
        
        # Create Solver Slot Object
        new_slot = Slot(
            day_index=day_idx,
            day_name=ts.day.name,
            slot_index=ts.index, # Ensure your DB has unique indices
            start_time=ts.start_time,
            end_time=ts.end_time,
            duration_minutes=50 # Calculate this from start/end if needed
        )
        solver_slots.append(new_slot)

    # 7. CONSTRUCT MINIMAL DATA
    return MinimalData(
        sections=section_names,
        subjects=subject_list,
        slots=solver_slots,
        faculty=faculty_list,
        rooms=room_names,
        room_types=room_types,
        subject_types=subject_types,
        subject_durations=subject_durations,
        competencies=competencies,
        unavailability={}, # You can map FacultyAvailability here later
        hours=hours,
        scheduling_style="COMPACT"
    )