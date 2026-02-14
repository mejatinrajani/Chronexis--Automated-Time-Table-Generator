from .solver_prototype import MinimalData, Slot
# Adjust imports based on your project structure. 
# If 'core' is not in your python path, remove 'core.' prefix.
from core.academic.models import Section, Subject, SectionSubjectMap
from core.people.models import Faculty, FacultySubject
from core.infrastructure.models import Room
from core.times.models import TimeSlot, Day
from core.planning.models import PlanningSession

def build_data_for_session(session_id):
    """
    Fetches data from Django DB for a specific PlanningSession 
    and converts it to MinimalData for the solver.
    """
    # 1. Fetch the Session
    # We assume the session has linked sections. 
    # If not, we might need to fetch all sections for the session's semester.
    session = PlanningSession.objects.get(id=session_id)
    
    # Get sections related to this session (assuming you link them via PlanningSection)
    # If your PlanningSession doesn't explicitly link sections yet, 
    # you might want to filter Sections by the session's Semester.
    relevant_sections = Section.objects.filter(semester=session.semester)
    section_names = [s.name for s in relevant_sections]
    
    # 2. Get Subjects & Hours (The Demand)
    # We look at SectionSubjectMap to see what subjects these sections need
    hours = {s_name: {} for s_name in section_names}
    all_involved_subjects = set()

    for sec in relevant_sections:
        # Get all subjects required for this section
        maps = SectionSubjectMap.objects.filter(section=sec)
        for sm in maps:
            sub_code = sm.subject.code
            hours[sec.name][sub_code] = sm.required_hours
            all_involved_subjects.add(sm.subject)

    subject_list = [s.code for s in all_involved_subjects]

    # 3. Subject Metadata (Lab vs Theory)
    subject_types = {}
    subject_durations = {}
    for sub in all_involved_subjects:
        sType = "LAB" if sub.is_lab else "THEORY"
        subject_types[sub.code] = sType
        # If it's a lab, duration is 2 slots, else 1
        subject_durations[sub.code] = 2 if sub.is_lab else 1

    # 4. Faculty Competencies (The Supply)
    competencies = {} # {sub_code: [list of faculty names]}
    all_faculty_names = set()

    for sub in all_involved_subjects:
        # Find faculty who can teach this subject
        # Your model is FacultySubject
        fac_subjects = FacultySubject.objects.filter(subject=sub)
        
        # You can sort by preference here if you want later
        teachers = [fs.faculty.name for fs in fac_subjects]
        competencies[sub.code] = teachers
        for t in teachers:
            all_faculty_names.add(t)

    faculty_list = list(all_faculty_names)

    # 5. Rooms
    rooms = Room.objects.all()
    room_names = [r.name for r in rooms]
    room_types = {r.name: ("LAB" if r.is_lab else "THEORY") for r in rooms}

    # 6. Time Slots
    # We fetch all slots and convert them to the Solver's Slot object
    db_slots = TimeSlot.objects.all().order_by('day__id', 'index')
    solver_slots = []
    
    # Map Day names to 0-4 index
    # Assuming Day IDs are 1=Mon, 2=Tue... or similar. 
    # Let's map dynamically to be safe.
    unique_days = Day.objects.filter(is_working_day=True).order_by('id')
    day_map = {d.name: i for i, d in enumerate(unique_days)} 

    for ts in db_slots:
        if not ts.day.is_working_day:
            continue
        
        d_idx = day_map.get(ts.day.name)
        if d_idx is None: continue # Skip if day not in map

        new_slot = Slot(
            day_index=d_idx,
            day_name=ts.day.name,
            slot_index=ts.index,
            start_time=ts.start_time,
            end_time=ts.end_time,
            duration_minutes=50 # Approximation
        )
        solver_slots.append(new_slot)

    # 7. Return the Packet
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
        unavailability={}, # Add faculty availability logic here later
        hours=hours,
        scheduling_style="COMPACT"
    )