import os 
import sys
import django

current_path = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_path, "../../"))
sys.path.append(project_root)   

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "timetable.settings")
django.setup()


from ortools.sat.python import cp_model
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import random, string
from datetime import time, timedelta, datetime
from scheduler.slots.models import Slot
import json
import pandas as pd
from pathlib import Path

@dataclass
class MinimalData:
    sections: List[str]
    subjects: List[str]
    slots: list 
    faculty: List[str]
    rooms: List[str]
    room_types: Dict[str, str]
    subject_types: Dict[str, str]    
    subject_durations: Dict[str, int]
    competencies: Dict[str, List[str]] 
    unavailability: Dict[str, List[int]]
    hours: Dict[str, Dict[str, int]]
    scheduling_style: str

    @property
    def num_slots(self):
        return len(self.slots)

def generate_time_slots(
    working_days: List[int],
    day_names: List[str],
    shift_start: time,
    shift_end: time,
    slot_duration_minutes: int = 50,
    break_periods: List[Tuple[time, time]] = None,
    buffer_minutes: int = 0,
    min_slot_gap_minutes: int = 0
) -> List[Slot]:
    if break_periods is None:
        break_periods = []

    all_slots = []
    current_date = datetime(2000, 1, 3)

    for day_idx in sorted(working_days):
        day_name = day_names[day_idx]
        

        current_time = datetime.combine(current_date, shift_start)
        slot_index = 0

        while current_time.time() < shift_end:
            slot_end = current_time + timedelta(minutes=slot_duration_minutes)


            if slot_end.time() > shift_end:
                break


            overlaps_break = False
            for break_start, break_end in break_periods:
                if not (slot_end.time() <= break_start or current_time.time() >= break_end):
                    overlaps_break = True
                    current_time = datetime.combine(current_date, break_end)
                    break

            if overlaps_break:
                continue

            slot = Slot(
                day_index=day_idx,
                day_name=day_name,
                slot_index=slot_index,
                start_time=current_time.time(),
                end_time=slot_end.time(),
                duration_minutes=slot_duration_minutes
            )
            all_slots.append(slot)
            slot_index += 1

            current_time = slot_end + timedelta(minutes=buffer_minutes + min_slot_gap_minutes)

    return all_slots


def calculate_lunch_break(shift_start: time, shift_end: time, duration_minutes: int = 60) -> List[Tuple[time, time]]:
    """
    Calculates a lunch break near the midpoint of the shift.
    Ensures lunch does not start before 12:00 PM.
    """
    
    dummy_date = datetime(2000, 1, 1)
    start_dt = datetime.combine(dummy_date, shift_start)
    end_dt = datetime.combine(dummy_date, shift_end)
    
    
    total_seconds = (end_dt - start_dt).total_seconds()
    midpoint_dt = start_dt + timedelta(seconds=total_seconds / 2)
    
    # Rule: Lunch shouldn't start before 12:00 PM
    earliest_lunch = datetime.combine(dummy_date, time(12, 0))
    
    # Target lunch start is either the midpoint or 12:00 PM, whichever is later
    lunch_start_dt = max(midpoint_dt - timedelta(minutes=duration_minutes / 2), earliest_lunch)
    
    if lunch_start_dt.minute < 15:
        lunch_start_dt = lunch_start_dt.replace(minute=0)
    elif lunch_start_dt.minute < 45:
        lunch_start_dt = lunch_start_dt.replace(minute=30)
    else:
        lunch_start_dt = (lunch_start_dt + timedelta(hours=1)).replace(minute=0)

    lunch_end_dt = lunch_start_dt + timedelta(minutes=duration_minutes)
    
    return [(lunch_start_dt.time(), lunch_end_dt.time())]

