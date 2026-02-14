import * as XLSX from "xlsx";
import { SlotData } from "@/components/DraggableSlot";

const DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"];
const TIME_SLOTS = ["8:00", "9:00", "10:00", "11:00", "12:00", "1:00", "2:00", "3:00", "4:00"];

type GridData = Record<string, Record<string, SlotData | null>>;

export const exportTimetableToExcel = (allGrids: Record<string, GridData>) => {
  const wb = XLSX.utils.book_new();

  Object.keys(allGrids).forEach((sectionName) => {
    const grid = allGrids[sectionName];
    
    // Create Header Row
    const headers = ["Day/Time", ...TIME_SLOTS];
    
    // Create Data Rows
    const dataRows = DAYS.map((day) => {
      const row = [day];
      TIME_SLOTS.forEach((time) => {
        const slot = grid[day]?.[time];
        if (slot) {
          // Format text inside the cell
          row.push(`${slot.subject}\n(${slot.teacher})`);
        } else {
          row.push("");
        }
      });
      return row;
    });

    const wsData = [headers, ...dataRows];
    const ws = XLSX.utils.aoa_to_sheet(wsData);

    // Set generic column width
    ws['!cols'] = [{ wch: 15 }, ...TIME_SLOTS.map(() => ({ wch: 20 }))];

    XLSX.utils.book_append_sheet(wb, ws, sectionName);
  });

  XLSX.writeFile(wb, "Timetable_Schedule.xlsx");
};