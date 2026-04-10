import { useState, useCallback } from "react";
import DraggableSlot, { SlotData } from "./DraggableSlot";
import { cn } from "@/lib/utils";
import { globalDragData } from "@/utils/dragState";
import { formatSlotRange } from "@/utils/dataMapper"; 

const DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"];

type GridData = Record<string, Record<string, SlotData | null>>;

interface TimetableGridProps {
  section: string;
  grid: GridData;
  timeSlots: string[];
  breakTimes?: string[]; 
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
    <div className="overflow-x-auto pb-4 w-full"> 
      {/* 
        table-fixed forces equal column widths.
        min-w-[1200px] ensures it scrolls on small screens rather than crushing columns.
      */}
      <table className="w-full min-w-[3000px] table-fixed border-collapse">
        <thead>
          <tr>
            {/* Set a specific width for the Days column */}
            <th className="w-32 border border-border bg-secondary p-3 text-left text-[16px] md:text-[20px] font-medium uppercase tracking-widest text-muted-foreground sticky left-0 z-10 shadow-[2px_0_5px_-2px_rgba(0,0,0,0.1)]">
              {section}
            </th>
            
            {timeSlots.map((time) => {
               const isBreak = breakTimes.includes(time);
               return (
                <th key={time} className={cn(
                    // Removed dynamic max-w, let table-fixed handle the equal sizing
                    "border border-border bg-secondary p-3 text-center text-[16px] md:text-[20px] font-medium uppercase tracking-widest text-muted-foreground",
                    isBreak && "bg-secondary/50 text-muted-foreground/50 w-24" // Make lunch column slightly thinner
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
              <td className="border border-border bg-secondary/50 p-3 text-[16px] md:text-[20px] font-medium text-muted-foreground sticky left-0 z-10 shadow-[2px_0_5px_-2px_rgba(0,0,0,0.1)]">
                {day}
              </td>
              
              {timeSlots.map((time) => {
                const isBreak = breakTimes.includes(time);
                
                if (isBreak) {
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
                    return null;
                }

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
                      "border border-border p-1.5 transition-all duration-200 h-28 align-top cell-hover relative", // Added relative
                      isOver && "drop-zone-active bg-primary/10"
                    )}
                  >
                    {slot ? (
                      <div className="h-full w-full absolute inset-0 p-1.5"> {/* Absolute fill ensures the card takes exact cell boundaries */}
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