def solve_minimal_timetable(data: MinimalData):
    model = cp_model.CpModel()
    assign, is_start, assign_room, fac_assign = {}, {}, {}, {}

    slots_by_day = {}
    for idx, s in enumerate(data.slots):
        slots_by_day.setdefault(s.day_index, []).append(idx)

    # --- 1. Variable Creation ---
    for sec in data.sections:
        for sub in data.hours[sec].keys():
            qualified = data.competencies.get(sub, [])
            for fac in qualified:
                fac_assign[(sec, sub, fac)] = model.NewBoolVar(f"teach_{sec}_{sub}_{fac}")
            model.Add(sum(fac_assign[(sec, sub, fac)] for fac in qualified) == 1)

            sub_type = data.subject_types[sub]
            valid_rooms = [r for r in data.rooms if data.room_types[r] == sub_type]
            
            for s_idx in range(data.num_slots):
                assign[(sec, sub, s_idx)] = model.NewBoolVar(f"as_{sec}_{sub}_{s_idx}")
                is_start[(sec, sub, s_idx)] = model.NewBoolVar(f"st_{sec}_{sub}_{s_idx}")
                for r in valid_rooms:
                    assign_room[(sec, sub, r, s_idx)] = model.NewBoolVar(f"asr_{sec}_{sub}_{r}_{s_idx}")
                model.Add(assign[(sec, sub, s_idx)] == sum(assign_room[(sec, sub, r, s_idx)] for r in valid_rooms))

    # --- 2. Hard Clash Constraints (NEVER RELAX THESE) ---
    for fac in data.faculty:
        for s_idx in range(data.num_slots):
            busy_vars = [assign[(sec, sub, s_idx)] for sec in data.sections for sub in data.hours[sec].keys() 
                         if fac in data.competencies.get(sub, []) and (sec, sub, fac) in fac_assign]
            # Use logic: A faculty is busy if (assigned AND teaching that specific section)
            # For performance with 52 sections, we use a simpler conflict check:
            model.AddAtMostOne(assign_room[(sec, sub, r, s_idx)] 
                               for sec in data.sections for sub in data.hours[sec].keys() 
                               for r in data.rooms if fac in data.competencies.get(sub, []) 
                               and (sec, sub, r, s_idx) in assign_room)

    for r in data.rooms:
        for s_idx in range(data.num_slots):
            usage = [assign_room[(sec, sub, r, s_idx)] for sec in data.sections 
                     for sub in data.hours[sec].keys() if (sec, sub, r, s_idx) in assign_room]
            if usage: model.AddAtMostOne(usage)

    # --- 3. Softened Logistics & Optimization ---
    obj_vars = []
    for sec in data.sections:
        for s_idx in range(data.num_slots):
            model.AddAtMostOne(assign[(sec, sub, s_idx)] for sub in data.hours[sec].keys())

        for sub, credits in data.hours[sec].items():
            duration = data.subject_durations.get(sub, 1)
            model.Add(sum(is_start[(sec, sub, s)] for s in range(data.num_slots)) == credits)

            # SOFT: Subject Diversity (Penalty if > 2 per day)
            for day_idx, indices in slots_by_day.items():
                day_sub_vars = [assign[(sec, sub, s_idx)] for s_idx in indices]
                over_limit = model.NewBoolVar(f"over_{sec}_{sub}_{day_idx}")
                model.Add(sum(day_sub_vars) <= 2).OnlyEnforceIf(over_limit.Not())
                obj_vars.append(over_limit * 1000)

            if duration == 2: # Lab logic (Consecutive)
                for s in range(data.num_slots):
                    if s == 0: model.Add(assign[(sec, sub, s)] == is_start[(sec, sub, s)])
                    else: model.Add(assign[(sec, sub, s)] == is_start[(sec, sub, s)] + is_start[(sec, sub, s-1)])
                for day_idx, indices in slots_by_day.items():
                    model.Add(is_start[(sec, sub, indices[-1])] == 0)
            else:
                for s in range(data.num_slots): model.Add(assign[(sec, sub, s)] == is_start[(sec, sub, s)])

        # SOFT: Anti-Isolation & Gaps
        for day_idx, indices in slots_by_day.items():
            is_occ = {s: model.NewBoolVar(f"o_{sec}_{s}") for s in indices}
            for s in indices:
                model.AddMaxEquality(is_occ[s], [assign[(sec, sub, s)] for sub in data.hours[sec].keys()])
            
            active = model.NewBoolVar(f"act_{sec}_{day_idx}")
            model.Add(sum(is_occ[s] for s in indices) >= 1).OnlyEnforceIf(active)
            
            for i, s_idx in enumerate(indices):
                # Gap Penalty
                gap = model.NewBoolVar(f"g_{sec}_{s_idx}")
                model.AddBoolAnd([active, is_occ[s_idx].Not()]).OnlyEnforceIf(gap)
                obj_vars.append(gap * 500)

                # Loneliness Penalty (Soft)
                neigh = [indices[j] for j in [i-1, i+1] if 0 <= j < len(indices)]
                if neigh:
                    has_neigh = model.NewBoolVar(f"h_{sec}_{s_idx}")
                    model.AddMaxEquality(has_neigh, [is_occ[n] for n in neigh])
                    lonely = model.NewBoolVar(f"l_{sec}_{s_idx}")
                    model.AddBoolAnd([is_occ[s_idx], has_neigh.Not()]).OnlyEnforceIf(lonely)
                    obj_vars.append(lonely * 2000)

    model.Minimize(sum(obj_vars))

    # --- 4. High-Performance Solver Settings ---
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 600.0 # 10 mins
    solver.parameters.num_search_workers = 8    
    solver.parameters.log_search_progress = True
    
    # These two lines are "The Secret Sauce" for large models
    solver.parameters.linearization_level = 0 
    solver.parameters.exploit_best_solution = True

    status = solver.Solve(model)

    if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
        print(f"SUCCESS: {solver.StatusName(status)}")
        #print faculty workload
        print_faculty_workload_report(data, solver, assign, fac_assign)
        #convert the result to json
        json_timetable = get_timetable_json(data, solver, assign, fac_assign, assign_room, slots_by_day)
        #save the excel file to the exports folder
        export_path = os.path.abspath(os.path.join(project_root, "exports"))
        export_json_to_excel(json_timetable, folder_path=export_path)


        def get_info(sec, s_idx):
            for sub in data.hours[sec].keys():
                if solver.Value(assign[(sec, sub, s_idx)]) == 1:
                    prof = next(f for f in data.competencies[sub] if solver.Value(fac_assign[(sec, sub, f)]) == 1)
                    room = next(r for r in data.rooms if (sec, sub, r, s_idx) in assign_room and solver.Value(assign_room[(sec, sub, r, s_idx)]) == 1)
                    return f"{sub:<10} | {prof:<12} | {room}"
            return "FREE".center(31, " ")

        for sec in data.sections:
            print(f"\n{'='*80}\nSECTION: {sec}\n{'='*80}")
            for day_idx in sorted(slots_by_day.keys()):
                indices = slots_by_day[day_idx]
                print(f"\n--- {data.slots[indices[0]].day_name.upper()} ---")
                expected_start = data.slots[indices[0]].start_time 
                for s_idx in indices:
                    s = data.slots[s_idx]
                    if s.start_time > expected_start:
                        print(f" {expected_start.strftime('%H:%M')} - {s.start_time.strftime('%H:%M')} | {'[ LUNCH BREAK ]'.center(31, ' ')}")
                    print(f" {s.start_time.strftime('%H:%M')} - {s.end_time.strftime('%H:%M')} | {get_info(sec, s_idx)}")
                    expected_start = s.end_time
    else:
        print("COULD NOT GENERATE FEASIBLE TIMETABLE.")

