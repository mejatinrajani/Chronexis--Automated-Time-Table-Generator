import { SlotData } from "@/components/DraggableSlot";
import { APISlot, formatTimeDisplay } from "@/utils/dataMapper"; // Reuse existing helpers

const DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"];

// We reuse the GridData type
type GridData = Record<string, Record<string, SlotData | null>>;

export const mapApiToTeacherGrid = (apiData: APISlot[]) => {
  const grids: Record<string, GridData> = {};
  const timeSet = new Set<string>();
  const teacherSet = new Set<string>();

  // 1. First, find all unique teachers and times
  apiData.forEach(item => {
    teacherSet.add(item.teacher);
    timeSet.add(item.time);
  });

  const uniqueTeachers = Array.from(teacherSet).sort();
  
  // 2. Initialize Grids for each Teacher
  uniqueTeachers.forEach(teacher => {
    grids[teacher] = {};
    DAYS.forEach(day => {
      grids[teacher][day] = {};
    });
  });

  // 3. Populate Data
  apiData.forEach((item) => {
    // If the teacher name exists in our list
    if (grids[item.teacher]) {
      const timeKey = item.time;
      
      // LOGIC SWAP: On a Teacher's timetable, they want to know 
      // WHICH SECTION they are teaching, not their own name.
      // So we put 'item.section' into the 'teacher' field of the slot object.
      grids[item.teacher][item.day][timeKey] = {
        id: String(item.id),
        subject: item.subject,
        teacher: `Section ${item.section}`, // <--- Display Section Name here
        room: item.room,
        credits: item.credits
      };
    }
  });

  // 4. Sort Times & Detect Breaks (Reuse logic from dataMapper if possible, or simple sort)
  // We'll do a simple sort here to match your existing logic
  const sortedTimes = Array.from(timeSet).sort((a, b) => {
    const [h1, m1] = a.split(":").map(Number);
    const [h2, m2] = b.split(":").map(Number);
    return h1 * 60 + m1 - (h2 * 60 + m2);
  });

  // Calculate breaks (Simple 60min gap check)
  const breakTimes: string[] = [];
  const finalTimes: string[] = [];
  
  for (let i = 0; i < sortedTimes.length; i++) {
    finalTimes.push(sortedTimes[i]);
    if (i < sortedTimes.length - 1) {
      const current = parseInt(sortedTimes[i].split(":")[0]) * 60 + parseInt(sortedTimes[i].split(":")[1]);
      const next = parseInt(sortedTimes[i+1].split(":")[0]) * 60 + parseInt(sortedTimes[i+1].split(":")[1]);
      
      if (next - current > 60) {
        // Calculate break start (e.g. +50 mins)
        const breakMins = current + 50; 
        const breakStr = `${Math.floor(breakMins/60)}:${(breakMins%60).toString().padStart(2,'0')}`;
        finalTimes.push(breakStr);
        breakTimes.push(breakStr);
      }
    }
  }

  return { grids, uniqueTeachers, uniqueTimes: finalTimes, breakTimes };
};