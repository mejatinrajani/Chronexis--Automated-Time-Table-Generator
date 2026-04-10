
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, time, timedelta
from itertools import groupby
from typing import Dict, List, Optional, Set, Tuple

from ortools.sat.python import cp_model

@dataclass
class Slot:
    id: int
    day_index: int
    day_name: str
    slot_index: int
    start_time: time
    end_time: time
    duration_minutes: int


@dataclass
class TimetableData:
    sections: List[str]
    subjects: List[str]
    slots: List[Slot]
    faculty: List[str]
    rooms: List[str]
    room_types: Dict[str, str]              # room → "THEORY" | "LAB"
    subject_types: Dict[str, str]           # subject → "THEORY" | "LAB"
    subject_durations: Dict[str, int]       # subject → 1 (theory) | 2 (lab block)
    hours: Dict[str, Dict[str, int]]        # hours[sec][sub] = weekly sessions
    competencies: Dict[str, List[str]]      # subject → [faculty names]
    faculty_sections: Dict[str, List[str]]  # faculty → allowed sections ([] = all)
    unavailability: Dict[str, Set[int]]     # faculty → {slot_id (1-based), ...}
    lab_subgroups: Dict[str, List[str]]     # section → [sub-section labels]
    scheduling_style: str = "BALANCED"

def _snap_half(dt: datetime) -> datetime:
    m = dt.minute
    if m < 15:   return dt.replace(minute=0,  second=0, microsecond=0)
    elif m < 45: return dt.replace(minute=30, second=0, microsecond=0)
    else:        return (dt + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)


def calculate_lunch_break(shift_start: time, shift_end: time,
                           duration_minutes: int = 60) -> Tuple[time, time]:
    d = datetime(2000, 1, 1)
    s = datetime.combine(d, shift_start)
    e = datetime.combine(d, shift_end)
    mid = s + (e - s) / 2
    earliest = datetime.combine(d, time(12, 0))
    ls = _snap_half(max(mid - timedelta(minutes=duration_minutes / 2), earliest))
    return ls.time(), (ls + timedelta(minutes=duration_minutes)).time()


def generate_time_slots(
    working_days: List[int],
    day_names: List[str],
    shift_start: time,
    shift_end: time,
    slot_duration_minutes: int = 50,
    break_periods: Optional[List[Tuple[time, time]]] = None,
) -> List[Slot]:
    break_periods = break_periods or []
    slots, gid = [], 1
    for day_idx in sorted(working_days):
        day_name = day_names[day_idx]
        now = datetime(2000, 1, 1, shift_start.hour, shift_start.minute)
        sidx = 0
        while True:
            end = now + timedelta(minutes=slot_duration_minutes)
            if end.time() > shift_end:
                break
            in_break = any(not (end.time() <= bs or now.time() >= be)
                           for bs, be in break_periods)
            if in_break:
                for bs, be in break_periods:
                    if now.time() < be:
                        now = datetime(2000, 1, 1, be.hour, be.minute)
                        break
                continue
            slots.append(Slot(id=gid, day_index=day_idx, day_name=day_name,
                              slot_index=sidx, start_time=now.time(),
                              end_time=end.time(), duration_minutes=slot_duration_minutes))
            gid += 1; sidx += 1; now = end
    return slots