def create_realistic_large_instance() -> MinimalData:
    shift_start, shift_end = time(9, 0), time(17, 0)
    slots = generate_time_slots([0,1,2,3,4], ["Mon","Tue","Wed","Thu","Fri"], shift_start, shift_end, 50, calculate_lunch_break(shift_start, shift_end))

    sections = [f"SEC-{i:02d}" for i in range(1, 31)] # 30 SECTIONS
    faculty = [f"Prof-{string.ascii_uppercase[i//26]}{string.ascii_uppercase[i%26]}" for i in range(100)]
    
    theory_subjects = ["OS", "DBMS", "DAA", "AI", "MATH", "CN", "Automata"]
    lab_subjects = ["OS Lab", "DBMS Lab", "CN Lab", "Programming Lab"]
    
    subject_types = {s: "THEORY" for s in theory_subjects}
    subject_types.update({s: "LAB" for s in lab_subjects})
    subject_durations = {s: 1 for s in theory_subjects}
    subject_durations.update({s: 2 for s in lab_subjects})

    # Competency Pool
    competencies = {sub: random.sample(faculty, k=random.randint(5, 8)) for sub in theory_subjects + lab_subjects}

    user_hours = {}
    for sec in sections:
        credits = {}
        for sub in random.sample(theory_subjects, 4): credits[sub] = random.randint(3, 4)
        for sub in random.sample(lab_subjects, 2): credits[sub] = 2 
        user_hours[sec] = credits

    return MinimalData(
        sections=sections, subjects=theory_subjects+lab_subjects, slots=slots,
        faculty=faculty, rooms=[f"R-{i}" for i in range(50)], 
        room_types={f"R-{i}": ("THEORY" if i < 40 else "LAB") for i in range(50)},
        subject_types=subject_types, subject_durations=subject_durations,
        competencies=competencies, unavailability={}, hours=user_hours, scheduling_style="COMPACT"
    )



def get_timetable_json(data: MinimalData, solver, assign, fac_assign, assign_room, slots_by_day):
    timetable_data = []

    for sec in data.sections:
        section_schedule = {"section": sec, "days": []}
        
        for day_idx in sorted(slots_by_day.keys()):
            indices = slots_by_day[day_idx]
            day_name = data.slots[indices[0]].day_name
            day_entries = []
            
            expected_start = data.slots[indices[0]].start_time
            
            for s_idx in indices:
                s = data.slots[s_idx]
                
                # Add Lunch Break to JSON if a gap exists
                if s.start_time > expected_start:
                    day_entries.append({
                        "time": f"{expected_start.strftime('%H:%M')} - {s.start_time.strftime('%H:%M')}",
                        "subject": "LUNCH BREAK",
                        "faculty": "-",
                        "room": "-"
                    })

                # Find assigned subject
                entry = {"time": f"{s.start_time.strftime('%H:%M')} - {s.end_time.strftime('%H:%M')}", 
                         "subject": "FREE", "faculty": "-", "room": "-"}
                
                for sub in data.hours[sec].keys():
                    if solver.Value(assign[(sec, sub, s_idx)]) == 1:
                        prof = next(f for f in data.competencies[sub] if solver.Value(fac_assign[(sec, sub, f)]) == 1)
                        room = next(r for r in data.rooms if (sec, sub, r, s_idx) in assign_room and solver.Value(assign_room[(sec, sub, r, s_idx)]) == 1)
                        entry.update({"subject": sub, "faculty": prof, "room": room})
                        break
                
                day_entries.append(entry)
                expected_start = s.end_time
            
            section_schedule["days"].append({"day": day_name, "entries": day_entries})
        
        timetable_data.append(section_schedule)
    
    return timetable_data



def export_json_to_excel(json_data, folder_path="exports"):
    # Ensure directory exists
    Path(folder_path).mkdir(parents=True, exist_ok=True)
    
    flattened_data = []
    for section in json_data:
        sec_name = section["section"]
        for day in section["days"]:
            day_name = day["day"]
            for entry in day["entries"]:
                flattened_data.append({
                    "Section": sec_name,
                    "Day": day_name,
                    "Time Range": entry["time"],
                    "Subject": entry["subject"],
                    "Faculty": entry["faculty"],
                    "Room": entry["room"]
                })
    
    df = pd.DataFrame(flattened_data)
    
    # Save to file
    filename = f"Timetable_Export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    file_path = Path(folder_path) / filename
    
    df.to_excel(file_path, index=False)
    print(f"\n✅ Excel file saved to: {file_path}")
    return file_path

