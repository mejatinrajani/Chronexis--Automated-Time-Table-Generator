import { cn } from "@/lib/utils";
import { GripVertical, X, Edit2 } from "lucide-react";
import { useState } from "react";

export interface SlotData {
  id: string;
  subject: string;
  teacher: string;
  room?: string;
  credits?: number;
  duration?: number;
}

interface DraggableSlotProps {
  slot: SlotData;
  onDragStart: (e: React.DragEvent, slot: SlotData) => void;
  onDelete?: (id: string) => void;
  onEdit?: (id: string) => void;
}

const DraggableSlot = ({ slot, onDragStart, onDelete, onEdit }: DraggableSlotProps) => {
  const [hovering, setHovering] = useState(false);

  return (
    <div
      draggable
      onDragStart={(e) => onDragStart(e, slot)}
      onMouseEnter={() => setHovering(true)}
      onMouseLeave={() => setHovering(false)}
      className={cn(
        "group relative cursor-grab border border-border bg-secondary p-2.5 transition-all duration-200 select-none h-full", // Added h-full to fill td
        "hover:bg-accent hover:border-foreground/20 active:cursor-grabbing",
        "active:scale-105 active:shadow-[0_20px_60px_-10px_rgba(0,0,0,0.8)]"
      )}
    >
      <div className="flex items-start gap-2 h-full overflow-hidden"> 
        <div className="min-w-0 flex-1 overflow-hidden"> 
          {/* Truncate applied here */}
          <p className="truncate text-[15px] font-medium text-foreground" title={slot.subject}>
             {slot.subject}
          </p>
          {/* Truncate applied here */}
          <p className="truncate text-[15px] text-muted-foreground" title={slot.teacher}>
             {slot.teacher}
          </p>
          <div className="mt-1 flex items-center gap-2">
            {slot.room && (
              <span className="truncate text-[15px] text-muted-foreground/70" title={slot.room}>
                 {slot.room}
              </span>
            )}
            {slot.credits && (
              <span className="shrink-0 text-[15px] text-muted-foreground/50">
                 {slot.credits} credits
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Action buttons */}
      {hovering && (
        <div className="absolute right-1 top-1 flex gap-0.5 animate-fade-in bg-secondary/80 rounded p-0.5 backdrop-blur-sm">
          {onEdit && (
            <button onClick={() => onEdit(slot.id)} className="p-0.5 text-muted-foreground hover:text-foreground transition-colors">
              <Edit2 size={12} />
            </button>
          )}
          {onDelete && (
            <button onClick={() => onDelete(slot.id)} className="p-0.5 text-muted-foreground hover:text-foreground transition-colors">
               <X size={14} />
            </button>
          )}
        </div>
      )}
    </div>
  );
};

export default DraggableSlot;