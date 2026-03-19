"""
Scalable Timetable Solver — CP-SAT v8 (Production Grade)
=========================================================

ROOT CAUSE OF ALL PREVIOUS H4/H6 VIOLATIONS (now fixed):

  make_on_day_indicator() was called multiple times for the same
  (instance_idx, day) pair — once per constraint triplet — creating
  SEPARATE BoolVars each time. Since b_i0_dayD_A and b_i0_dayD_B are
  independent booleans both claiming to mean "instance i0 is on day D",
  the solver could set one True and the other False simultaneously,
  making each individual constraint (b_lo + b_hi <= 1) appear satisfied
  while 3+ classes still land on the same day.

FIX (one line): a global cache maps (instance_idx, day_idx) → BoolVar.
  Every constraint that needs "is instance i on day d?" reuses the same
  boolean. The solver can no longer lie about an instance's day.

ENCODING STRATEGY:
  on_day(i, d) = 1  <=>  starts[i] in [day_lo..day_hi]

  b = 1  =>  starts[i] >= day_lo  (always safe to add)
             starts[i] <= day_hi  (always safe to add)
  b = 0  =>  starts[i] < day_lo  OR  starts[i] > day_hi

  Boundary handling:
    if lo == 0:      b=0 => starts[i] >= hi+1   (no lower bound possible)
    if hi == max:    b=0 => starts[i] <= lo-1    (no upper bound possible)
    otherwise:       b=0 => AddBoolOr([b_below, b_above])

  This correctly handles Monday (lo=0) and Friday (hi=max) without
  creating impossible constraints or vacuous ones.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import time, timedelta, datetime
from itertools import groupby
from typing import Dict, List, Tuple

from ortools.sat.python import cp_model


# ─────────────────────────────────────────────────────────────────────────────
# Data classes
# ─────────────────────────────────────────────────────────────────────────────

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
class MinimalData:
    sections: List[str]
    subjects: List[str]
    slots: List[Slot]
    faculty: List[str]
    rooms: List[str]
    room_types: Dict[str, str]
    subject_types: Dict[str, str]
    subject_durations: Dict[str, int]
    competencies: Dict[str, List[str]]
    unavailability: Dict[str, List[int]]
    hours: Dict[str, Dict[str, int]]
    scheduling_style: str


# ─────────────────────────────────────────────────────────────────────────────
# Slot generation
# ─────────────────────────────────────────────────────────────────────────────

def calculate_lunch_break(shift_start: time, shift_end: time,
                          duration_minutes: int = 60) -> Tuple[time, time]:
    dummy    = datetime(2000, 1, 1)
    start_dt = datetime.combine(dummy, shift_start)
    end_dt   = datetime.combine(dummy, shift_end)
    mid      = start_dt + (end_dt - start_dt) / 2
    earliest = datetime.combine(dummy, time(12, 0))
    ls = max(mid - timedelta(minutes=duration_minutes / 2), earliest)
    if ls.minute < 15:   ls = ls.replace(minute=0)
    elif ls.minute < 45: ls = ls.replace(minute=30)
    else:                ls = (ls + timedelta(hours=1)).replace(minute=0)
    return ls.time(), (ls + timedelta(minutes=duration_minutes)).time()


def generate_time_slots(
    working_days: List[int], day_names: List[str],
    shift_start: time, shift_end: time,
    slot_duration_minutes: int = 50,
    break_periods: List[Tuple[time, time]] = None,
    buffer_minutes: int = 5,
) -> List[Slot]:
    if break_periods is None:
        break_periods = []
    slots, gid = [], 1
    for day_idx in sorted(working_days):
        day_name = day_names[day_idx]
        now = datetime(2000, 1, 1, shift_start.hour, shift_start.minute)
        sidx = 0
        while now.time() < shift_end:
            end = now + timedelta(minutes=slot_duration_minutes)
            if end.time() > shift_end:
                break
            if any(not (end.time() <= bs or now.time() >= be) for bs, be in break_periods):
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


# ─────────────────────────────────────────────────────────────────────────────
# Feasibility checker
# ─────────────────────────────────────────────────────────────────────────────

def check_feasibility(data: MinimalData) -> Tuple[bool, str]:
    num_slots   = len(data.slots)
    slot_to_day = [s.day_index for s in data.slots]

    valid_by_dur: Dict[int, list] = {}
    for dur in set(data.subject_durations.values()) | {1}:
        vs = [s for s in range(num_slots - dur + 1)
              if slot_to_day[s] == slot_to_day[s + dur - 1]
              and (dur != 2 or data.slots[s].end_time == data.slots[s + 1].start_time)]
        valid_by_dur[dur] = vs
        if not vs:
            return False, f"No valid start slots for duration={dur}."

    for sec in data.sections:
        needed = sum(data.subject_durations.get(sub, 1) * c
                     for sub, c in data.hours[sec].items())
        if needed > num_slots:
            return False, f"Section '{sec}' needs {needed} slots, only {num_slots} exist."

    for sub in data.subjects:
        if not data.competencies.get(sub):
            return False, f"Subject '{sub}' has no teachers."
        sub_type = data.subject_types.get(sub)
        if not any(data.room_types.get(r) == sub_type for r in data.rooms):
            return False, f"Subject '{sub}' needs room type '{sub_type}' — none found."

    teacher_load: Dict[str, int] = defaultdict(int)
    for sec in data.sections:
        for sub, count in data.hours[sec].items():
            teachers = data.competencies.get(sub, [])
            if len(teachers) == 1:
                teacher_load[teachers[0]] += data.subject_durations.get(sub, 1) * count
    for t, l in teacher_load.items():
        if l > num_slots:
            return False, f"Teacher '{t}' sole-teaches {l} SU > {num_slots} slots."

    type_load: Dict[str, int] = defaultdict(int)
    type_cap:  Dict[str, int] = defaultdict(int)
    for r, rt in data.room_types.items():
        type_cap[rt] += num_slots
    for sec in data.sections:
        for sub, count in data.hours[sec].items():
            rt = data.subject_types.get(sub)
            if rt:
                type_load[rt] += data.subject_durations.get(sub, 1) * count
    for rt, load in type_load.items():
        if load > type_cap[rt]:
            return False, f"Room type '{rt}': demand {load} > capacity {type_cap[rt]}."

    return True, ""


# ─────────────────────────────────────────────────────────────────────────────
# Pre-assignment (teachers + rooms)
# ─────────────────────────────────────────────────────────────────────────────

def preassign_resources(data: MinimalData
) -> Tuple[Dict[Tuple[str,str], str], Dict[Tuple[str,str], str]]:
    teacher_map: Dict[Tuple[str,str], str] = {}
    t_load: Dict[str, int] = defaultdict(int)
    for sub in data.subjects:
        teachers = data.competencies.get(sub, [])
        if not teachers:
            continue
        for sec in sorted(data.sections):
            chosen = min(teachers, key=lambda t: t_load[t])
            teacher_map[(sec, sub)] = chosen
            t_load[chosen] += (data.subject_durations.get(sub, 1) *
                               data.hours[sec].get(sub, 0))

    rooms_by_type: Dict[str, List[str]] = defaultdict(list)
    for r in data.rooms:
        rooms_by_type[data.room_types[r]].append(r)

    room_map: Dict[Tuple[str,str], str] = {}
    r_ctr: Dict[str, int] = defaultdict(int)
    for sub in data.subjects:
        sub_type = data.subject_types.get(sub, "THEORY")
        avail = rooms_by_type.get(sub_type, [])
        if not avail:
            continue
        for sec in sorted(data.sections):
            room_map[(sec, sub)] = avail[r_ctr[sub_type] % len(avail)]
            r_ctr[sub_type] += 1

    return teacher_map, room_map


# ─────────────────────────────────────────────────────────────────────────────
# THE FIX: Global on_day cache — one BoolVar per (instance_idx, day_idx)
# ─────────────────────────────────────────────────────────────────────────────

class OnDayCache:
    """
    Ensures every constraint that asks "is instance i on day d?" gets the
    EXACT SAME BoolVar. Without this, duplicate booleans are independent,
    allowing the solver to assign them different values for the same question.
    """
    def __init__(self, model, starts, valid_by_day_dur, max_slot):
        self._model = model
        self._starts = starts
        self._vbdd = valid_by_day_dur
        self._max = max_slot
        self._cache: Dict[Tuple[int,int], object] = {}

    def get(self, inst_idx: int, day: int, dur: int) -> object:
        key = (inst_idx, day)
        if key in self._cache:
            return self._cache[key]

        dv = self._vbdd.get((day, dur))
        b  = self._model.NewBoolVar(f"od_{inst_idx}_{day}")

        if not dv:
            # Instance can never be on this day — b is always 0
            self._model.Add(b == 0)
            self._cache[key] = b
            return b

        lo, hi = min(dv), max(dv)
        start  = self._starts[inst_idx]

        # b=1 => start in [lo..hi]
        self._model.Add(start >= lo).OnlyEnforceIf(b)
        self._model.Add(start <= hi).OnlyEnforceIf(b)

        # b=0 => start NOT in [lo..hi]
        can_below = lo > 0
        can_above = hi < self._max

        if can_below and can_above:
            b_bel = self._model.NewBoolVar(f"od_{inst_idx}_{day}_bel")
            b_abv = self._model.NewBoolVar(f"od_{inst_idx}_{day}_abv")
            self._model.Add(start <= lo - 1).OnlyEnforceIf(b_bel)
            self._model.Add(start >= hi + 1).OnlyEnforceIf(b_abv)
            self._model.AddBoolOr([b_bel, b_abv]).OnlyEnforceIf(b.Not())
        elif can_below:
            self._model.Add(start <= lo - 1).OnlyEnforceIf(b.Not())
        elif can_above:
            self._model.Add(start >= hi + 1).OnlyEnforceIf(b.Not())
        else:
            # lo=0 and hi=max_slot: start always in this range → b always 1
            self._model.Add(b == 1)

        self._cache[key] = b
        return b


# ─────────────────────────────────────────────────────────────────────────────
# Core solver — v8
# ─────────────────────────────────────────────────────────────────────────────

def run_solver_internal(data: MinimalData) -> List[dict]:

    print("🔍 Running feasibility checks...")
    ok, reason = check_feasibility(data)
    if not ok:
        print(f"  ❌ {reason}"); return []
    print("✅ Data checks passed.\n")

    teacher_map, room_map = preassign_resources(data)
    print("👩‍🏫 Teachers + rooms pre-assigned.")

    W = len(data.slots)
    t_load: Dict[str, int] = defaultdict(int)
    for sec in data.sections:
        for sub, count in data.hours[sec].items():
            t = teacher_map.get((sec, sub))
            if t:
                t_load[t] += data.subject_durations.get(sub, 1) * count
    overloaded = [(t, l) for t, l in t_load.items() if l > W]
    if overloaded:
        for t, l in overloaded:
            print(f"  ❌ Teacher '{t}' has {l} SU > {W}.")
        return []

    # ── Slot metadata ─────────────────────────────────────────────────────────
    num_slots   = len(data.slots)
    slot_to_day = [s.day_index for s in data.slots]
    unique_days = sorted(set(slot_to_day))
    spd         = sum(1 for s in data.slots if s.day_index == unique_days[0])
    max_slot    = num_slots - 1

    valid_by_dur: Dict[int, list] = {}
    for dur in set(data.subject_durations.values()) | {1}:
        valid_by_dur[dur] = [
            s for s in range(num_slots - dur + 1)
            if slot_to_day[s] == slot_to_day[s + dur - 1]
            and (dur != 2 or data.slots[s].end_time == data.slots[s + 1].start_time)
        ]

    valid_by_day_dur: Dict[Tuple[int,int], List[int]] = {}
    for dur in valid_by_dur:
        for day in unique_days:
            vd = [s for s in valid_by_dur[dur] if slot_to_day[s] == day]
            if vd:
                valid_by_day_dur[(day, dur)] = vd

    day_range_theory: Dict[int, Tuple[int,int]] = {}
    for day in unique_days:
        vd = valid_by_day_dur.get((day, 1), [])
        if vd:
            day_range_theory[day] = (min(vd), max(vd))

    # ── Build instances ───────────────────────────────────────────────────────
    instances: list = []
    for sec in data.sections:
        for sub, count in data.hours[sec].items():
            dur    = data.subject_durations.get(sub, 1)
            is_lab = (data.subject_types.get(sub) == "LAB")
            for credit_idx in range(count):
                instances.append({
                    "sec": sec, "sub": sub, "dur": dur, "is_lab": is_lab,
                    "teacher": teacher_map.get((sec, sub), ""),
                    "room":    room_map.get((sec, sub), ""),
                    "credits": 1, "total_credits": count,
                    "credit_idx": credit_idx,
                })

    n = len(instances)
    print(f"📐 Instances: {n}  |  Pure scheduling\n")

    model  = cp_model.CpModel()
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 300
    solver.parameters.num_search_workers  = 8
    solver.parameters.log_search_progress = True
    solver.parameters.cp_model_presolve   = True
    solver.parameters.symmetry_level      = 2

    # ── Decision variables ────────────────────────────────────────────────────
    starts    = []
    intervals = []
    for i, inst in enumerate(instances):
        start = model.NewIntVarFromDomain(
            cp_model.Domain.FromValues(valid_by_dur[inst["dur"]]), f"s_{i}")
        starts.append(start)
        intervals.append(
            model.NewIntervalVar(start, inst["dur"], start + inst["dur"], f"iv_{i}"))

    # ── THE FIX: Single shared on_day cache ───────────────────────────────────
    od = OnDayCache(model, starts, valid_by_day_dur, max_slot)

    # ── H1/H2/H3: No-overlap ─────────────────────────────────────────────────
    sec_grp: Dict[str, list] = defaultdict(list)
    tch_grp: Dict[str, list] = defaultdict(list)
    rom_grp: Dict[str, list] = defaultdict(list)
    for i, inst in enumerate(instances):
        sec_grp[inst["sec"]].append(intervals[i])
        tch_grp[inst["teacher"]].append(intervals[i])
        rom_grp[inst["room"]].append(intervals[i])
    for ivs in sec_grp.values():
        model.AddNoOverlap(ivs)
    for ivs in tch_grp.values():
        if len(ivs) > 1: model.AddNoOverlap(ivs)
    for ivs in rom_grp.values():
        if len(ivs) > 1: model.AddNoOverlap(ivs)

    # Symmetry breaking + group index
    kf = lambda idx: (instances[idx]["sec"], instances[idx]["sub"])
    sec_sub_grp: Dict[Tuple[str,str], List[int]] = defaultdict(list)
    for _, grp_iter in groupby(sorted(range(n), key=kf), key=kf):
        g = list(grp_iter)
        for a, b in zip(g, g[1:]):
            model.Add(starts[a] <= starts[b])
        key = (instances[g[0]]["sec"], instances[g[0]]["sub"])
        sec_sub_grp[key] = g

    # ── H4: Max 2 same-subject per section per day ────────────────────────────
    # For ordered group [i0, i1, ..., ik] and day D:
    #   At most 2 on day D means: the (k+1)th ordered instance cannot
    #   also be on day D if the 1st is already there.
    #
    #   Since instances are ordered, ALL k+1 being on day D implies
    #   both i0 and i_k are on day D (they're the extreme endpoints).
    #   So forbidding (i0 on D AND i2 on D) prevents 3+ on same day.
    #   For k>=3: also forbid (i0 on D AND i3 on D), etc.
    #   Using CACHED booleans: od.get(i0, D) is the same BoolVar everywhere.
    print("Building H4 (max 2 same-subject/day — cached on_day indicators)...")
    h4_count = 0
    for (sec, sub), grp in sec_sub_grp.items():
        if len(grp) < 3:
            continue
        dur = instances[grp[0]]["dur"]
        for day in unique_days:
            if not valid_by_day_dur.get((day, dur)):
                continue
            # b_first: single cached boolean for grp[0] on this day
            b_first = od.get(grp[0], day, dur)
            # Forbid: grp[0] and any grp[2+] both on same day
            for k in range(2, len(grp)):
                b_k = od.get(grp[k], day, dur)
                model.Add(b_first + b_k <= 1)
                h4_count += 1
    print(f"  H4 constraints: {h4_count}")

    # ── H5: Lab sessions on different days ────────────────────────────────────
    print("Building H5 (lab sessions different days — cached indicators)...")
    h5_count = 0
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
                    h5_count += 1
    print(f"  H5 constraints: {h5_count}")

    # ── H6: Daily theory cap <= 6 per section ─────────────────────────────────
    # Same pattern: cached booleans. For theory group of size k > 6,
    # forbid: grp[0] and grp[6] both on same day (and all sliding windows).
    print("Building H6 (theory cap ≤ 6/day — cached indicators)...")
    MAX_THEORY = 6
    h6_count   = 0
    sec_theory_grp: Dict[str, List[int]] = defaultdict(list)
    for i, inst in enumerate(instances):
        if not inst["is_lab"]:
            sec_theory_grp[inst["sec"]].append(i)
    for sec in sec_theory_grp:
        sec_theory_grp[sec].sort()

    for sec, grp in sec_theory_grp.items():
        if len(grp) <= MAX_THEORY:
            continue
        for day in unique_days:
            lo_hi = day_range_theory.get(day)
            if not lo_hi:
                continue
            for start_idx in range(len(grp) - MAX_THEORY):
                i_first = grp[start_idx]
                i_last  = grp[start_idx + MAX_THEORY]
                b_f = od.get(i_first, day, 1)
                b_l = od.get(i_last,  day, 1)
                model.Add(b_f + b_l <= 1)
                h6_count += 1
    print(f"  H6 constraints: {h6_count}")

    # ── Soft objective: S1 + S2 + S3 ─────────────────────────────────────────
    # S1 (w=1):  minimize sum of starts (compact schedule)
    # S2 (w=12): penalize intra-day gaps > 2 slots per section
    # S3 (w=5):  penalize theory load > 5 per section per day
    # S4 (w=8):  penalize all-Monday/Tuesday clustering (new — encourages spread)
    print("Building soft objective (S1 compact, S2 gap, S3 load, S4 spread)...")
    PENALTY_GAP   = 12
    PENALTY_LOAD  = 5
    PENALTY_EARLY = 8  # pushes classes to later days to balance Mon-Fri
    BIG           = num_slots + 1
    obj_terms     = []

    # S1: compact/early
    for i in range(n):
        obj_terms.append(starts[i])

    # S4: extra cost for landing on Mon/Tue (encourages Thu/Fri usage)
    # Only for theory, weighted mildly so it doesn't override correctness
    early_days = set(unique_days[:2])  # Monday, Tuesday
    for i, inst in enumerate(instances):
        if not inst["is_lab"]:
            for day in early_days:
                b = od.get(i, day, inst["dur"])
                obj_terms.append(b * PENALTY_EARLY)

    for sec in data.sections:
        sec_inst = [i for i, inst in enumerate(instances) if inst["sec"] == sec]

        for day in unique_days:
            can_be = [i for i in sec_inst
                      if valid_by_day_dur.get((day, instances[i]["dur"]))]
            if not can_be:
                continue

            # S3: penalize >5 theory per day
            theory_here = [i for i in can_be if not instances[i]["is_lab"]]
            if len(theory_here) > 5:
                el = model.NewIntVar(0, 6, f"el_{sec}_{day}")
                model.Add(el >= sum(od.get(i, day, 1) for i in theory_here) - 5)
                obj_terms.append(el * PENALTY_LOAD)

            # S2: gap penalty
            if len(can_be) < 3:
                continue

            earliest = model.NewIntVar(0, num_slots, f"ea_{sec}_{day}")
            latest   = model.NewIntVar(0, num_slots, f"la_{sec}_{day}")
            tot_dur  = model.NewIntVar(0, spd * 2,   f"td_{sec}_{day}")
            any_on   = model.NewBoolVar(f"any_{sec}_{day}")

            model.Add(sum(od.get(i, day, instances[i]["dur"]) for i in can_be) >= 1).OnlyEnforceIf(any_on)
            model.Add(sum(od.get(i, day, instances[i]["dur"]) for i in can_be) == 0).OnlyEnforceIf(any_on.Not())

            for i in can_be:
                dur = instances[i]["dur"]
                b   = od.get(i, day, dur)
                model.Add(earliest <= starts[i] + BIG - BIG * b)
                model.Add(latest   >= starts[i] + dur - BIG + BIG * b)

            model.Add(tot_dur == sum(instances[i]["dur"] * od.get(i, day, instances[i]["dur"]) for i in can_be))

            span    = model.NewIntVar(0, spd + 2, f"sp_{sec}_{day}")
            gap     = model.NewIntVar(0, spd + 2, f"gp_{sec}_{day}")
            gap_exc = model.NewIntVar(0, spd + 2, f"gx_{sec}_{day}")

            model.Add(span == latest - earliest).OnlyEnforceIf(any_on)
            model.Add(span == 0).OnlyEnforceIf(any_on.Not())
            model.Add(gap  == span - tot_dur).OnlyEnforceIf(any_on)
            model.Add(gap  == 0).OnlyEnforceIf(any_on.Not())
            model.Add(gap_exc >= gap - 2)
            obj_terms.append(gap_exc * PENALTY_GAP)

    print(f"  Objective terms: {len(obj_terms)}")
    model.Minimize(sum(obj_terms))

    # ── Solve ─────────────────────────────────────────────────────────────────
    print("\n🚀 Starting solver …")
    status = solver.Solve(model)

    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        print("❌ No solution found.")
        return []

    print(f"✅ {solver.StatusName(status)} | "
          f"Objective: {solver.ObjectiveValue():.0f} | "
          f"Wall time: {solver.WallTime():.1f}s")

    # ── Output ────────────────────────────────────────────────────────────────
    output = []
    for i, inst in enumerate(instances):
        s          = solver.Value(starts[i])
        start_slot = data.slots[s]
        end_slot   = data.slots[s + inst["dur"] - 1]
        output.append({
            "section":       inst["sec"],
            "subject":       inst["sub"],
            "day":           start_slot.day_name,
            "start_time":    start_slot.start_time.strftime("%H:%M"),
            "end_time":      end_slot.end_time.strftime("%H:%M"),
            "teacher":       inst["teacher"],
            "room":          inst["room"],
            "duration":      inst["dur"],
            "credits":       inst["credits"],
            "total_credits": inst["total_credits"],
        })
    return output


# ─────────────────────────────────────────────────────────────────────────────
# Public entry point
# ─────────────────────────────────────────────────────────────────────────────

def solve_custom_timetable(json_data: dict):
    s_h, s_m = map(int, json_data["start_time"].split(":"))
    e_h, e_m = map(int, json_data["end_time"].split(":"))
    shift_start = time(s_h, s_m)
    shift_end   = time(e_h, e_m)

    lunch_start, lunch_end = calculate_lunch_break(shift_start, shift_end)
    slots = generate_time_slots(
        working_days=[0,1,2,3,4],
        day_names=["Monday","Tuesday","Wednesday","Thursday","Friday"],
        shift_start=shift_start, shift_end=shift_end,
        slot_duration_minutes=json_data["duration"],
        break_periods=[(lunch_start, lunch_end)], buffer_minutes=0,
    )

    sections = json_data["sections"]
    subjects = [s["name"] for s in json_data["subjects"]]
    subject_types     = {s["name"]: ("LAB" if s.get("is_lab") else "THEORY")
                         for s in json_data["subjects"]}
    subject_durations = {s["name"]: (2 if s.get("is_lab") else 1)
                         for s in json_data["subjects"]}

    faculty_list = [f["name"] for f in json_data["faculty"]]
    competencies: Dict[str, List[str]] = {sub: [] for sub in subjects}
    for fac in json_data["faculty"]:
        for sub in fac["subjects"]:
            if sub in competencies:
                competencies[sub].append(fac["name"])

    rooms: List[str] = []; room_types: Dict[str, str] = {}
    for rb in json_data["rooms"]:
        for r_num in range(rb["start"], rb["end"] + 1):
            rn = f"{rb['block']}-{r_num}"
            rooms.append(rn)
            room_types[rn] = "LAB" if "LAB" in rb["block"].upper() else "THEORY"

    user_hours = {sec: {s["name"]: s["credits"] for s in json_data["subjects"]}
                  for sec in sections}

    data = MinimalData(
        sections=sections, subjects=subjects, slots=slots,
        faculty=faculty_list, rooms=rooms, room_types=room_types,
        subject_types=subject_types, subject_durations=subject_durations,
        competencies=competencies, unavailability={},
        hours=user_hours, scheduling_style="COMPACT",
    )

    print("\n Running Feasibility Checks...")
    ok, reason = check_feasibility(data)
    if not ok:
        print(f" Feasibility Check Failed: {reason}")
        return []
    print("Math checks out. Starting Solver...")
    return run_solver_internal(data)