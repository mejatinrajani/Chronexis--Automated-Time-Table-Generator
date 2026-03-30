import { SlotData } from "@/components/DraggableSlot";

type GridData = Record<string, Record<string, SlotData | null>>;

export interface ExcelValidationError {
  id: string;
  type: "CLASH" | "ROOM"; 
  message: string;
  details?: string[];
  severity: "critical" | "warning";
}

const DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"];

export const validateExcelTimetable = (allGrids: Record<string, GridData>): ExcelValidationError[] => {
  const errors: ExcelValidationError[] = [];
  
  // Map: Day -> Time -> Teacher Name -> List of Sections
  const teacherSchedule: Record<string, Record<string, Record<string, string[]>>> = {};
  
  // Map: Day -> Time -> Room Name -> List of Sections
  const roomSchedule: Record<string, Record<string, Record<string, string[]>>> = {};

  // --- PASS 1: SCAN EVERY SLOT ---
  Object.keys(allGrids).forEach(section => {
    const grid = allGrids[section];

    DAYS.forEach(day => {
      if (!grid[day]) return;
      
      Object.keys(grid[day]).forEach(time => {
        const slot = grid[day][time];
        if (!slot) return;

        // A. Track Teacher Usage (Critical Clash)
        if (slot.teacher && slot.teacher !== "TBA" && slot.teacher !== "-") {
            if (!teacherSchedule[day]) teacherSchedule[day] = {};
            if (!teacherSchedule[day][time]) teacherSchedule[day][time] = {};
            
            if (!teacherSchedule[day][time][slot.teacher]) {
                teacherSchedule[day][time][slot.teacher] = [];
            }
            teacherSchedule[day][time][slot.teacher].push(section);
        }

        // B. Track Room Usage (Critical Clash)
        if (slot.room && slot.room !== "-" && slot.room !== "TBA") {
            if (!roomSchedule[day]) roomSchedule[day] = {};
            if (!roomSchedule[day][time]) roomSchedule[day][time] = {};
            
            if (!roomSchedule[day][time][slot.room]) {
                roomSchedule[day][time][slot.room] = [];
            }
            roomSchedule[day][time][slot.room].push(section);
        }
      });
    });
  });

  // --- PASS 2: DETECT ISSUES ---
  
  // A. Check Teachers
  Object.keys(teacherSchedule).forEach(day => {
    Object.keys(teacherSchedule[day]).forEach(time => {
        Object.keys(teacherSchedule[day][time]).forEach(teacher => {
            const sections = teacherSchedule[day][time][teacher];
            if (sections.length > 1) {
                errors.push({
                    id: `clash-fac-${day}-${time}-${teacher}`,
                    type: "CLASH",
                    severity: "critical",
                    message: `Faculty Clash: ${teacher}`,
                    details: [`Booked in ${sections.join(", ")} at ${day} ${time}`]
                });
            }
        });
    });
  });

  // B. Check Rooms
  Object.keys(roomSchedule).forEach(day => {
    Object.keys(roomSchedule[day]).forEach(time => {
        Object.keys(roomSchedule[day][time]).forEach(room => {
            const sections = roomSchedule[day][time][room];
            if (sections.length > 1) {
                errors.push({
                    id: `clash-room-${day}-${time}-${room}`,
                    type: "ROOM",
                    severity: "critical",
                    message: `Room Clash: ${room}`,
                    details: [`Occupied by ${sections.join(", ")} at ${day} ${time}`]
                });
            }
        });
    });
  });

  return errors;
};