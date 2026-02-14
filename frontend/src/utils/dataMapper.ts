import { SlotData } from "@/components/DraggableSlot";

export interface APISlot {
  id: number | string;
  section: string;
  day: string;
  time: string; // e.g. "09:50", "14:20"
  subject: string;
  teacher: string;
  room?: string;
  credits?: number;
}

type GridData = Record<string, Record<string, SlotData | null>>;

const DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"];
const SLOT_DURATION = 50; // Minutes

// --- Helpers ---

const parseTime = (t: string) => {
  const [h, m] = t.split(":").map(Number);
  return h * 60 + m;
};

const minutesToTime = (mins: number) => {
  const h = Math.floor(mins / 60);
  const m = mins % 60;
  // Convert to 12h format if needed, or keep 24h. 
  // e.g. 13:00 -> 1:00
  const displayH = h > 12 ? h - 12 : h;
  return `${displayH}:${m.toString().padStart(2, '0')}`;
};

// EXPORT THIS FUNCTION (This was likely missing or not imported)
export const formatTimeDisplay = (timeStr: string) => {
  if (!timeStr) return "";
  const [h, m] = timeStr.split(":").map(Number);
  const displayH = h > 12 ? h - 12 : h; 
  return `${displayH}:${m.toString().padStart(2, '0')}`;
};

export const formatSlotRange = (startStr: string) => {
  if (!startStr) return "";
  const startMins = parseTime(startStr);
  const endMins = startMins + SLOT_DURATION;
  return `${minutesToTime(startMins)} - ${minutesToTime(endMins)}`;
};

export const mapApiToGrid = (apiData: APISlot[], sections: string[]) => {
  const grids: Record<string, GridData> = {};
  const timeSet = new Set<string>();

  // 1. Initialize Grids
  sections.forEach(section => {
    grids[section] = {};
    DAYS.forEach(day => { grids[section][day] = {}; });
  });

  // 2. Populate Data
  apiData.forEach((item) => {
    if (!grids[item.section]) {
      grids[item.section] = {}; 
      DAYS.forEach(day => { grids[item.section][day] = {}; });
    }
    const timeKey = item.time; 
    timeSet.add(timeKey);

    if (grids[item.section][item.day]) {
      grids[item.section][item.day][timeKey] = {
        id: String(item.id),
        subject: item.subject,
        teacher: item.teacher,
        room: item.room,
        credits: item.credits
      };
    }
  });

  // 3. Sort & Detect Lunch Breaks
  let sortedTimes = Array.from(timeSet).sort((a, b) => parseTime(a) - parseTime(b));
  const breakTimes: string[] = [];

  // Look for gaps > 60 mins to insert a Lunch Break automatically
  const finalTimes: string[] = [];
  
  for (let i = 0; i < sortedTimes.length; i++) {
    finalTimes.push(sortedTimes[i]);
    
    if (i < sortedTimes.length - 1) {
      const current = parseTime(sortedTimes[i]);
      const next = parseTime(sortedTimes[i+1]);
      
      // If gap is big (e.g. > 60 mins), insert a break slot
      if (next - current > 60) {
        // Calculate where the break likely starts (e.g., 50 mins after current slot)
        const breakStartMins = current + SLOT_DURATION;
        const breakStartStr = `${Math.floor(breakStartMins/60)}:${(breakStartMins%60).toString().padStart(2,'0')}`;
        
        finalTimes.push(breakStartStr); // Add fake slot
        breakTimes.push(breakStartStr); // Mark as break
      }
    }
  }

  return { grids, uniqueTimes: finalTimes, breakTimes };
};