def create_real_gla_large_instance() -> MinimalData:
    """
    Manual data entry function for GLA University style instance.
    Optimized for a 52-section stress test.
    """
    # 1. TIME SETUP
    shift_start, shift_end = time(9, 0), time(17, 0)
    lunch = calculate_lunch_break(shift_start, shift_end)
    slots = generate_time_slots(
        working_days=[0, 1, 2, 3, 4],
        day_names=["Mon", "Tue", "Wed", "Thu", "Fri"],
        shift_start=shift_start,
        shift_end=shift_end,
        slot_duration_minutes=50,
        break_periods=lunch
    )

    # 2. SECTIONS (52 total)
    sections = [
        "CS-3A", "CS-3B", "CS-3C", "CS-3D", "CS-3E", "CS-3F", "CS-3G", "CS-3H", "CS-3I", "CS-3J",
        "CS-3K", "CS-3L", "CS-3M", "CS-3N", "CS-3O", "CS-3P", "CS-3Q", "CS-3R", "CS-3S", "CS-3T",
        "CS-3U", "CS-3V", "CS-3W", "CS-3X", "CS-3Y", "CS-3Z",
        "CS-3AA", "CS-3AB", "CS-3AC", "CS-3AD", "CS-3AE", "CS-3AF"]

    # 3. FACULTY LIST (30 Unique Teachers)
    faculty = [
        "Prof. Rajesh Sharma", "Prof. Priya Patel", "Prof. Amit Kumar", "Dr. Ananya Desai", "Prof. Vikram Singh", 
        "Dr. Meera Reddy", "Prof. Arjun Nair", "Prof. Sneha Menon", "Dr. Sanjay Verma", "Prof. Kavita Joshi", 
        "Prof. Anjali Mehta", "Dr. Ravi Iyer", "Prof. Anjali Chatterjee", "Prof. Deepak Banerjee", "Dr. Swati Kapoor", 
        "Prof. Rohit Das", "Prof. Neha Gupta", "Dr. Karan Malhotra", "Prof. Sunita Rao", "Prof. Manoj Tiwari", 
        "Dr. Pooja Sharma", "Prof. Akhilesh Jha", "Prof. Alok Mishra", "Prof. Tanvi Saxena", "Dr. Rajiv Mehta", 
        "Prof. Nisha Singh", "Prof. Aditya Choudhury", "Prof. Smriti Irani", "Dr. Divya Jain", "Prof. Varun Bhatt", 
        "Prof. Ishita Roy", "Dr. Suresh Pillai", "Prof. Maya Krishnan", "Prof. Preeti Sharma", "Prof. Disha Singh",
        "Dr. K.P. Yadav", "Prof. S.K. Gupta", "Dr. Mukul Dixit", "Prof. Arpit Jain", "Dr. Shweta Singh",
        "Prof. Gaurav Kumar", "Dr. Neerja Talwar", "Prof. Himanshu Mittal", "Dr. Ritu Bhargava", "Prof. Sandeep Rawat",
        "Dr. Pankaj Pathak", "Prof. Kriti Azad", "Dr. Yogesh Chandra", "Prof. Abhay Pratap", "Dr. Suman Lata",
        "Prof. Vipin Saini", "Dr. Anil Kothari", "Prof. Madhu Sudan", "Dr. Rekha Rani", "Prof. Sunil Dutt",
        "Dr. J.P. Singh", "Prof. Om Prakash", "Dr. Bharti Mittal", "Prof. K.K. Sharma", "Dr. Poonam Sethi"
    ]

    # 4. SUBJECT METADATA
    subject_types = {
        "OS": "THEORY", "DBMS": "THEORY", "Automata": "THEORY", "Programming" : "THEORY",
        "Quant" : "THEORY", "Logical Reasoning" : "THEORY", "Digital Image Processing" : "THEORY",
        "OS Lab": "LAB", "DBMS Lab": "LAB", "Digital Image Processing Lab" : "LAB",
    }
    
    # FIX: Set Lab durations to 2 so the Atomic Continuity logic triggers. Theory is 1.
    subject_durations = {
        "OS": 1, "DBMS": 1, "Automata": 1, "Programming": 1, "Quant": 1, 
        "Logical Reasoning": 1, "Digital Image Processing": 1,
        "OS Lab": 2, "DBMS Lab": 2, "Digital Image Processing Lab": 2
    }

    # 5. FACULTY COMPETENCY (The Mapping)
    competencies = {
        "OS": ["Prof. Rajesh Sharma", "Prof. Arjun Nair", "Prof. Vikram Singh", "Dr. Meera Reddy", "Prof. Aditya Choudhury", "Prof. Akhilesh Jha", "Prof. Preeti Sharma", "Dr. K.P. Yadav", "Prof. S.K. Gupta", "Dr. Mukul Dixit"],
        "DBMS": ["Dr. Sanjay Verma", "Prof. Nisha Singh", "Dr. Pooja Sharma", "Prof. Alok Mishra", "Dr. Rajiv Mehta", "Prof. Smriti Irani", "Prof. Disha Singh", "Prof. Arpit Jain", "Dr. Shweta Singh", "Prof. Gaurav Kumar"],
        "Automata": ["Prof. Vikram Singh", "Prof. Rajesh Sharma", "Dr. Karan Malhotra", "Prof. Neha Gupta", "Dr. Swati Kapoor", "Prof. Anjali Mehta", "Dr. Neerja Talwar", "Prof. Himanshu Mittal", "Dr. Ritu Bhargava"],
        "Programming": ["Prof. Amit Kumar", "Dr. Ravi Iyer", "Prof. Manoj Tiwari", "Prof. Tanvi Saxena", "Dr. Rajiv Mehta", "Prof. Sandeep Rawat", "Dr. Pankaj Pathak", "Prof. Kriti Azad", "Dr. Yogesh Chandra"],
        "Quant": ["Prof. Rohit Das", "Dr. Suresh Pillai", "Prof. Varun Bhatt", "Prof. Maya Krishnan", "Prof. Kavita Joshi", "Prof. Abhay Pratap", "Dr. Suman Lata", "Prof. Vipin Saini", "Dr. Anil Kothari"],
        "Logical Reasoning": ["Prof. Anjali Chatterjee", "Prof. Varun Bhatt", "Prof. Ishita Roy", "Prof. Priya Patel", "Dr. Divya Jain", "Prof. Madhu Sudan", "Dr. Rekha Rani", "Prof. Sunil Dutt", "Dr. J.P. Singh"],
        "Digital Image Processing": ["Dr. Ananya Desai", "Prof. Deepak Banerjee", "Dr. Swati Kapoor", "Prof. Neha Gupta", "Dr. Meera Reddy", "Prof. Om Prakash", "Dr. Bharti Mittal", "Prof. K.K. Sharma", "Dr. Poonam Sethi"],
        
        # Labs (Mapped to the same subject experts)
        "OS Lab": ["Prof. Rajesh Sharma", "Prof. Arjun Nair", "Dr. Meera Reddy", "Prof. Aditya Choudhury", "Prof. Manoj Tiwari", "Dr. K.P. Yadav", "Prof. S.K. Gupta"],
        "DBMS Lab": ["Dr. Sanjay Verma", "Prof. Nisha Singh", "Dr. Pooja Sharma", "Dr. Rajiv Mehta", "Prof. Sunita Rao", "Prof. Arpit Jain", "Dr. Shweta Singh"],
        "Digital Image Processing Lab": ["Dr. Ananya Desai", "Prof. Deepak Banerjee", "Dr. Swati Kapoor", "Prof. Ishita Roy", "Dr. Meera Reddy", "Prof. Om Prakash", "Dr. Bharti Mittal"]
    }

    # 6. ROOMS (55 Theory + 15 Labs)
    theory_rooms = [f"AB1-{101+i}" for i in range(55)]
    lab_rooms = [f"LAB-{i+1}" for i in range(20)]
    rooms = theory_rooms + lab_rooms
    room_types = {r: "THEORY" for r in theory_rooms}
    room_types.update({r: "LAB" for r in lab_rooms})

    # 7. SECTION-WISE COURSE LOAD (Credits)
    user_hours = {
"CS-3A": {"OS": 3, "DBMS": 4, "Automata": 3, "Programming": 2, "Quant": 1, "Logical Reasoning": 1, "Digital Image Processing": 2, "OS Lab": 2, "DBMS Lab": 2, "Digital Image Processing Lab": 2},
"CS-3B": {"OS": 4, "DBMS": 3, "Automata": 2, "Programming": 3, "Quant": 2, "Logical Reasoning": 1, "Digital Image Processing": 2, "OS Lab": 2, "DBMS Lab": 2, "Digital Image Processing Lab": 2},
"CS-3C": {"OS": 3, "DBMS": 3, "Automata": 3, "Programming": 2, "Quant": 1, "Logical Reasoning": 2, "Digital Image Processing": 3, "OS Lab": 2, "DBMS Lab": 2, "Digital Image Processing Lab": 1},
"CS-3D": {"OS": 4, "DBMS": 2, "Automata": 4, "Programming": 1, "Quant": 2, "Logical Reasoning": 2, "Digital Image Processing": 1, "OS Lab": 2, "DBMS Lab": 2, "Digital Image Processing Lab": 2},
"CS-3E": {"OS": 3, "DBMS": 3, "Automata": 2, "Programming": 3, "Quant": 2, "Logical Reasoning": 1, "Digital Image Processing": 3, "OS Lab": 2, "DBMS Lab": 2, "Digital Image Processing Lab": 2},
"CS-3F": {"OS": 3, "DBMS": 4, "Automata": 3, "Programming": 2, "Quant": 1, "Logical Reasoning": 2, "Digital Image Processing": 2, "OS Lab": 2, "DBMS Lab": 2, "Digital Image Processing Lab": 2},
"CS-3G": {"OS": 4, "DBMS": 3, "Automata": 3, "Programming": 2, "Quant": 2, "Logical Reasoning": 1, "Digital Image Processing": 3, "OS Lab": 2, "DBMS Lab": 2, "Digital Image Processing Lab": 1},
"CS-3H": {"OS": 3, "DBMS": 3, "Automata": 4, "Programming": 1, "Quant": 2, "Logical Reasoning": 2, "Digital Image Processing": 2, "OS Lab": 2, "DBMS Lab": 2, "Digital Image Processing Lab": 2},
"CS-3I": {"OS": 3, "DBMS": 4, "Automata": 2, "Programming": 3, "Quant": 1, "Logical Reasoning": 1, "Digital Image Processing": 2, "OS Lab": 2, "DBMS Lab": 2, "Digital Image Processing Lab": 2},
"CS-3J": {"OS": 4, "DBMS": 3, "Automata": 3, "Programming": 2, "Quant": 2, "Logical Reasoning": 2, "Digital Image Processing": 3, "OS Lab": 2, "DBMS Lab": 2, "Digital Image Processing Lab": 2},
"CS-3K": {"OS": 3, "DBMS": 3, "Automata": 3, "Programming": 2, "Quant": 1, "Logical Reasoning": 1, "Digital Image Processing": 2, "OS Lab": 2, "DBMS Lab": 2, "Digital Image Processing Lab": 1},
"CS-3L": {"OS": 4, "DBMS": 2, "Automata": 4, "Programming": 1, "Quant": 2, "Logical Reasoning": 2, "Digital Image Processing": 1, "OS Lab": 2, "DBMS Lab": 2, "Digital Image Processing Lab": 2},
"CS-3M": {"OS": 3, "DBMS": 3, "Automata": 2, "Programming": 3, "Quant": 2, "Logical Reasoning": 1, "Digital Image Processing": 3, "OS Lab": 2, "DBMS Lab": 2, "Digital Image Processing Lab": 2},
"CS-3N": {"OS": 3, "DBMS": 4, "Automata": 3, "Programming": 2, "Quant": 1, "Logical Reasoning": 2, "Digital Image Processing": 2, "OS Lab": 2, "DBMS Lab": 2, "Digital Image Processing Lab": 2},
"CS-3O": {"OS": 4, "DBMS": 3, "Automata": 3, "Programming": 2, "Quant": 2, "Logical Reasoning": 1, "Digital Image Processing": 3, "OS Lab": 2, "DBMS Lab": 2, "Digital Image Processing Lab": 1},
"CS-3P": {"OS": 3, "DBMS": 3, "Automata": 4, "Programming": 1, "Quant": 2, "Logical Reasoning": 2, "Digital Image Processing": 2, "OS Lab": 2, "DBMS Lab": 2, "Digital Image Processing Lab": 2},
"CS-3Q": {"OS": 3, "DBMS": 4, "Automata": 2, "Programming": 3, "Quant": 1, "Logical Reasoning": 1, "Digital Image Processing": 2, "OS Lab": 2, "DBMS Lab": 2, "Digital Image Processing Lab": 2},
"CS-3R": {"OS": 4, "DBMS": 3, "Automata": 3, "Programming": 2, "Quant": 2, "Logical Reasoning": 2, "Digital Image Processing": 3, "OS Lab": 2, "DBMS Lab": 2, "Digital Image Processing Lab": 2},
"CS-3S": {"OS": 3, "DBMS": 3, "Automata": 3, "Programming": 2, "Quant": 1, "Logical Reasoning": 1, "Digital Image Processing": 2, "OS Lab": 2, "DBMS Lab": 2, "Digital Image Processing Lab": 1},
"CS-3T": {"OS": 4, "DBMS": 2, "Automata": 4, "Programming": 1, "Quant": 2, "Logical Reasoning": 2, "Digital Image Processing": 1, "OS Lab": 2, "DBMS Lab": 2, "Digital Image Processing Lab": 2},
"CS-3U": {"OS": 3, "DBMS": 3, "Automata": 2, "Programming": 3, "Quant": 2, "Logical Reasoning": 1, "Digital Image Processing": 3, "OS Lab": 2, "DBMS Lab": 2, "Digital Image Processing Lab": 2},
"CS-3V": {"OS": 3, "DBMS": 4, "Automata": 3, "Programming": 2, "Quant": 1, "Logical Reasoning": 2, "Digital Image Processing": 2, "OS Lab": 2, "DBMS Lab": 2, "Digital Image Processing Lab": 2},
"CS-3W": {"OS": 4, "DBMS": 3, "Automata": 3, "Programming": 2, "Quant": 2, "Logical Reasoning": 1, "Digital Image Processing": 3, "OS Lab": 2, "DBMS Lab": 2, "Digital Image Processing Lab": 1},
"CS-3X": {"OS": 3, "DBMS": 3, "Automata": 4, "Programming": 1, "Quant": 2, "Logical Reasoning": 2, "Digital Image Processing": 2, "OS Lab": 2, "DBMS Lab": 2, "Digital Image Processing Lab": 2},
"CS-3Y": {"OS": 3, "DBMS": 4, "Automata": 2, "Programming": 3, "Quant": 1, "Logical Reasoning": 1, "Digital Image Processing": 2, "OS Lab": 2, "DBMS Lab": 2, "Digital Image Processing Lab": 2},
"CS-3Z": {"OS": 4, "DBMS": 3, "Automata": 3, "Programming": 2, "Quant": 2, "Logical Reasoning": 2, "Digital Image Processing": 3, "OS Lab": 2, "DBMS Lab": 2, "Digital Image Processing Lab": 2},
"CS-3AA": {"OS": 3, "DBMS": 3, "Automata": 3, "Programming": 2, "Quant": 1, "Logical Reasoning": 1, "Digital Image Processing": 2, "OS Lab": 2, "DBMS Lab": 2, "Digital Image Processing Lab": 1},
"CS-3AB": {"OS": 4, "DBMS": 2, "Automata": 4, "Programming": 1, "Quant": 2, "Logical Reasoning": 2, "Digital Image Processing": 1, "OS Lab": 2, "DBMS Lab": 2, "Digital Image Processing Lab": 2},
"CS-3AC": {"OS": 3, "DBMS": 3, "Automata": 2, "Programming": 3, "Quant": 2, "Logical Reasoning": 1, "Digital Image Processing": 3, "OS Lab": 2, "DBMS Lab": 2, "Digital Image Processing Lab": 2},
"CS-3AD": {"OS": 3, "DBMS": 4, "Automata": 3, "Programming": 2, "Quant": 1, "Logical Reasoning": 2, "Digital Image Processing": 2, "OS Lab": 2, "DBMS Lab": 2, "Digital Image Processing Lab": 2},
"CS-3AE": {"OS": 4, "DBMS": 3, "Automata": 3, "Programming": 2, "Quant": 2, "Logical Reasoning": 1, "Digital Image Processing": 3, "OS Lab": 2, "DBMS Lab": 2, "Digital Image Processing Lab": 1},
"CS-3AF": {"OS": 3, "DBMS": 3, "Automata": 4, "Programming": 1, "Quant": 2, "Logical Reasoning": 2, "Digital Image Processing": 2, "OS Lab": 2, "DBMS Lab": 2, "Digital Image Processing Lab": 2},
"CS-3AG": {"OS": 3, "DBMS": 4, "Automata": 2, "Programming": 3, "Quant": 1, "Logical Reasoning": 1, "Digital Image Processing": 2, "OS Lab": 2, "DBMS Lab": 2, "Digital Image Processing Lab": 2},
"CS-3AH": {"OS": 4, "DBMS": 3, "Automata": 3, "Programming": 2, "Quant": 2, "Logical Reasoning": 2, "Digital Image Processing": 3, "OS Lab": 2, "DBMS Lab": 2, "Digital Image Processing Lab": 2},
"CS-3AI": {"OS": 3, "DBMS": 3, "Automata": 3, "Programming": 2, "Quant": 1, "Logical Reasoning": 1, "Digital Image Processing": 2, "OS Lab": 2, "DBMS Lab": 2, "Digital Image Processing Lab": 1},
"CS-3AJ": {"OS": 4, "DBMS": 2, "Automata": 4, "Programming": 1, "Quant": 2, "Logical Reasoning": 2, "Digital Image Processing": 1, "OS Lab": 2, "DBMS Lab": 2, "Digital Image Processing Lab": 2},
"CS-3AK": {"OS": 3, "DBMS": 3, "Automata": 2, "Programming": 3, "Quant": 2, "Logical Reasoning": 1, "Digital Image Processing": 3, "OS Lab": 2, "DBMS Lab": 2, "Digital Image Processing Lab": 2},
"CS-3AL": {"OS": 3, "DBMS": 4, "Automata": 3, "Programming": 2, "Quant": 1, "Logical Reasoning": 2, "Digital Image Processing": 2, "OS Lab": 2, "DBMS Lab": 2, "Digital Image Processing Lab": 2},
"CS-3AM": {"OS": 4, "DBMS": 3, "Automata": 3, "Programming": 2, "Quant": 2, "Logical Reasoning": 1, "Digital Image Processing": 3, "OS Lab": 2, "DBMS Lab": 2, "Digital Image Processing Lab": 1},
"CS-3AN": {"OS": 3, "DBMS": 3, "Automata": 4, "Programming": 1, "Quant": 2, "Logical Reasoning": 2, "Digital Image Processing": 2, "OS Lab": 2, "DBMS Lab": 2, "Digital Image Processing Lab": 2},
"CS-3AO": {"OS": 3, "DBMS": 4, "Automata": 2, "Programming": 3, "Quant": 1, "Logical Reasoning": 1, "Digital Image Processing": 2, "OS Lab": 2, "DBMS Lab": 2, "Digital Image Processing Lab": 2},
"CS-3AP": {"OS": 4, "DBMS": 3, "Automata": 3, "Programming": 2, "Quant": 2, "Logical Reasoning": 2, "Digital Image Processing": 3, "OS Lab": 2, "DBMS Lab": 2, "Digital Image Processing Lab": 2},
"CS-3AQ": {"OS": 3, "DBMS": 3, "Automata": 3, "Programming": 2, "Quant": 1, "Logical Reasoning": 1, "Digital Image Processing": 2, "OS Lab": 2, "DBMS Lab": 2, "Digital Image Processing Lab": 1},
"CS-3AR": {"OS": 4, "DBMS": 2, "Automata": 4, "Programming": 1, "Quant": 2, "Logical Reasoning": 2, "Digital Image Processing": 1, "OS Lab": 2, "DBMS Lab": 2, "Digital Image Processing Lab": 2},
"CS-3AS": {"OS": 3, "DBMS": 3, "Automata": 2, "Programming": 3, "Quant": 2, "Logical Reasoning": 1, "Digital Image Processing": 3, "OS Lab": 2, "DBMS Lab": 2, "Digital Image Processing Lab": 2},
"CS-3AT": {"OS": 3, "DBMS": 4, "Automata": 3, "Programming": 2, "Quant": 1, "Logical Reasoning": 2, "Digital Image Processing": 2, "OS Lab": 2, "DBMS Lab": 2, "Digital Image Processing Lab": 2},
"CS-3AU": {"OS": 4, "DBMS": 3, "Automata": 3, "Programming": 2, "Quant": 2, "Logical Reasoning": 1, "Digital Image Processing": 3, "OS Lab": 2, "DBMS Lab": 2, "Digital Image Processing Lab": 1},
"CS-3AV": {"OS": 3, "DBMS": 3, "Automata": 4, "Programming": 1, "Quant": 2, "Logical Reasoning": 2, "Digital Image Processing": 2, "OS Lab": 2, "DBMS Lab": 2, "Digital Image Processing Lab": 2},
"CS-3AW": {"OS": 3, "DBMS": 4, "Automata": 2, "Programming": 3, "Quant": 1, "Logical Reasoning": 1, "Digital Image Processing": 2, "OS Lab": 2, "DBMS Lab": 2, "Digital Image Processing Lab": 2},
"CS-3AX": {"OS": 4, "DBMS": 3, "Automata": 3, "Programming": 2, "Quant": 2, "Logical Reasoning": 2, "Digital Image Processing": 3, "OS Lab": 2, "DBMS Lab": 2, "Digital Image Processing Lab": 2},
"CS-3AY": {"OS": 3, "DBMS": 3, "Automata": 3, "Programming": 2, "Quant": 1, "Logical Reasoning": 1, "Digital Image Processing": 2, "OS Lab": 2, "DBMS Lab": 2, "Digital Image Processing Lab": 1},
"CS-3AZ": {"OS": 4, "DBMS": 2, "Automata": 4, "Programming": 1, "Quant": 2, "Logical Reasoning": 2, "Digital Image Processing": 1, "OS Lab": 2, "DBMS Lab": 2, "Digital Image Processing Lab": 2}
}

    return MinimalData(
        sections=sections, subjects=list(subject_types.keys()), slots=slots,
        faculty=faculty, rooms=rooms, room_types=room_types,
        subject_types=subject_types, subject_durations=subject_durations,
        competencies=competencies, unavailability={}, hours=user_hours,
        scheduling_style="COMPACT"
    )