def check_feasibility(data: TimetableData) -> Tuple[bool, str]:
    num_slots   = len(data.slots)
    slot_to_day = [s.day_index for s in data.slots]

    for dur in set(data.subject_durations.values()) | {1}:
        vs = [s for s in range(num_slots - dur + 1)
              if slot_to_day[s] == slot_to_day[s + dur - 1]
              and (dur < 2 or data.slots[s].end_time == data.slots[s + 1].start_time)]
        if not vs:
            return False, f"No valid consecutive slots for duration={dur}."

    for sec in data.sections:
        needed = sum(data.subject_durations.get(sub, 1) * c
                     for sub, c in data.hours[sec].items())
        if needed > num_slots:
            return False, f"Section '{sec}' needs {needed} slot-units, only {num_slots} exist."

    for sub in data.subjects:
        if not data.competencies.get(sub):
            return False, f"Subject '{sub}' has no assigned faculty."
        sub_type = data.subject_types.get(sub, "THEORY")
        if not any(data.room_types.get(r) == sub_type for r in data.rooms):
            return False, f"Subject '{sub}' needs room type '{sub_type}' — none available."

    # Faculty load check (sole-teacher case)
    t_load: Dict[str, int] = defaultdict(int)
    for sec in data.sections:
        n_sg = len(data.lab_subgroups.get(sec) or [""])
        for sub, count in data.hours[sec].items():
            is_lab = data.subject_types.get(sub) == "LAB"
            teachers = [t for t in data.competencies.get(sub, [])
                        if not data.faculty_sections.get(t)
                        or sec in data.faculty_sections[t]]
            # Labs: need n_sg teachers simultaneously
            needed_teachers = n_sg if is_lab else 1
            if len(teachers) < needed_teachers:
                return (False,
                        f"Subject '{sub}' for section '{sec}' needs {needed_teachers} "
                        f"simultaneous teachers (for subgroups) but only {len(teachers)} qualified.")
    for t, l in t_load.items():
        avail = num_slots - len(data.unavailability.get(t, set()))
        if l > avail:
            return False, f"Teacher '{t}' load {l} > available {avail} slots."

    # Room capacity check
    type_load: Dict[str, int] = defaultdict(int)
    type_cap:  Dict[str, int] = defaultdict(int)
    for r, rt in data.room_types.items():
        type_cap[rt] += num_slots
    for sec in data.sections:
        n_sg = len(data.lab_subgroups.get(sec) or [""])
        for sub, count in data.hours[sec].items():
            rt  = data.subject_types.get(sub, "THEORY")
            dur = data.subject_durations.get(sub, 1)
            mult = n_sg if rt == "LAB" else 1
            type_load[rt] += dur * count * mult
    for rt, load in type_load.items():
        if load > type_cap[rt]:
            return False, (f"Room type '{rt}': demand {load} > capacity {type_cap[rt]}. "
                           f"Add more {rt} rooms.")

    return True, ""

def preassign_resources(
    data: TimetableData,
) -> Tuple[Dict[Tuple[str, str, str], str], Dict[Tuple[str, str, str], str]]:
    """
    Returns:
      teacher_map[(sec, sub, sg)] → faculty name   (sg="" for theory)
      room_map   [(sec, sub, sg)] → room name       (sg="" for theory)
    """
    teacher_map: Dict[Tuple[str, str, str], str] = {}
    t_load: Dict[str, int] = defaultdict(int)

    rooms_by_type: Dict[str, List[str]] = defaultdict(list)
    for r in data.rooms:
        rooms_by_type[data.room_types[r]].append(r)
    room_map: Dict[Tuple[str, str, str], str] = {}
    r_ctr: Dict[str, int] = defaultdict(int)

    for sub in data.subjects:
        is_lab   = data.subject_types.get(sub) == "LAB"
        sub_type = data.subject_types.get(sub, "THEORY")
        avail_rooms = rooms_by_type.get(sub_type, [])

        for sec in sorted(data.sections):
            if is_lab:
                subgroups = data.lab_subgroups.get(sec) or [""]
            else:
                subgroups = [""]

            for sg in subgroups:
                candidates = [
                    t for t in data.competencies.get(sub, [])
                    if not data.faculty_sections.get(t)
                       or sec in data.faculty_sections[t]
                ]
                if not candidates:
                    candidates = data.competencies.get(sub, [])
                if candidates:
                    chosen_t = min(candidates, key=lambda t: t_load[t])
                    teacher_map[(sec, sub, sg)] = chosen_t
                    t_load[chosen_t] += (data.subject_durations.get(sub, 1)
                                         * data.hours[sec].get(sub, 0))

                # Room: round-robin
                if avail_rooms:
                    room_map[(sec, sub, sg)] = avail_rooms[r_ctr[sub_type] % len(avail_rooms)]
                    r_ctr[sub_type] += 1

    return teacher_map, room_map


