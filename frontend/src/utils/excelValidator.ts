import { SlotData } from "@/components/DraggableSlot";

type GridData = Record<string, Record<string, SlotData | null>>;

export interface ExcelValidationError {
  id: string;
  type: "CLASH" | "ROOM" | "CONTINUATION"; 
  message: string;
  details?: string[];
  severity: "critical" | "warning";
}

const DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];

export const validateExcelTimetable = (allGrids: Record<string, GridData>): ExcelValidationError[] => {
  const errors: ExcelValidationError[] = [];
  
  const teacherSchedule: Record<string, Record<string, Record<string, string[]>>> = {};
  const roomSchedule: Record<string, Record<string, Record<string, string[]>>> = {};
  const labContinuity: Record<string, Record<string, Record<string, number[]>>> = {};

  const timeSet = new Set<string>();
  Object.values(allGrids).forEach(grid => {
      Object.values(grid).forEach(daySlots => {
          Object.keys(daySlots).forEach(time => timeSet.add(time));
      });
  });
  const sortedTimes = Array.from(timeSet).sort();

  Object.keys(allGrids).forEach(section => {
    const grid = allGrids[section];

    DAYS.forEach(day => {
      if (!grid[day]) return;
      
      Object.keys(grid[day]).forEach(time => {
        const slot = grid[day][time];
        if (!slot) return;

        if (slot.teacher && slot.teacher !== "TBA" && slot.teacher !== "-") {
            if (!teacherSchedule[day]) teacherSchedule[day] = {};
            if (!teacherSchedule[day][time]) teacherSchedule[day][time] = {};
            if (!teacherSchedule[day][time][slot.teacher]) {
                teacherSchedule[day][time][slot.teacher] = [];
            }
            teacherSchedule[day][time][slot.teacher].push(section);
        }

        if (slot.room && slot.room !== "-" && slot.room !== "TBA") {
            if (!roomSchedule[day]) roomSchedule[day] = {};
            if (!roomSchedule[day][time]) roomSchedule[day][time] = {};
            if (!roomSchedule[day][time][slot.room]) {
                roomSchedule[day][time][slot.room] = [];
            }
            roomSchedule[day][time][slot.room].push(section);
        }

        const subjectName = slot.subject.toLowerCase();
        if (subjectName.includes("lab")) {
            if (!labContinuity[section]) labContinuity[section] = {};
            if (!labContinuity[section][day]) labContinuity[section][day] = {};
            if (!labContinuity[section][day][slot.subject]) labContinuity[section][day][slot.subject] = [];
            
            const timeIndex = sortedTimes.indexOf(time);
            labContinuity[section][day][slot.subject].push(timeIndex);
        }
      });
    });
  });

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

  Object.keys(labContinuity).forEach(section => {
      Object.keys(labContinuity[section]).forEach(day => {
          Object.keys(labContinuity[section][day]).forEach(subject => {
              const indices = labContinuity[section][day][subject].sort((a, b) => a - b);
              if (indices.length > 1) {
                  const isContiguous = indices.every((val, i) => i === 0 || val === indices[i - 1] + 1);
                  if (!isContiguous) {
                      errors.push({
                          id: `gap-lab-${section}-${day}-${subject.replace(/\s+/g, '-')}`,
                          type: "CONTINUATION",
                          severity: "warning",
                          message: `Lab Continuation Error: ${subject}`,
                          details: [`${subject} in ${section} on ${day} is split across non-adjacent time slots.`]
                      });
                  }
              }
          });
      });
  });

  return errors;
};