def validate_gla_data(data: MinimalData):
    print("\n" + "═"*60)
    print(" 🔍 PRE-SOLVE DATA VALIDATION (WEEKLY) ".center(60, "═"))
    print("═"*60)
    
    # Total unique time slots available in the whole week definition
    total_slots_in_week = len(data.slots) 
    max_faculty_load = 30 # Maximum recommended teaching hours/week
    
    is_feasible = True
    
    # --- Faculty Supply vs Demand ---
    for sub in data.subjects:
        total_demand = sum(data.hours[sec].get(sub, 0) for sec in data.sections)
        qualified_profs = data.competencies.get(sub, [])
        total_supply = len(qualified_profs) * max_faculty_load
        
        status = "✅" if total_demand <= total_supply else "❌"
        print(f"{status} [{sub:<20}] Demand: {total_demand:>3} hrs | Supply: {total_supply:>3} hrs")
        
        if total_demand > total_supply:
            is_feasible = False

    # --- Room Supply vs Demand ---
    # THEORY: Calculate total slots needed across ALL sections
    total_theory_demand = sum(
        data.hours[s_name][subj] 
        for s_name in data.sections 
        for subj in data.hours[s_name] 
        if data.subject_types[subj] == "THEORY"
    )
    theory_rooms_count = len([r for r in data.rooms if data.room_types[r] == "THEORY"])
    theory_capacity = theory_rooms_count * total_slots_in_week
    
    # LABS: Calculate total slots needed (Credits * 2 because duration=2)
    total_lab_demand = sum(
        data.hours[s_name][subj] * 2 
        for s_name in data.sections 
        for subj in data.hours[s_name] 
        if data.subject_types[subj] == "LAB"
    )
    lab_rooms_count = len([r for r in data.rooms if data.room_types[r] == "LAB"])
    lab_capacity = lab_rooms_count * total_slots_in_week

    print(f"\n🏠 [THEORY ROOMS] Demand: {total_theory_demand:>4} slots | Capacity: {theory_capacity:>4}")
    print(f"🔬 [LAB ROOMS]    Demand: {total_lab_demand:>4} slots | Capacity: {lab_capacity:>4}")

    if total_theory_demand > theory_capacity or total_lab_demand > lab_capacity:
        print("❌ ALERT: Room shortage detected for the week.")
        is_feasible = False
    else:
        print("✅ Room capacity is sufficient.")

    print("═"*60)
    return is_feasible

def print_faculty_workload_report(data: MinimalData, solver, assign, fac_assign):
    print("\n" + "═"*50)
    print(" 👨‍🏫 FINAL FACULTY WORKLOAD REPORT ".center(50, "═"))
    print("═"*50)
    print(f"{'Faculty Name':<25} | {'Total Hours'}")
    print("-" * 50)
    
    workloads = {fac: 0 for fac in data.faculty}
    
    for (sec, sub, fac), var in fac_assign.items():
        if solver.Value(var) == 1:
            # Add total credits for this assignment
            workloads[fac] += data.hours[sec][sub]
            
    # Sort by busiest professors
    for fac, hrs in sorted(workloads.items(), key=lambda x: x[1], reverse=True):
        if hrs > 0:
            print(f"{fac:<25} | {hrs} hours/week")
            
    print("═"*50)

if __name__ == "__main__":
    data = create_real_gla_large_instance()
    if validate_gla_data(data):
        print("✅ Data looks mathematically sound. Starting Solver...")
        solve_minimal_timetable(data)
    else:
        print("🛑 FEASIBILITY ERROR: Fix the faculty/room bottlenecks listed above.")