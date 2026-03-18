import { SlotData } from "@/components/DraggableSlot";
import { APISlot } from "@/utils/dataMapper";

const DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"];
const SLOT_DURATION = 50;

type GridData = Record<string, Record<string, SlotData | null>>;

// --- Helpers (reuse same logic as dataMapper) ---
const parseTime = (t: string) => {
  if (!t) return 0;
  const [h, m] = t.split(":").map(Number);
  return h * 60 + m;
};

export const mapApiToTeacherGrid = (apiData: APISlot[]) => {
  const grids: Record<string, GridData> = {};
  const timeSet = new Set<string>();
  const teacherSet = new Set<string>();

  // 1️⃣ Collect teachers & time slots
  apiData.forEach((item) => {
    teacherSet.add(item.teacher);
    timeSet.add(item.start_time); // ✅ FIXED
  });

  const uniqueTeachers = Array.from(teacherSet).sort();

  // 2️⃣ Sort time slots (same as dataMapper)
  const sortedTimes = Array.from(timeSet).sort(
    (a, b) => parseTime(a) - parseTime(b)
  );

  // 3️⃣ Initialize grids
  uniqueTeachers.forEach((teacher) => {
    grids[teacher] = {};
    DAYS.forEach((day) => {
      grids[teacher][day] = {};
    });
  });

  // 🔥 4️⃣ PLACE DATA (HANDLE LABS / DURATION)
  apiData.forEach((item) => {
    const duration = item.duration || 1;
    const startIndex = sortedTimes.indexOf(item.start_time);

    for (let i = 0; i < duration; i++) {
      const timeKey = sortedTimes[startIndex + i];
      if (!timeKey) continue;

      if (!grids[item.teacher]) continue;

      const slot: SlotData = {
        id: String(item.id),
        subject: item.subject,
        teacher: `Section ${item.section}`, // ✅ correct display
        room: item.room,
        credits: item.total_credits ?? item.credits,
        duration: duration,
      };

      if (!grids[item.teacher][item.day]) {
        grids[item.teacher][item.day] = {};
      }

      grids[item.teacher][item.day][timeKey] = slot;
    }
  });

  // 5️⃣ Detect breaks (same logic as main mapper)
  const finalTimes: string[] = [];

  for (let i = 0; i < sortedTimes.length; i++) {
    finalTimes.push(sortedTimes[i]);

    if (i < sortedTimes.length - 1) {
      const current = parseTime(sortedTimes[i]);
      const next = parseTime(sortedTimes[i + 1]);

      if (next - current > 60) {
        const breakStart = current + SLOT_DURATION;

        const breakStr = `${Math.floor(breakStart / 60)}:${(
          breakStart % 60
        )
          .toString()
          .padStart(2, "0")}`;

        if (!timeSet.has(breakStr)) {
          finalTimes.push(breakStr);
        }
      }
    }
  }

  const breakTimes = finalTimes.filter((t) => !timeSet.has(t));

  return {
    grids,
    uniqueTeachers,
    uniqueTimes: finalTimes,
    breakTimes,
  };
};