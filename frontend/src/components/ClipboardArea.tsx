import { useState } from "react";
import { ClipboardList, Plus } from "lucide-react";
import { cn } from "@/lib/utils";
import DraggableSlot, { SlotData } from "./DraggableSlot";
import { globalDragData } from "@/utils/dragState";

interface ClipboardAreaProps {
  items: SlotData[];
  onDropFromGrid: (slot: SlotData, fromSection: string, fromDay: string, fromTime: string) => void;
  onRemoveItem: (index: number) => void;
}

const ClipboardArea = ({ items, onDropFromGrid, onRemoveItem }: ClipboardAreaProps) => {
  const [isOver, setIsOver] = useState(false);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    // Only allow drop if it's coming from the GRID
    if (globalDragData.current?.type === "GRID") {
      setIsOver(true);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsOver(false);
    const data = globalDragData.current;

    if (data && data.type === "GRID" && data.section && data.day && data.time) {
      onDropFromGrid(data.slot, data.section, data.day, data.time);
      globalDragData.current = null;
    }
  };

  const handleDragStart = (e: React.DragEvent, slot: SlotData, index: number) => {
    globalDragData.current = {
      type: "CLIPBOARD",
      slot,
      index
    };
    e.dataTransfer.effectAllowed = "move";
  };

  return (
    <div 
      className={cn(
        "mt-6 rounded-lg border-4 border-dashed p-4 transition-all duration-200",
        isOver ? "border-primary bg-primary/5" : "border-border bg-secondary/30",
        items.length === 0 && "py-8"
      )}
      onDragOver={handleDragOver}
      onDragLeave={() => setIsOver(false)}
      onDrop={handleDrop}
    >
      <div className="mb-4 flex items-center gap-3 text-lg font-medium text-muted-foreground">
        <ClipboardList size={30} />
        <span className="uppercase tracking-widest text-[25px]">Class Clipboard</span>
        <span className="text-[25px] opacity-80">
             (Drag classes here to move them between sections)
        </span>
      </div>

      <div className="flex flex-wrap gap-3 mt-24">
        {items.length === 0 ? (
          <div className="w-full text-center text-[25px] text-muted-foreground/50">
            Drop a class here to hold it
          </div>
        ) : (
          items.map((slot, index) => (
            <div key={`${slot.id}-${index}`} className="w-48">
              <DraggableSlot 
                slot={slot} 
                onDragStart={(e, s) => handleDragStart(e, s, index)}
                onDelete={() => onRemoveItem(index)} // Allow deleting from clipboard
              />
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default ClipboardArea;