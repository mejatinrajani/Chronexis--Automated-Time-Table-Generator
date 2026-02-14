import { SlotData } from "@/components/DraggableSlot";

type GridData = Record<string, Record<string, SlotData | null>>;

export interface ValidationError {
  id: string;
  type: "CLASH" | "CREDITS" | "ROOM";
  message: string;
  details?: string[];
  severity: "critical" | "warning";
}

const DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"];

export const validateTimetable = (allGrids: Record<string, GridData>): ValidationError[] => {
  const errors: ValidationError[] = [];
  
  // 1. Prepare Data Structures
  // Map: Day -> Time -> Teacher Name -> List of Sections
  const teacherSchedule: Record<string, Record<string, Record<string, string[]>>> = {};
  
  // Map: Day -> Time -> Room Name -> List of Sections
  const roomSchedule: Record<string, Record<string, Record<string, string[]>>> = {};
  
  // Map: Section -> Subject -> { actualSlots, requiredSessions, duration }
  const creditCounts: Record<string, Record<string, { actualSlots: number, requiredSessions: number, duration: number }>> = {};

  // --- PASS 1: SCAN EVERY SLOT ---
  Object.keys(allGrids).forEach(section => {
    const grid = allGrids[section];
    if (!creditCounts[section]) creditCounts[section] = {};

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

        // C. Track Credits (Session Count)
        // We use 'duration' to differentiate between 1-hour Theory and 2-hour Labs
        const duration = slot.duration || 1; 
        const required = slot.credits || 0;

        if (!creditCounts[section][slot.subject]) {
            creditCounts[section][slot.subject] = { 
                actualSlots: 0, 
                requiredSessions: required,
                duration: duration
            };
        }
        creditCounts[section][slot.subject].actualSlots += 1;
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

  // C. Check Credits / Sessions
  Object.keys(creditCounts).forEach(section => {
      Object.keys(creditCounts[section]).forEach(subject => {
          const { actualSlots, requiredSessions, duration } = creditCounts[section][subject];
          
          // LOGIC: 
          // If duration is 2 (Lab), then 4 slots = 2 Sessions.
          // If duration is 1 (Theory), then 3 slots = 3 Sessions.
          const actualSessions = actualSlots / duration;

          if (requiredSessions > 0 && actualSessions !== requiredSessions) {
              // Create readable mismatch string
              const expectedStr = duration > 1 
                 ? `${requiredSessions} sessions (${requiredSessions * duration} hrs)`
                 : `${requiredSessions} hrs`;

              const actualStr = duration > 1
                 ? `${actualSessions} sessions (${actualSlots} hrs)`
                 : `${actualSlots} hrs`;

              errors.push({
                  id: `cred-${section}-${subject}`,
                  type: "CREDITS",
                  severity: "warning",
                  message: `Credit Mismatch in ${section}: ${subject}`,
                  details: [
                      `Scheduled: ${actualStr}`, 
                      `Required: ${expectedStr}`
                  ]
              });
          }
      });
  });

  return errors;
};