class OnDayCache:
    """Memoised indicator: starts[inst_idx] is on `day` for a given duration."""

    def __init__(self, model: cp_model.CpModel, starts: list,
                 valid_by_day_dur: Dict, max_slot: int):
        self._m = model; self._s = starts
        self._vbdd = valid_by_day_dur; self._max = max_slot
        self._cache: Dict = {}

    def get(self, inst: int, day: int, dur: int):
        key = (inst, day, dur)
        if key in self._cache:
            return self._cache[key]

        dv = self._vbdd.get((day, dur))
        b  = self._m.NewBoolVar(f"od_{inst}_{day}_{dur}")
        if not dv:
            self._m.Add(b == 0)
            self._cache[key] = b
            return b

        lo, hi = min(dv), max(dv)
        start  = self._s[inst]
        self._m.Add(start >= lo).OnlyEnforceIf(b)
        self._m.Add(start <= hi).OnlyEnforceIf(b)

        can_bel = lo > 0
        can_abv = hi < self._max
        if can_bel and can_abv:
            bb = self._m.NewBoolVar(f"od_{inst}_{day}_{dur}_b")
            ba = self._m.NewBoolVar(f"od_{inst}_{day}_{dur}_a")
            self._m.Add(start <= lo - 1).OnlyEnforceIf(bb)
            self._m.Add(start >= hi + 1).OnlyEnforceIf(ba)
            self._m.AddBoolOr([bb, ba]).OnlyEnforceIf(b.Not())
        elif can_bel:
            self._m.Add(start <= lo - 1).OnlyEnforceIf(b.Not())
        elif can_abv:
            self._m.Add(start >= hi + 1).OnlyEnforceIf(b.Not())
        else:
            self._m.Add(b == 1)

        self._cache[key] = b
        return b

