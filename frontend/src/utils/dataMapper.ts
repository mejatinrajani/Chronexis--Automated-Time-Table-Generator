import { SlotData } from "@/components/DraggableSlot";

export interface APISlot {
  id: number | string;
  section: string;
  day: string;
  start_time: string;   
  end_time: string;     
  subject: string;
  teacher: string;
  room?: string;
  credits?: number;
  total_credits?: number; 
  duration?: number;
}

type GridData = Record<string, Record<string, SlotData | null>>;

const DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"];
const SLOT_DURATION = 50;

// --- Helpers ---
const parseTime = (t: string) => {
  if (!t) return 0;
  const [h, m] = t.split(":").map(Number);
  return h * 60 + m;
};

const minutesToTime = (mins: number) => {
  const h = Math.floor(mins / 60);
  const m = mins % 60;
  const displayH = h > 12 ? h - 12 : h === 0 ? 12 : h;
  return `${displayH}:${m.toString().padStart(2, "0")}`;
};

export const formatTimeDisplay = (timeStr: string) => {
  if (!timeStr) return "";
  const [h, m] = timeStr.split(":").map(Number);
  const displayH = h > 12 ? h - 12 : h === 0 ? 12 : h;
  return `${displayH}:${m.toString().padStart(2, "0")}`;
};

export const formatSlotRange = (startStr: string, endStr?: string) => {
  if (!startStr) return "";
  if (!endStr) {
    const startMins = parseTime(startStr);
    const endMins = startMins + SLOT_DURATION;
    return `${minutesToTime(startMins)} - ${minutesToTime(endMins)}`;
  }
  return `${formatTimeDisplay(startStr)} - ${formatTimeDisplay(endStr)}`;
};

// 🔥 MAIN FIX FUNCTION
export const mapApiToGrid = (
  apiData: APISlot[],
  sections: string[],
  forcedTimeSlots?: string[]
) => {
  const grids: Record<string, GridData> = {};

  // 1. Collect all time slots
  let timeSet = new Set<string>();

  if (forcedTimeSlots && forcedTimeSlots.length > 0) {
    forcedTimeSlots.forEach((t) => timeSet.add(t));
  }

  apiData.forEach((item) => {
    timeSet.add(item.start_time);
  });

  // 2. Sort times
  let sortedTimes = Array.from(timeSet).sort(
    (a, b) => parseTime(a) - parseTime(b)
  );

  // 3. Initialize grids
  sections.forEach((section) => {
    grids[section] = {};
    DAYS.forEach((day) => {
      grids[section][day] = {};
    });
  });

  // 🔥 4. PLACE DATA (HANDLE LABS PROPERLY)
  apiData.forEach((item) => {
    const duration = item.duration || 1;

    const startIndex = sortedTimes.indexOf(item.start_time);

    // 🔥 EXPAND INTO MULTIPLE CELLS (KEY FIX)
    for (let i = 0; i < duration; i++) {
      const timeKey = sortedTimes[startIndex + i];
      if (!timeKey) continue;

      const slot: SlotData = {
      id: String(item.id),
      subject: item.subject,
      teacher: item.teacher,
      room: item.room,
      credits: item.total_credits ?? item.credits,
      duration: duration,
      };
      if (!grids[item.section]) {
        grids[item.section] = {};
        DAYS.forEach((d) => (grids[item.section][d] = {}));
      }

      if (!grids[item.section][item.day]) {
        grids[item.section][item.day] = {};
      }

      grids[item.section][item.day][timeKey] = slot;
    }
  });

  // 5. Detect breaks
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

  const breakTimes = finalTimes.filter(
    (t) => !timeSet.has(t) && !forcedTimeSlots?.includes(t)
  );

  return {
    grids,
    uniqueTimes: finalTimes,
    breakTimes,
  };
};