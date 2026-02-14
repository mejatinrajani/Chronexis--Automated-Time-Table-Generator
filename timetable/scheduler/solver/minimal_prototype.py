import os 
import sys
import django
import json
import pandas as pd
from pathlib import Path

# 1. FIX: Ensure project_root correctly points to the 'timetable' folder 
current_path = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_path, "../../"))
sys.path.append(project_root)   

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "timetable.settings")
django.setup()

# 2. FIX: Group all imports together AFTER django.setup()
from ortools.sat.python import cp_model
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from datetime import time, timedelta, datetime
from scheduler.slots.models import Slot

def generate_time_slots(
    working_days: List[int],
    day_names: List[str],
    shift_start: time,
    shift_end: time,
    slot_duration_minutes: int = 50, # Adjusted to match your college instance
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
        
        # FIX: Initialize current_time explicitly at the start of each day
        current_time = datetime.combine(current_date, shift_start)
        slot_index = 0

        while current_time.time() < shift_end:
            slot_end = current_time + timedelta(minutes=slot_duration_minutes)

            # FIX: Prevent slots from spilling over the shift_end
            if slot_end.time() > shift_end:
                break

            # Check if this slot overlaps with any break
            overlaps_break = False
            for break_start, break_end in break_periods:
                if not (slot_end.time() <= break_start or current_time.time() >= break_end):
                    overlaps_break = True
                    # FIX: If we hit a break, move the current_time to the end of that break
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

            # FIX: Always update current_time at the end of the loop
            current_time = slot_end + timedelta(minutes=buffer_minutes + min_slot_gap_minutes)

    return all_slots

@dataclass
class MinimalData:
    sections: List[str]
    subjects: List[str]
    slots: List[Slot]
    faculty: List[str]
    rooms: List[str]
    room_types: Dict[str, str]
    subject_types: Dict[str, str]    
    subject_durations: Dict[str, int]
    assignments: Dict[str, Dict[str, str]]
    hours: Dict[str, Dict[str, int]]
    scheduling_style: str

    @property
    def num_slots(self):
        return len(self.slots)


def build_timetable_dict(data, solver, assign, assign_room):
    timetable = {}

    slots_by_day = {}
    for idx, s in enumerate(data.slots):
        slots_by_day.setdefault(s.day_index, []).append(idx)

    for sec in data.sections:
        timetable[sec] = {}

        for day_idx, indices in slots_by_day.items():
            day_name = data.slots[indices[0]].day_name
            timetable[sec][day_name] = []

            for idx in indices:
                s = data.slots[idx]

                subject = None
                faculty = None
                room = None

                for sub in data.assignments[sec].keys():
                    if solver.Value(assign[(sec, sub, idx)]) == 1:
                        subject = sub
                        faculty = data.assignments[sec][sub]

                        valid_rooms = [
                            r for r in data.rooms
                            if data.room_types[r] == data.subject_types[sub]
                        ]
                        for r in valid_rooms:
                            if (sec, sub, r, idx) in assign_room and solver.Value(assign_room[(sec, sub, r, idx)]):
                                room = r
                                break
                        break

                timetable[sec][day_name].append({
                    "start_time": s.start_time.strftime("%H:%M"),
                    "end_time": s.end_time.strftime("%H:%M"),
                    "subject": subject or "FREE",
                    "faculty": faculty or None,
                    "room": room or None
                })

    return timetable


def export_timetable_json(timetable: dict, filename="timetable.json"):
    Path(filename).write_text(json.dumps(timetable, indent=4))
    print(f"JSON exported → {filename}")


def export_timetable_excel(timetable: dict, filename="timetable.xlsx"):
    with pd.ExcelWriter(filename, engine="openpyxl") as writer:
        for sec, days in timetable.items():
            rows = []

            for day, slots in days.items():
                for s in slots:
                    rows.append({
                        "Day": day,
                        "Start": s["start_time"],
                        "End": s["end_time"],
                        "Subject": s["subject"],
                        "Faculty": s["faculty"],
                        "Room": s["room"]
                    })

            df = pd.DataFrame(rows)
            df.to_excel(writer, sheet_name=sec, index=False)

    print(f"Excel exported → {filename}")


def calculate_lunch_break(shift_start: time, shift_end: time, duration_minutes: int = 60) -> List[Tuple[time, time]]:
    """
    Calculates a lunch break near the midpoint of the shift.
    Ensures lunch does not start before 12:00 PM.
    """
    # Convert times to datetime for calculation
    dummy_date = datetime(2000, 1, 1)
    start_dt = datetime.combine(dummy_date, shift_start)
    end_dt = datetime.combine(dummy_date, shift_end)
    
    # Find the mathematical midpoint
    total_seconds = (end_dt - start_dt).total_seconds()
    midpoint_dt = start_dt + timedelta(seconds=total_seconds / 2)
    
    # Rule: Lunch shouldn't start before 12:00 PM
    earliest_lunch = datetime.combine(dummy_date, time(12, 0))
    
    # Target lunch start is either the midpoint or 12:00 PM, whichever is later
    lunch_start_dt = max(midpoint_dt - timedelta(minutes=duration_minutes / 2), earliest_lunch)
    
    # Standardize to the nearest hour or half-hour for a "clean" schedule
    if lunch_start_dt.minute < 15:
        lunch_start_dt = lunch_start_dt.replace(minute=0)
    elif lunch_start_dt.minute < 45:
        lunch_start_dt = lunch_start_dt.replace(minute=30)
    else:
        lunch_start_dt = (lunch_start_dt + timedelta(hours=1)).replace(minute=0)

    lunch_end_dt = lunch_start_dt + timedelta(minutes=duration_minutes)
    
    return [(lunch_start_dt.time(), lunch_end_dt.time())]



def create_realistic_large_instance(style: str = "COMPACT") -> MinimalData:
    shift_start, shift_end = time(9, 0), time(17, 0)
    auto_breaks = calculate_lunch_break(shift_start, shift_end, duration_minutes=60)
    
    slots = generate_time_slots(
        working_days=[0, 1, 2, 3, 4],
        day_names=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
        shift_start=shift_start, shift_end=shift_end,
        slot_duration_minutes=50, break_periods=auto_breaks,
    )

    # 1. Rooms: 60 theory + 15 labs
    theory_rooms = [f"AB{b}-{100+i}" for b in [1, 2, 3] for i in range(1, 21)]
    lab_rooms = [f"LAB-{i:02d}" for i in range(1, 16)]
    rooms = theory_rooms + lab_rooms
    room_types = {r: "THEORY" for r in theory_rooms}
    room_types.update({r: "LAB" for r in lab_rooms})

    # 2. Harder Faculty Pool (50 teachers for 25 sections)
    faculty = [f"Professor {i}" for i in range(1, 51)]

    # 3. Subjects
    theory_subjects = ["OS", "DBMS", "CN", "DAA", "AI", "Math", "SE"]
    lab_subjects = ["OS Lab", "DBMS Lab", "CN Lab", "Python Lab"]
    
    subject_types = {s: "THEORY" for s in theory_subjects}
    subject_types.update({s: "LAB" for s in lab_subjects})
    subject_durations = {s: 1 for s in theory_subjects}
    subject_durations.update({s: 2 for s in lab_subjects})

    import string, random
    random.seed(42) # Consistent hard test
    sections = list(string.ascii_uppercase[:20])

    user_assignments, user_hours = {}, {}

    for sec in sections:
        # Hard requirement: 4 Theory + 2 Labs per section
        sec_theory = random.sample(theory_subjects, k=4)
        sec_labs = random.sample(lab_subjects, k=2)
        
        assignments, credits = {}, {}
        
        for sub in sec_theory:
            assignments[sub] = faculty[(hash(sec + sub)) % len(faculty)]
            credits[sub] = 3 # 3 sessions of 1 hour
        for sub in sec_labs:
            assignments[sub] = faculty[(hash(sec + sub)) % len(faculty)]
            credits[sub] = 2 # 2 sessions of 2 hours
            
        user_assignments[sec] = assignments
        user_hours[sec] = credits

    return MinimalData(
        sections=sections, subjects=theory_subjects + lab_subjects,
        slots=slots, faculty=faculty, rooms=rooms, room_types=room_types,
        subject_types=subject_types, subject_durations=subject_durations,
        assignments=user_assignments, hours=user_hours, scheduling_style=style
    )


def create_realistic_tiny_instance(style: str = "COMPACT") -> MinimalData:
    shift_start=time(9,0)
    shift_end=time(17,0)
    auto_breaks = calculate_lunch_break(shift_start, shift_end, duration_minutes=60)
    slots = generate_time_slots(
        working_days=[0,1,2,3,4],
        day_names=["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"],
        shift_start=shift_start,
        shift_end=shift_end,
        slot_duration_minutes=50,
        break_periods=auto_breaks,
        buffer_minutes=0,
    )
    blocks = ["AB1", "AB2", "AB3"]
    all_rooms = []
    for block in blocks:
        for i in range(1, 21):
            all_rooms.append(f"{block}-{100 + i}")

    # Use a small subset for our tiny instance to actually TEST the clash logic
    # If we have 3 sections and only 2 rooms, we can prove the solver works.
    # For now, let's give it 5 rooms to see if it spreads them out.
    test_rooms = all_rooms[:5]

    subject_durations = {
        "Math": 1, "English": 1, "Social": 1, "Programming": 2
    }

    subject_types = {
        "Math": "THEORY", "English": "THEORY", 
        "Social": "THEORY", "Programming": "LAB"
    }
    room_types = {
        "AB1-101": "THEORY", "AB1-102": "THEORY", "AB1-103": "THEORY",
        "LAB-01": "LAB", "LAB-02": "LAB", "AB1-105": "THEORY", "AB1-104": "THEORY"
    }
    rooms = list(room_types.keys())
    user_assignments = {
        "A": {"Math": "Dr. Nishant", "English": "Rahul G", "Social": "Priyanka G", "Programming": "Narendra Modi"},
        "B": {"Math": "Dr. Nishant", "English": "Rahul G", "Social": "Priyanka G", "Programming": "Narendra Modi"},
        "C": {"Math": "Mr. Amit",    "English": "Shekhar A", "Social": "Mahatma G", "Programming": "Sher Singh"},
    }

    user_hours = {
        "A": {"Math": 4, "English": 3, "Social": 3, "Programming": 3},
        "B": {"Math": 4, "English": 3, "Social": 3, "Programming": 3},
        "C": {"Math": 4, "English": 3, "Social": 3, "Programming": 3},
    }

    return MinimalData(
        sections=["A","B","C"],
        subjects=["Math", "English", "Social","Programming"],
        slots=slots,
        faculty=["Dr. Nishant", "Rahul G", "Mr. Amit", "Shekhar A", "Priyanka G", "Mahatma G", "Sher Singh", "Narendra Modi"],
        assignments=user_assignments,
        hours=user_hours,
        scheduling_style=style,
        subject_durations=subject_durations,
        subject_types=subject_types,
        room_types=room_types,
        rooms=rooms
    )

def solve_minimal_timetable(data: MinimalData):
    model = cp_model.CpModel()
    assign = {}
    is_start = {}
    assign_room = {}

    # --- 0. PRE-PROCESS DATA (CRITICAL FIX) ---
    slots_by_day = {}
    for idx, slot in enumerate(data.slots):
        if slot.day_index not in slots_by_day: 
            slots_by_day[slot.day_index] = []
        slots_by_day[slot.day_index].append(idx)

    # --- 1. Variables and Linking ---
    for sec in data.sections:
        for sub in data.assignments[sec].keys():
            sub_type = data.subject_types[sub]
            valid_rooms = [r for r in data.rooms if data.room_types[r] == sub_type]
            
            for slot_idx in range(data.num_slots):
                assign[(sec, sub, slot_idx)] = model.NewBoolVar(f"as_{sec}_{sub}_{slot_idx}")
                is_start[(sec, sub, slot_idx)] = model.NewBoolVar(f"st_{sec}_{sub}_{slot_idx}")
                
                for r in valid_rooms:
                    assign_room[(sec, sub, r, slot_idx)] = model.NewBoolVar(f"asr_{sec}_{sub}_{r}_{slot_idx}")
                
                # Link: Class at slot IF AND ONLY IF in exactly one valid room
                model.Add(assign[(sec, sub, slot_idx)] == sum(assign_room[(sec, sub, r, slot_idx)] for r in valid_rooms))

    # --- 2. Hard Constraints (Logic) ---
    for sec in data.sections:
        # A. One subject per section per slot
        for slot_idx in range(data.num_slots):
            model.AddAtMostOne(assign[(sec, sub, slot_idx)] for sub in data.assignments[sec].keys())

        # B. Weekly Hours and Continuity (Credit-Based Logic)
        for sub, credits in data.hours[sec].items():
            duration = data.subject_durations.get(sub, 1)
            
            # RULE: Credits = Number of Classes per week
            num_classes = credits
            model.Add(sum(is_start[(sec, sub, s)] for s in range(data.num_slots)) == num_classes)

            if duration == 2:   
                model.Add(sum(is_start[(sec, sub, s)] for s in range(data.num_slots)) == num_classes)
                # atomic continuity
                for s in range(data.num_slots):
                # total starts
                    if s == 0:
                        model.Add(assign[(sec, sub, s)] == is_start[(sec, sub, s)])

                    else:
                        # active if started here or previous slot
                        model.Add(assign[(sec, sub, s)] ==
                                  is_start[(sec, sub, s)] + is_start[(sec, sub, s-1)])
                # cannot start at last slot of day
                for day_idx, indices in slots_by_day.items():
                    last_slot = indices[-1]
                    model.Add(is_start[(sec, sub, last_slot)] == 0)

                # room continuity
                valid_rooms = [r for r in data.rooms if data.room_types[r] == data.subject_types[sub]]
                for s in range(data.num_slots - 1):
                    if data.slots[s].day_index == data.slots[s+1].day_index:
                    
                        for r in valid_rooms:
                            model.Add(assign_room[(sec, sub, r, s)] ==

                                      assign_room[(sec, sub, r, s+1)]
                            ).OnlyEnforceIf(is_start[(sec, sub, s)])


    # --- 3. Physical Resource Constraints ---
    # Faculty Clash
    for fac in data.faculty:
        for slot_idx in range(data.num_slots):
            fac_work = []
            for sec in data.sections:
                for sub, assigned_fac in data.assignments[sec].items():
                    if assigned_fac == fac:
                        fac_work.append(assign[(sec, sub, slot_idx)])
            if fac_work: model.AddAtMostOne(fac_work)

    # Room Clash
    for r in data.rooms:
        for slot_idx in range(data.num_slots):
            usage = [assign_room[(sec, sub, r, slot_idx)] 
                     for sec in data.sections 
                     for sub in data.assignments[sec].keys() 
                     if (sec, sub, r, slot_idx) in assign_room]
            if usage: model.AddAtMostOne(usage)

    # --- 4. Attendance & Style (Optimization) ---
    day_is_active = {}
    obj_vars = []
    for sec in data.sections:
        for day_idx, day_indices in slots_by_day.items():
            active = model.NewBoolVar(f"act_{sec}_{day_idx}")
            day_is_active[(sec, day_idx)] = active
            
            daily_count = sum(assign[(sec, sub, s)] for sub in data.assignments[sec].keys() for s in day_indices)
            model.Add(daily_count == 0).OnlyEnforceIf(active.Not())
            model.Add(daily_count >= 2).OnlyEnforceIf(active)
            
            # Penalize active days to encourage days off (Compact style)
            obj_vars.append(active * 100)

            # Penalize late slots and gaps
            for i, s_idx in enumerate(day_indices):
                for sub in data.assignments[sec].keys():
                    obj_vars.append(assign[(sec, sub, s_idx)] * (i * 20))

    model.Minimize(sum(obj_vars))

    # --- Solver Execution ---
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 60
    solver.parameters.num_search_workers = 8

    status = solver.Solve(model)

    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        print("\n" + "═"*60)
        print(" FINAL GENERATED TIMETABLE ".center(60, "═"))
        
        for sec in data.sections:
            print(f"\n» SECTION: {sec}")
            current_day_idx = -1
            
            # Map slots by day_index for easier lookup
            slots_by_day = {}
            for idx, s in enumerate(data.slots):
                if s.day_index not in slots_by_day:
                    slots_by_day[s.day_index] = []
                slots_by_day[s.day_index].append((idx, s))

            for day_idx in sorted(slots_by_day.keys()):
                day_slots = slots_by_day[day_idx]
                print(f"\n  [{day_slots[0][1].day_name.upper()}]")
                print(f"  {'Time Range':<20} | {'Status/Subject':<20} | {'Type'}")
                print(f"  {'-'*55}")

                # Tracking time to detect breaks
                # We assume the day starts at the first slot's start time
                last_time = day_slots[0][1].start_time

                for idx, s in day_slots:
                    if s.start_time > last_time:
                        print(f"  {last_time.strftime('%H:%M')} - {s.start_time.strftime('%H:%M')} | [ LUNCH BREAK ]".ljust(43) + " | BREAK")

                    # 2. Check Assignment
                    assigned_subject = "[ FREE ]"
                    info_str = ""
                    
                    for sub in data.assignments[sec].keys():
                        if solver.Value(assign[(sec, sub, idx)]) == 1:
                            assigned_subject = sub
                            fac = data.assignments[sec][sub]
                            
                            # Identify which room was chosen
                            assigned_room = "Unknown"
                            # Filter valid rooms for this subject to avoid KeyError
                            sub_type = data.subject_types[sub]
                            valid_rooms = [r for r in data.rooms if data.room_types[r] == sub_type]
                            
                            for r in valid_rooms:
                                # Safe check: ensure the variable exists before accessing Value()
                                if (sec, sub, r, idx) in assign_room and solver.Value(assign_room[(sec, sub, r, idx)]) == 1:
                                    assigned_room = r
                                    break
                            
                            info_str = f"({fac}) @ {assigned_room}"
                            break
                    
                    print(f"  {s.start_time.strftime('%H:%M')} - {s.end_time.strftime('%H:%M')} | {assigned_subject:<15} {info_str:<35} | SLOT {s.slot_index}")
                    last_time = s.end_time
                timetable = build_timetable_dict(data, solver, assign, assign_room)

        export_timetable_json(timetable, "timetable.json")
        export_timetable_excel(timetable, "timetable.xlsx")
        print("\n" + "═"*60)
        return timetable

    else:
        print("Error: No feasible solution found.")
    

if __name__ == "__main__":
    data = create_realistic_large_instance()
    solve_minimal_timetable(data)   