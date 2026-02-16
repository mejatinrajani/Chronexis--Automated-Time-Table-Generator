import ExcelJS from 'exceljs';
import { saveAs } from 'file-saver';
import { SlotData } from '@/components/DraggableSlot';

type GridData = Record<string, Record<string, SlotData | null>>;

const DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"];
const SLOT_DURATION = 50; 

const formatHeader = (timeStr: string) => {
    if (timeStr.includes("LUNCH")) return "LUNCH";
    
    if (!timeStr.includes(":")) return timeStr; // Fallback

    const [h, m] = timeStr.split(":").map(Number);
    const startMins = h * 60 + m;
    const endMins = startMins + SLOT_DURATION;

    const minsTo12h = (totalMins: number) => {
        const hh = Math.floor(totalMins / 60);
        const mm = totalMins % 60;
        const period = hh >= 12 ? "PM" : "AM";
        const displayH = hh > 12 ? hh - 12 : hh === 0 ? 12 : hh;
        return `${displayH}:${mm.toString().padStart(2, '0')} ${period}`;
    };

    return `${minsTo12h(startMins)} - ${minsTo12h(endMins)}`;
};

export const exportTimetableToExcel = async (
  allGrids: Record<string, GridData>,
  timeSlots: string[],
  filename: string = "Timetable_Export"
) => {
  const workbook = new ExcelJS.Workbook();
  workbook.creator = "Timetable Generator";
  workbook.created = new Date();

  const sheetNames = Object.keys(allGrids).sort();

  if (sheetNames.length === 0) {
    alert("No data to export!");
    return;
  }

  for (const sheetName of sheetNames) {
    const safeName = sheetName.replace(/[*?:\/\[\]]/g, '').substring(0, 31);
    const worksheet = workbook.addWorksheet(safeName);

    const columns = [
      { header: 'Day / Time', key: 'day', width: 20 }, 
      ...timeSlots.map(time => {
        const isLunch = time.includes("LUNCH");
        return {
            header: formatHeader(time), 
            key: time,
            width: isLunch ? 8 : 32 // Narrow column for Lunch
        };
      })
    ];
    worksheet.columns = columns;

    const headerRow = worksheet.getRow(1);
    headerRow.height = 45; 
    headerRow.eachCell((cell, colNum) => {
      const isLunch = timeSlots[colNum - 2]?.includes("LUNCH");
      
      cell.font = { bold: true, size: 12, color: { argb: isLunch ? 'FF666666' : 'FFFFFFFF' } };
      cell.fill = {
        type: 'pattern',
        pattern: 'solid',
        fgColor: { argb: isLunch ? 'FFE5E7EB' : 'FF4F46E5' }
      };
      cell.alignment = { vertical: 'middle', horizontal: 'center', wrapText: true };
      
      if (isLunch) cell.alignment.textRotation = 90;

      cell.border = { top: { style: 'thin' }, left: { style: 'thin' }, bottom: { style: 'thin' }, right: { style: 'thin' } };
    });

    const grid = allGrids[sheetName];

    DAYS.forEach(day => {
      const rowData: Record<string, string> = { day: day };
      
      timeSlots.forEach(time => {
        if (time.includes("LUNCH")) {
            rowData[time] = "";
            return;
        }

        const slot = grid[day]?.[time];
        if (slot) {
          const lines = [slot.subject];
          if (slot.teacher && slot.teacher !== 'TBA') lines.push(slot.teacher);
          if (slot.room && slot.room !== 'TBA') lines.push(`Room: ${slot.room}`);
          rowData[time] = lines.join('\n');
        } else {
          rowData[time] = '';
        }
      });

      const row = worksheet.addRow(rowData);
      row.height = 85;

      const dayCell = row.getCell(1);
      dayCell.font = { bold: true, size: 12 };
      dayCell.fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FFF3F4F6' } };
      dayCell.alignment = { vertical: 'middle', horizontal: 'center' };
      dayCell.border = { top: { style: 'thin' }, left: { style: 'thin' }, bottom: { style: 'thin' }, right: { style: 'thin' } };

      row.eachCell({ includeEmpty: true }, (cell, colNumber) => {
        if (colNumber > 1) {
            const timeKey = timeSlots[colNumber - 2];
            const isLunch = timeKey?.includes("LUNCH");

            cell.border = { top: { style: 'thin' }, left: { style: 'thin' }, bottom: { style: 'thin' }, right: { style: 'thin' } };

            if (isLunch) {
                cell.fill = { type: 'pattern', pattern: 'lightUp', fgColor: { argb: 'FFE5E7EB' } };
            } else {
                cell.alignment = { wrapText: true, vertical: 'middle', horizontal: 'center' };
                cell.font = { size: 11 };

                if (cell.value) {
                     const strVal = String(cell.value);
                     if (strVal.toLowerCase().includes('lab') || strVal.includes('2 cr')) {
                        cell.fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FFECFDF5' } };
                     }
                }
            }
        }
      });
    });
  }

  const buffer = await workbook.xlsx.writeBuffer();
  const blob = new Blob([buffer], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
  saveAs(blob, `${filename}.xlsx`);
};