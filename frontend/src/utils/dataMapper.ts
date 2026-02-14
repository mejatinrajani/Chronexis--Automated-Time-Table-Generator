import { SlotData } from "@/components/DraggableSlot";

export interface APISlot {
  id: number | string;
  section: string;
  day: string;
  time: string;
  subject: string;
  teacher: string;
  room?: string;
  credits?: number;
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
  return `${displayH}:${m.toString().padStart(2, '0')}`;
};

export const formatTimeDisplay = (timeStr: string) => {
  if (!timeStr) return "";
  const [h, m] = timeStr.split(":").map(Number);
  const displayH = h > 12 ? h - 12 : h === 0 ? 12 : h; 
  return `${displayH}:${m.toString().padStart(2, '0')}`;
};

export const formatSlotRange = (startStr: string) => {
  if (!startStr) return "";
  const startMins = parseTime(startStr);
  const endMins = startMins + SLOT_DURATION;
  return `${minutesToTime(startMins)} - ${minutesToTime(endMins)}`;
};

export const mapApiToGrid = (apiData: APISlot[], sections: string[], forcedTimeSlots?: string[]) => {
  const grids: Record<string, GridData> = {};
  
  // 1. Initialize Time Set
  let timeSet = new Set<string>();

  // FORCE THE FULL RANGE FROM SERVER
  if (forcedTimeSlots && forcedTimeSlots.length > 0) {
      forcedTimeSlots.forEach(t => timeSet.add(t));
  } 
  
  // Also include times from data (in case a class was scheduled outside standard hours)
  apiData.forEach(item => timeSet.add(item.time));

  // 2. Initialize Grids
  sections.forEach(section => {
    grids[section] = {};
    DAYS.forEach(day => { grids[section][day] = {}; });
  });

  // 3. Populate Data
  apiData.forEach((item) => {
    if (!grids[item.section]) {
      grids[item.section] = {}; 
      DAYS.forEach(day => { grids[item.section][day] = {}; });
    }

    if (grids[item.section][item.day]) {
      grids[item.section][item.day][item.time] = {
        id: String(item.id),
        subject: item.subject,
        teacher: item.teacher,
        room: item.room,
        credits: item.credits,
        duration: item.duration || 1, 
      };
    }
  });

  // 4. Sort Times (This ensures 9:00 comes before 10:00)
  let sortedTimes = Array.from(timeSet).sort((a, b) => parseTime(a) - parseTime(b));

  // 5. Lunch Break Detection
  // We only add visual breaks if we are inferring times. 
  // If forcedTimeSlots is present, we trust the server's layout.
  // But let's keep the gap check just in case the server slots have a gap.
  const finalTimes: string[] = [];
  
  for (let i = 0; i < sortedTimes.length; i++) {
    finalTimes.push(sortedTimes[i]);
    
    if (i < sortedTimes.length - 1) {
      const current = parseTime(sortedTimes[i]);
      const next = parseTime(sortedTimes[i+1]);
      
      // If gap is > 60 mins, likely a Lunch Break
      if (next - current > 60) {
        // We create a fake "Lunch" slot purely for visual rendering
        // We do NOT add it to the grid data, just the columns list
        const breakStartMins = current + SLOT_DURATION;
        const h = Math.floor(breakStartMins / 60);
        const m = breakStartMins % 60;
        const breakStartStr = `${h}:${m.toString().padStart(2, '0')}`;
        
        // Only add if it doesn't duplicate existing slot
        if (!timeSet.has(breakStartStr)) {
            finalTimes.push(breakStartStr);
        }
      }
    }
  }

  // Identify which times are purely breaks (not in original set)
  // This helps the UI render them differently (grayed out)
  const breakTimes = finalTimes.filter(t => !timeSet.has(t) && !forcedTimeSlots?.includes(t));

  return { grids, uniqueTimes: finalTimes, breakTimes };
};