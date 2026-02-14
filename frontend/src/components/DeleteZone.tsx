import { useState } from "react";
import { Trash2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { globalDragData } from "@/utils/dragState";

interface DeleteZoneProps {
  onDeleteFromGrid: (section: string, day: string, time: string) => void;
  onDeleteFromClipboard: (index: number) => void;
}

const DeleteZone = ({ onDeleteFromGrid, onDeleteFromClipboard }: DeleteZoneProps) => {
  const [isOver, setIsOver] = useState(false);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsOver(true);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsOver(false);
    const data = globalDragData.current;

    if (!data) return;

    if (data.type === "GRID" && data.section && data.day && data.time) {
      onDeleteFromGrid(data.section, data.day, data.time);
    } else if (data.type === "CLIPBOARD" && typeof data.index === 'number') {
      onDeleteFromClipboard(data.index);
    }
    
    globalDragData.current = null;
  };

  return (
    <div
      onDragOver={handleDragOver}
      onDragLeave={() => setIsOver(false)}
      onDrop={handleDrop}
      className={cn(
        "flex h-14 items-center justify-center gap-2 rounded-md border border-dashed transition-all duration-200 px-4",
        isOver 
          ? "border-red-500 bg-red-500/10 text-red-600 scale-105" 
          : "border-red-200 bg-red-50 text-red-400 hover:border-red-300 hover:text-red-500"
      )}
    >
      <Trash2 size={25} />
      <span className="text-[20px] font-medium uppercase tracking-widest">
        {isOver ? "Drop to Delete" : "Drag here to Delete"}
      </span>
    </div>
  );
};

export default DeleteZone;