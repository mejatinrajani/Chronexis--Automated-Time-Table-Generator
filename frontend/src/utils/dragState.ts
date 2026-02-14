import { SlotData } from "@/components/DraggableSlot";

export type DragSourceType = "GRID" | "CLIPBOARD";

export interface GlobalDragState {
  type: DragSourceType;
  slot: SlotData;
  // If from GRID
  section?: string;
  day?: string;
  time?: string;
  // If from CLIPBOARD
  index?: number; 
}

// We use a mutable object for this simple drag implementation
export const globalDragData: { current: GlobalDragState | null } = {
  current: null,
};