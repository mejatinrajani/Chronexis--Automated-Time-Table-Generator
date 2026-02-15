import { useState, useCallback } from "react";
import DraggableSlot, { SlotData } from "./DraggableSlot";
import { cn } from "@/lib/utils";
import { globalDragData } from "@/utils/dragState";
import { formatSlotRange } from "@/utils/dataMapper"; // Updated import

const DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"];

type GridData = Record<string, Record<string, SlotData | null>>;

interface TimetableGridProps {
  section: string;
  grid: GridData;
  timeSlots: string[];
  breakTimes?: string[]; // New prop for lunch slots
  onGridChange: (grid: GridData) => void;
  onDelete: (id: string) => void;
  onDropFromClipboard: (slot: SlotData, day: string, time: string, clipboardIndex: number) => void; 
}

const TimetableGrid = ({ section, grid, timeSlots, breakTimes = [], onGridChange, onDelete, onDropFromClipboard }: TimetableGridProps) => {
  const [dragOver, setDragOver] = useState<string | null>(null);

  if (!timeSlots || timeSlots.length === 0) return <div>No time slots available</div>;

  const handleDragStart = useCallback((e: React.DragEvent, slot: SlotData, day: string, time: string) => {
    globalDragData.current = { type: "GRID", slot, section, day, time };
    e.dataTransfer.effectAllowed = "move";
  }, [section]);

  const handleDrop = useCallback((day: string, time: string) => {
    const data = globalDragData.current;
    if (!data) return;

    if (data.type === "GRID" && data.section === section) {
      if(data.day === day && data.time === time) { setDragOver(null); return; }

      const next = { ...grid };
      if (next[data.day!]?.[data.time!]) {
          const sourceDay = { ...next[data.day!] };
          delete sourceDay[data.time!];
          next[data.day!] = sourceDay;
      }
      const targetDay = { ...next[day] };
      targetDay[time] = data.slot;
      next[day] = targetDay;
      onGridChange(next);
    } 
    else if (data.type === "CLIPBOARD" && typeof data.index === 'number') {
      onDropFromClipboard(data.slot, day, time, data.index);
    }
    globalDragData.current = null;
    setDragOver(null);
  }, [grid, section, onGridChange, onDropFromClipboard]);

  return (
    <div className="overflow-x-hidden pb-4">
      <table className="w-[2100px] border-collapse">
        <thead>
          <tr>
            <th className="border border-border bg-secondary p-3 text-left text-[20px] font-medium uppercase tracking-widest text-muted-foreground w-24 sticky left-0 z-10 shadow-[2px_0_5px_-2px_rgba(0,0,0,0.1)]">
              {section}
            </th>
            {timeSlots.map((time) => {
               const isBreak = breakTimes.includes(time);
               return (
                <th key={time} className={cn(
                    "border border-border bg-secondary p-3 text-center text-[20px] font-medium uppercase tracking-widest text-muted-foreground w-[590px] max-w-[590px]",
                    isBreak && "bg-secondary/50 text-muted-foreground/50"
                )}>
                  {isBreak ? "LUNCH" : formatSlotRange(time)}
                </th>
               );
            })}
          </tr>
        </thead>
        <tbody>
          {DAYS.map((day, dayIndex) => (
            <tr key={day}>
              <td className="border border-border bg-secondary/50 p-3 text-[20px] font-medium text-muted-foreground sticky left-0 z-10 shadow-[2px_0_5px_-2px_rgba(0,0,0,0.1)]">
                {day}
              </td>
              
              {timeSlots.map((time) => {
                const isBreak = breakTimes.includes(time);
                
                // LUNCH BREAK LOGIC
                if (isBreak) {
                    // Only render the cell for the FIRST row (Monday)
                    if (dayIndex === 0) {
                        return (
                            <td 
                                key={`${day}-${time}`} 
                                rowSpan={DAYS.length} 
                                className="border border-border bg-secondary/30 text-center align-middle"
                            >
                                <div className="flex h-full items-center justify-center">
                                    <span className="text-[20px] font-bold text-muted-foreground/40 tracking-[0.5em] uppercase" style={{ writingMode: "vertical-rl", textOrientation: "mixed", transform: "rotate(180deg)" }}>
                                        LUNCH BREAK
                                    </span>
                                </div>
                            </td>
                        );
                    }
                    // For other days, render nothing (because the first one spans down)
                    return null;
                }

                // NORMAL SLOT LOGIC
                const cellKey = `${day}-${time}`;
                const slot = grid[day]?.[time] || null;
                const isOver = dragOver === cellKey;

                return (
                  <td
                    key={cellKey}
                    onDragOver={(e) => { e.preventDefault(); setDragOver(cellKey); }}
                    onDragLeave={() => setDragOver(null)}
                    onDrop={() => handleDrop(day, time)}
                    className={cn(
                      "border border-border p-1.5 transition-all duration-200 h-24 align-top cell-hover",
                      isOver && "drop-zone-active bg-primary/10"
                    )}
                  >
                    {slot ? (
                      <div className="h-full">
                         <DraggableSlot
                            slot={slot}
                            onDragStart={(e, s) => handleDragStart(e, s, day, time)}
                            onDelete={(id) => onDelete(id)}
                          />
                      </div>
                    ) : (
                      <div className="h-full w-full" />
                    )}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default TimetableGrid;