def run_solver_internal(data: TimetableData) -> List[dict]:
    print("Running feasibility checks…")
    ok, reason = check_feasibility(data)
    if not ok:
        print(f" {reason}"); return []
    print("Feasibility passed.\n")

    teacher_map, room_map = preassign_resources(data)
    print("Resources pre-assigned.\n")

    num_slots   = len(data.slots)
    slot_to_day = [s.day_index for s in data.slots]
    id_to_idx   = {s.id: i for i, s in enumerate(data.slots)}
    unique_days = sorted(set(slot_to_day))
    spd         = sum(1 for s in data.slots if s.day_index == unique_days[0])
    max_slot    = num_slots - 1


    fac_unavail: Dict[str, Set[int]] = {
        fac: {id_to_idx[sid] for sid in bad if sid in id_to_idx}
        for fac, bad in data.unavailability.items()
    }


    valid_by_dur: Dict[int, List[int]] = {}
    for dur in set(data.subject_durations.values()) | {1}:
        valid_by_dur[dur] = [
            s for s in range(num_slots - dur + 1)
            if slot_to_day[s] == slot_to_day[s + dur - 1]
            and (dur < 2 or data.slots[s].end_time == data.slots[s + 1].start_time)
        ]

    valid_by_day_dur: Dict[Tuple[int, int], List[int]] = {}
    for dur, vs in valid_by_dur.items():
        for day in unique_days:
            vd = [s for s in vs if slot_to_day[s] == day]
            if vd:
                valid_by_day_dur[(day, dur)] = vd

    day_range_theory: Dict[int, Tuple[int, int]] = {
        day: (min(v), max(v))
        for day in unique_days
        if (v := valid_by_day_dur.get((day, 1)))
    }

    instances: List[dict] = []

    linked_groups: List[List[int]] = []

    for sec in data.sections:
        subgroups_lab = data.lab_subgroups.get(sec) or [""]
        for sub, count in data.hours[sec].items():
            dur    = data.subject_durations.get(sub, 1)
            is_lab = data.subject_types.get(sub) == "LAB"

            if is_lab:
                for ci in range(count):
                    group_idxs = []
                    for sg in subgroups_lab:
                        instances.append(dict(
                            sec=sec, sub=sub, dur=dur, is_lab=True,
                            teacher=teacher_map.get((sec, sub, sg), ""),
                            room=room_map.get((sec, sub, sg), ""),
                            subgroup=sg, credit_idx=ci, total_credits=count,
                        ))
                        group_idxs.append(len(instances) - 1)
                    if len(group_idxs) > 1:
                        linked_groups.append(group_idxs)
            else:
                for ci in range(count):
                    instances.append(dict(
                        sec=sec, sub=sub, dur=dur, is_lab=False,
                        teacher=teacher_map.get((sec, sub, ""), ""),
                        room=room_map.get((sec, sub, ""), ""),
                        subgroup="", credit_idx=ci, total_credits=count,
                    ))

    n = len(instances)
    print(f"Total instances: {n}  |  Linked lab groups: {len(linked_groups)}\n")


    model  = cp_model.CpModel()
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds    = 100
    solver.parameters.num_search_workers     = 16
    solver.parameters.log_search_progress    = True
    solver.parameters.cp_model_presolve      = True
    solver.parameters.symmetry_level         = 2
    solver.parameters.linearization_level    = 2
    solver.parameters.cp_model_probing_level = 2

    starts:    List = []
    intervals: List = []

    for i, inst in enumerate(instances):
        dur = inst["dur"]
        fac = inst["teacher"]
        bad = fac_unavail.get(fac, set())
        forbidden: Set[int] = set()
        for b in bad:
            for offset in range(dur):
                forbidden.add(b - offset)
        allowed = [s for s in valid_by_dur[dur] if s not in forbidden]
        if not allowed:
            print(f" No valid slots for instance {i} "
                  f"({inst['sec']}/{inst['sub']}/{inst['subgroup']}) "
                  f"after faculty unavailability.")
            return []
        start = model.NewIntVarFromDomain(
            cp_model.Domain.FromValues(allowed), f"s_{i}")
        starts.append(start)
        intervals.append(model.NewIntervalVar(start, dur, start + dur, f"iv_{i}"))

    od = OnDayCache(model, starts, valid_by_day_dur, max_slot)

    print("Building H0 (linked lab subgroup sync)…")
    for grp in linked_groups:
        anchor = starts[grp[0]]
        for j in grp[1:]:
            model.Add(starts[j] == anchor)

    print("Building H1 (section no-overlap)…")
    sec_ivs: Dict[str, List] = defaultdict(list)
    for i, inst in enumerate(instances):
        sg = inst["subgroup"]
        if sg == "" or sg == (data.lab_subgroups.get(inst["sec"]) or [""])[0]:
            sec_ivs[inst["sec"]].append(intervals[i])
    for ivs in sec_ivs.values():
        model.AddNoOverlap(ivs)

    print("Building H2 (teacher no-overlap)…")
    tch_ivs: Dict[str, List] = defaultdict(list)
    for i, inst in enumerate(instances):
        if inst["teacher"]:
            tch_ivs[inst["teacher"]].append(intervals[i])
    for ivs in tch_ivs.values():
        if len(ivs) > 1:
            model.AddNoOverlap(ivs)

    print("Building H3 (room no-overlap)…")
    rom_ivs: Dict[str, List] = defaultdict(list)
    for i, inst in enumerate(instances):
        if inst["room"]:
            rom_ivs[inst["room"]].append(intervals[i])
    for ivs in rom_ivs.values():
        if len(ivs) > 1:
            model.AddNoOverlap(ivs)

    print("Building H4 (intra-subject ordering)…")

    def kf(idx):
        return (instances[idx]["sec"], instances[idx]["sub"], instances[idx]["subgroup"])

    sec_sub_sg: Dict[Tuple, List[int]] = defaultdict(list)
    for i in sorted(range(n), key=kf):
        sec_sub_sg[kf(i)].append(i)

    for grp in sec_sub_sg.values():
        for a, b in zip(grp, grp[1:]):
            model.Add(starts[a] <= starts[b])

    sec_sub_grp: Dict[Tuple[str, str], List[int]] = {}
    for (sec, sub, sg), grp in sec_sub_sg.items():
        first_sg = (data.lab_subgroups.get(sec) or [""])[0]
        if sg in ("", first_sg):
            sec_sub_grp[(sec, sub)] = grp

    print("Building H5 (max 2 same-subject/day)…")
    h5_count = 0
    for (sec, sub), grp in sec_sub_grp.items():
        if len(grp) < 3:
            continue
        dur = instances[grp[0]]["dur"]
        for day in unique_days:
            if not valid_by_day_dur.get((day, dur)):
                continue
            b0 = od.get(grp[0], day, dur)
            for k in range(2, len(grp)):
                bk = od.get(grp[k], day, dur)
                model.Add(b0 + bk <= 1)
                h5_count += 1
    print(f"  H5 constraints: {h5_count}")

    print("Building H6 (lab sessions on different days)…")
    h6_count = 0
    for (sec, sub), grp in sec_sub_grp.items():
        if not instances[grp[0]]["is_lab"] or len(grp) < 2:
            continue
        dur = instances[grp[0]]["dur"]
        for a_pos, i0 in enumerate(grp):
            for i1 in grp[a_pos + 1:]:
                for day in unique_days:
                    if not valid_by_day_dur.get((day, dur)):
                        continue
                    b0 = od.get(i0, day, dur)
                    b1 = od.get(i1, day, dur)
                    model.Add(b0 + b1 <= 1)
                    h6_count += 1
    print(f"  H6 constraints: {h6_count}")

    print("Building H7 (theory cap ≤ 6/day)…")
    MAX_THEORY = 6
    h7_count   = 0
    sec_theory: Dict[str, List[int]] = defaultdict(list)
    for i, inst in enumerate(instances):
        if not inst["is_lab"] and inst["subgroup"] == "":
            sec_theory[inst["sec"]].append(i)
    for sec, grp in sec_theory.items():
        if len(grp) <= MAX_THEORY:
            continue
        for day in unique_days:
            if not day_range_theory.get(day):
                continue
            for si in range(len(grp) - MAX_THEORY):
                bf = od.get(grp[si],              day, 1)
                bl = od.get(grp[si + MAX_THEORY], day, 1)
                model.Add(bf + bl <= 1)
                h7_count += 1
    print(f"  H7 constraints: {h7_count}")

    print("\nBuilding soft objective…")
    PENALTY_MIN3   = 20
    PENALTY_GAP    = 12
    PENALTY_SPREAD =  8
    PENALTY_LOAD   =  5
    BIG            = num_slots + 1
    obj_terms      = []

    def is_rep(i: int) -> bool:
        sg = instances[i]["subgroup"]
        return sg == "" or sg == (data.lab_subgroups.get(instances[i]["sec"]) or [""])[0]

    for sec in data.sections:
        sec_inst  = [i for i in range(n) if instances[i]["sec"] == sec and is_rep(i)]
        ideal     = max(1, len(sec_inst) // len(unique_days))

        for day in unique_days:
            can_be = [i for i in sec_inst
                      if valid_by_day_dur.get((day, instances[i]["dur"]))]
            if not can_be:
                continue

            sbools = [od.get(i, day, instances[i]["dur"]) for i in can_be]
            cnt    = model.NewIntVar(0, len(can_be), f"cnt_{sec}_{day}")
            model.Add(cnt == sum(sbools))

            any_on = model.NewBoolVar(f"any_{sec}_{day}")
            model.Add(sum(sbools) >= 1).OnlyEnforceIf(any_on)
            model.Add(sum(sbools) == 0).OnlyEnforceIf(any_on.Not())

            sh = model.NewIntVar(0, 3, f"sh_{sec}_{day}")
            model.Add(sh + cnt >= 3).OnlyEnforceIf(any_on)
            model.Add(sh == 0).OnlyEnforceIf(any_on.Not())
            obj_terms.append(sh * PENALTY_MIN3)

            ov = model.NewIntVar(0, len(can_be), f"ov_{sec}_{day}")
            model.Add(ov >= cnt - (ideal + 1))
            obj_terms.append(ov * PENALTY_SPREAD)
            if ideal >= 2:
                un = model.NewIntVar(0, len(can_be), f"un_{sec}_{day}")
                model.Add(un + cnt >= ideal - 1).OnlyEnforceIf(any_on)
                model.Add(un == 0).OnlyEnforceIf(any_on.Not())
                obj_terms.append(un * PENALTY_SPREAD)

            th_here = [i for i in can_be if not instances[i]["is_lab"]]
            if len(th_here) > 5:
                el = model.NewIntVar(0, 6, f"el_{sec}_{day}")
                model.Add(el >= sum(od.get(i, day, 1) for i in th_here) - 5)
                obj_terms.append(el * PENALTY_LOAD)

            if len(can_be) < 3:
                continue

            ea = model.NewIntVar(0, num_slots, f"ea_{sec}_{day}")
            la = model.NewIntVar(0, num_slots, f"la_{sec}_{day}")
            td = model.NewIntVar(0, spd * 2,   f"td_{sec}_{day}")

            for i in can_be:
                dur = instances[i]["dur"]
                b   = od.get(i, day, dur)
                model.Add(ea <= starts[i] + BIG - BIG * b)
                model.Add(la >= starts[i] + dur - BIG + BIG * b)

            model.Add(td == sum(instances[i]["dur"] * od.get(i, day, instances[i]["dur"])
                                for i in can_be))

            sp  = model.NewIntVar(0, spd + 2, f"sp_{sec}_{day}")
            gp  = model.NewIntVar(0, spd + 2, f"gp_{sec}_{day}")
            gx  = model.NewIntVar(0, spd + 2, f"gx_{sec}_{day}")
            model.Add(sp == la - ea).OnlyEnforceIf(any_on)
            model.Add(sp == 0).OnlyEnforceIf(any_on.Not())
            model.Add(gp == sp - td).OnlyEnforceIf(any_on)
            model.Add(gp == 0).OnlyEnforceIf(any_on.Not())
            model.Add(gx >= gp - 2)
            obj_terms.append(gx * PENALTY_GAP)

    print(f"  Objective terms: {len(obj_terms)}")
    model.Minimize(sum(obj_terms))

    print("\nStarting CP-SAT solver…")
    status = solver.Solve(model)

    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        print("No solution found within time limit.")
        return []

    print(f"\n{solver.StatusName(status)}"
          f"  |  Objective: {solver.ObjectiveValue():.0f}"
          f"  |  Wall time: {solver.WallTime():.1f}s")

    output = []
    for i, inst in enumerate(instances):
        s       = solver.Value(starts[i])
        s_slot  = data.slots[s]
        e_slot  = data.slots[s + inst["dur"] - 1]
        output.append({
            "section":       inst["sec"],
            "subgroup":      inst["subgroup"] if inst["subgroup"] else inst["sec"],
            "subject":       inst["sub"],
            "day":           s_slot.day_name,
            "start_time":    s_slot.start_time.strftime("%H:%M"),
            "end_time":      e_slot.end_time.strftime("%H:%M"),
            "teacher":       inst["teacher"],
            "room":          inst["room"],
            "duration":      inst["dur"],
            "is_lab":        inst["is_lab"],
            "credit_idx":    inst["credit_idx"],
            "total_credits": inst["total_credits"],
        })
    return output


def solve_timetable(json_data: dict) -> List[dict]:
    """
    json_data keys:
      start_time        : "HH:MM"
      end_time          : "HH:MM"
      slot_duration     : int minutes (default 50)
      working_days      : [0..4] (default [0,1,2,3,4])
      day_names         : list[str]
      sections          : list[str]
      subjects          : list[{name, is_lab, credits}]
      faculty           : list[{
                            name,
                            subjects: [sub_name, ...],
                            sections: [sec_name, ...]  (optional, empty=all),
                            unavailable_slots: [slot_id, ...]  (optional, 1-based)
                          }]
      rooms             : list[{block, start, end}]
      lab_subgroups     : {section: [sg1, sg2, sg3], ...}  (optional)
    """
    sh, sm = map(int, json_data["start_time"].split(":"))
    eh, em = map(int, json_data["end_time"].split(":"))
    shift_start  = time(sh, sm)
    shift_end    = time(eh, em)
    slot_dur     = json_data.get("slot_duration", 50)
    working_days = json_data.get("working_days", [0, 1, 2, 3, 4])
    day_names    = json_data.get("day_names",
                                 ["Monday","Tuesday","Wednesday","Thursday","Friday"])

    lunch_s, lunch_e = calculate_lunch_break(shift_start, shift_end)
    slots = generate_time_slots(
        working_days=working_days, day_names=day_names,
        shift_start=shift_start, shift_end=shift_end,
        slot_duration_minutes=slot_dur,
        break_periods=[(lunch_s, lunch_e)],
    )
    print(f"  Generated {len(slots)} time slots  "
          f"(lunch: {lunch_s.strftime('%H:%M')}–{lunch_e.strftime('%H:%M')})")

    subjects          = [s["name"] for s in json_data["subjects"]]
    subject_types     = {s["name"]: ("LAB" if s.get("is_lab") else "THEORY")
                         for s in json_data["subjects"]}
    subject_durations = {s["name"]: (2 if s.get("is_lab") else 1)
                         for s in json_data["subjects"]}

    faculty_list     = [f["name"] for f in json_data["faculty"]]
    competencies:     Dict[str, List[str]] = {sub: [] for sub in subjects}
    faculty_sections: Dict[str, List[str]] = {}
    unavailability:   Dict[str, Set[int]]  = {}

    for fac in json_data["faculty"]:
        fname = fac["name"]
        for sub in fac.get("subjects", []):
            if sub in competencies:
                competencies[sub].append(fname)
        if fac.get("sections"):
            faculty_sections[fname] = fac["sections"]
        if fac.get("unavailable_slots"):
            unavailability[fname] = set(fac["unavailable_slots"])

    rooms: List[str] = []
    room_types: Dict[str, str] = {}
    for rb in json_data["rooms"]:
        is_lab_block = "LAB" in rb["block"].upper()
        for rnum in range(rb["start"], rb["end"] + 1):
            rn = f"{rb['block']}-{rnum}"
            rooms.append(rn)
            room_types[rn] = "LAB" if is_lab_block else "THEORY"

    lab_subgroups: Dict[str, List[str]] = dict(json_data.get("lab_subgroups", {}))

    sections   = json_data["sections"]
    user_hours = {sec: {s["name"]: s["credits"] for s in json_data["subjects"]}
                  for sec in sections}

    data = TimetableData(
        sections=sections, subjects=subjects, slots=slots,
        faculty=faculty_list, rooms=rooms, room_types=room_types,
        subject_types=subject_types, subject_durations=subject_durations,
        hours=user_hours, competencies=competencies,
        faculty_sections=faculty_sections, unavailability=unavailability,
        lab_subgroups=lab_subgroups,
    )

    return run_solver_internal(data)

def solve_custom_timetable(json_data: dict) -> List[dict]:
    """
    Wrapper to match API expectations.
    """
    return solve_timetable(json_data)

def _build_stress_test_disabled(num_sections: int = 15) -> dict:
    import math, random
    random.seed(42)

    N    = num_sections
    N_SG = 3

    def sec_label(i: int) -> str:
        alpha = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        return alpha[i] if i < 26 else alpha[i // 26 - 1] + alpha[i % 26]

    sections = [sec_label(i) for i in range(N)]

    subjects = [
        {"name": "Maths",       "is_lab": False, "credits": 4},
        {"name": "Physics",     "is_lab": False, "credits": 3},
        {"name": "Chemistry",   "is_lab": False, "credits": 3},
        {"name": "English",     "is_lab": False, "credits": 2},
        {"name": "DS",          "is_lab": False, "credits": 3},
        {"name": "OOP",         "is_lab": False, "credits": 3},
        {"name": "Physics Lab", "is_lab": True,  "credits": 2},
        {"name": "Chem Lab",    "is_lab": True,  "credits": 2},
        {"name": "DS Lab",      "is_lab": True,  "credits": 1},
    ]
    theory_subs = [s["name"] for s in subjects if not s["is_lab"]]
    lab_subs    = [s["name"] for s in subjects if s["is_lab"]]

    total_theory = sum(s["credits"] for s in subjects if not s["is_lab"])
    total_lab    = sum(s["credits"] for s in subjects if s["is_lab"])
    print(f"[stress] {N} sections | theory credits/sec={total_theory} | "
          f"lab credits/sec={total_lab} (×{N_SG} subgroups)")

    lab_subgroups = {sec: [f"{sec}{j+1}" for j in range(N_SG)] for sec in sections}

    n_theory_rooms = max(1, math.floor(0.8 * N))
    n_lab_rooms    = max(N_SG, math.floor(0.8 * N * N_SG))
    print(f"[stress] theory rooms={n_theory_rooms}/{N} | "
          f"lab rooms={n_lab_rooms}/{N*N_SG}  (0.8× budget)")

    rooms = [
        {"block": "THEORY", "start": 101, "end": 100 + n_theory_rooms},
        {"block": "LAB",    "start":   1, "end": n_lab_rooms},
    ]

    faculty  = []
    fac_idx  = [0]

    def new_teacher(subjects_list, allowed_sections, unavail=None):
        tid   = fac_idx[0]; fac_idx[0] += 1
        sub0  = subjects_list[0]
        prefix = "L" if not allowed_sections and any(
            s["name"] == sub0 and s["is_lab"]
            for s in subjects) else "T"
        name  = f"{prefix}_{sub0[:3]}_{tid:03d}"
        entry = {"name": name, "subjects": subjects_list, "sections": allowed_sections}
        if unavail:
            entry["unavailable_slots"] = unavail
        faculty.append(entry)

    BAND = 4
    for subj in theory_subs:
        for i in range(0, N, BAND):
            chunk = sections[i:i+BAND]
            unavail = [1, 2] if random.random() < 0.25 else None
            new_teacher([subj], list(chunk), unavail)

    BAND_LAB = 5
    for lsub in lab_subs:
        n_instr = N_SG * math.ceil(N / BAND_LAB)
        for _ in range(n_instr):
            unavail = [1, 2, 3] if random.random() < 0.20 else None
            new_teacher([lsub], [], unavail)

    n_theory_fac = sum(1 for f in faculty if f["name"].startswith("T_"))
    n_lab_fac    = sum(1 for f in faculty if f["name"].startswith("L_"))
    print(f"[stress] faculty={len(faculty)} "
          f"(theory={n_theory_fac} | lab={n_lab_fac})")

    return {
        "start_time":    "08:00",
        "end_time":      "18:00",
        "slot_duration": 60,
        "sections":      sections,
        "subjects":      subjects,
        "faculty":       faculty,
        "rooms":         rooms,
        "lab_subgroups": lab_subgroups,
    }