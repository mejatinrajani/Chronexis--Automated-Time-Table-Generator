import { useState, useCallback, useEffect } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import TimetableGrid from "@/components/TimetableGrid";
import SectionTabs from "@/components/SectionTabs"; 
import AppButton from "@/components/AppButton";
import Modal from "@/components/Modal";
import InputField from "@/components/InputField";
import ClipboardArea from "@/components/ClipboardArea";
import DeleteZone from "@/components/DeleteZone"; 
import HistoryModal from "@/components/HistoryModal";
import { Undo2, Plus, FileSpreadsheet, History, DoorOpen } from "lucide-react";
import { SlotData } from "@/components/DraggableSlot";
import { APISlot, formatTimeDisplay } from "@/utils/dataMapper";
import { mapApiToRoomGrid } from "@/utils/roomMapper"; // Using our new mapper
import { exportTimetableToExcel } from "@/utils/excelExport";
import { apiUrl } from "@/lib/api";

const DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"];

type GridData = Record<string, Record<string, SlotData | null>>;

let nextId = 3000; // Unique range for room-added IDs

const RoomTimetable = () => {
  const [rooms, setRooms] = useState<string[]>([]);
  const [activeRoom, setActiveRoom] = useState("");
  const [loading, setLoading] = useState(false);
  const [allGrids, setAllGrids] = useState<Record<string, GridData>>({});
  
  const [timeSlots, setTimeSlots] = useState<string[]>([]);
  const [breakTimes, setBreakTimes] = useState<string[]>([]); 

  const [clipboardItems, setClipboardItems] = useState<SlotData[]>([]);
  const [addModalOpen, setAddModalOpen] = useState(false);
  const [historyModalOpen, setHistoryModalOpen] = useState(false);
  
  // Form State
  const [newSubject, setNewSubject] = useState("");
  const [newTeacher, setNewTeacher] = useState("");
  const [newSection, setNewSection] = useState("");
  const [newCredits, setNewCredits] = useState("");
  const [newDay, setNewDay] = useState(DAYS[0]);
  const [newTime, setNewTime] = useState("");

  const [history, setHistory] = useState<{ grids: Record<string, GridData>, clipboard: SlotData[] }[]>([]);

  useEffect(() => {
    const fetchSchedule = async () => {
      setLoading(true);
      try {
        const response = await fetch(apiUrl("/api/latest/"));
        const result = await response.json();
        
        const data: APISlot[] = Array.isArray(result) ? result : result.schedule; 
        
        if (Array.isArray(data) && data.length > 0) {
           processAndLoadData(data);
        } else {
            console.warn("API returned empty array");
        }
      } catch (error) {
        console.error("Failed to fetch schedule:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchSchedule();
  }, []);

  const handleExportExcel = () => {
    exportTimetableToExcel(allGrids, timeSlots, "Room_Occupancy_Schedules");
  };

  const processAndLoadData = (data: APISlot[]) => {
      const result = mapApiToRoomGrid(data); 
      
      setRooms(result.uniqueRooms);
      setActiveRoom(prev => result.uniqueRooms.includes(prev) ? prev : result.uniqueRooms[0]);

      setAllGrids(result.grids);
      setTimeSlots(result.uniqueTimes);
      setBreakTimes(result.breakTimes);
      
      if (result.uniqueTimes.length > 0) {
        setNewTime(result.uniqueTimes[0]);
      }
  };

  const pushHistory = useCallback(() => {
    setHistory(prev => [
      ...prev.slice(-20), 
      { 
        grids: JSON.parse(JSON.stringify(allGrids)), 
        clipboard: JSON.parse(JSON.stringify(clipboardItems)) 
      }
    ]);
  }, [allGrids, clipboardItems]);

  const handleUndo = () => {
    if (history.length === 0) return;
    const prev = history[history.length - 1];
    setAllGrids(prev.grids);
    setClipboardItems(prev.clipboard);
    setHistory(h => h.slice(0, -1));
  };

  const handleGridChange = useCallback((room: string, newGrid: GridData) => {
    pushHistory();
    setAllGrids(prev => ({ ...prev, [room]: newGrid }));
  }, [pushHistory]);

  const handleDelete = useCallback((room: string, id: string) => {
    pushHistory();
    setAllGrids(prev => {
      const next = { ...prev };
      const grid = { ...next[room] };
      for (const day of DAYS) {
        const daySlots = { ...grid[day] };
        for (const time of timeSlots) {
          if (daySlots[time]?.id === id) {
            delete daySlots[time];
            grid[day] = daySlots;
            next[room] = grid;
            return next;
          }
        }
      }
      return next;
    });
  }, [pushHistory, timeSlots]);

  const handleDeleteByDrag = useCallback((room: string, day: string, time: string) => {
    pushHistory();
    setAllGrids(prev => {
      const next = { ...prev };
      const grid = { ...next[room] };
      const daySlots = { ...grid[day] };
      delete daySlots[time];
      grid[day] = daySlots;
      next[room] = grid;
      return next;
    });
  }, [pushHistory]);

  const handleMoveToClipboard = useCallback((slot: SlotData, fromRoom: string, fromDay: string, fromTime: string) => {
    pushHistory();
    setAllGrids(prev => {
      const next = { ...prev };
      const roomGrid = { ...next[fromRoom] };
      const daySlots = { ...roomGrid[fromDay] };
      
      if (daySlots[fromTime]?.id === slot.id) {
        delete daySlots[fromTime];
        roomGrid[fromDay] = daySlots;
        next[fromRoom] = roomGrid;
      }
      return next;
    });
    setClipboardItems(prev => [...prev, slot]);
  }, [pushHistory]);

  const handleDropFromClipboard = useCallback((slot: SlotData, day: string, time: string, clipboardIndex: number) => {
    pushHistory();
    setAllGrids(prev => {
      const next = { ...prev };
      const roomGrid = { ...next[activeRoom] };
      roomGrid[day] = { ...roomGrid[day], [time]: slot };
      next[activeRoom] = roomGrid;
      return next;
    });
    setClipboardItems(prev => prev.filter((_, i) => i !== clipboardIndex));
  }, [activeRoom, pushHistory]);

  const handleRemoveFromClipboard = useCallback((index: number) => {
    pushHistory();
    setClipboardItems(prev => prev.filter((_, i) => i !== index));
  }, [pushHistory]);

  const handleAddClass = () => {
    if (!newSubject || !newTeacher) return;
    pushHistory();
    const slot: SlotData = {
      id: String(nextId++),
      subject: newSubject,
      teacher: `${newTeacher} (${newSection})`,
      room: activeRoom, // Always assigned to the active room
      credits: newCredits ? Number(newCredits) : undefined,
    };
    setAllGrids(prev => {
      const next = { ...prev };
      if (!activeRoom) return prev;
      const grid = { ...next[activeRoom] };
      if(!grid[newDay]) grid[newDay] = {};
      grid[newDay] = { ...grid[newDay], [newTime]: slot };
      next[activeRoom] = grid;
      return next;
    });
    setNewSubject("");
    setNewTeacher("");
    setNewSection("");
    setNewCredits("");
    setAddModalOpen(false);
  };

  const handleHistoryLoad = (data: APISlot[]) => {
    processAndLoadData(data);
    setHistoryModalOpen(false);
  };

  return (
    <DashboardLayout title="Room Timetable">
      <div className="animate-fade-in space-y-5 pb-20">
        
        <div className="flex flex-wrap items-center w-full gap-3">
          {rooms.length > 0 ? (
             <SectionTabs sections={rooms} active={activeRoom} onChange={setActiveRoom} />
          ) : (
             <div className="text-sm text-muted-foreground italic">No rooms found</div>
          )}
          
          <div className="flex items-center gap-2 ml-auto">
            <DeleteZone 
              onDeleteFromGrid={handleDeleteByDrag} 
              onDeleteFromClipboard={handleRemoveFromClipboard} 
            />
            
            <div className="h-6 w-px bg-border mx-1" />

            <AppButton variant="ghost" size="sm" onClick={() => setHistoryModalOpen(true)} className="flex items-center text-muted-foreground text-[18px] hover:text-foreground">
              <History size={20} className="mr-1.5" /> History
            </AppButton>

            <AppButton variant="ghost" size="lg" onClick={handleUndo} disabled={history.length === 0} className="flex text-[18px] items-center">
              <Undo2 size={20} className="mr-1.5" /> Undo
            </AppButton>
            
            <AppButton variant="outline" size="lg" className="flex items-center justify-center text-[18px] min-w-[140px]" onClick={handleExportExcel}>
              <FileSpreadsheet size={20} className="mr-2 text-green-600" /> Export Excel
            </AppButton>
            
            <AppButton variant="primary" size="lg" onClick={() => setAddModalOpen(true)} className="flex text-[18px] items-center">
              <Plus size={20} className="mr-1.5" /> Add Class
            </AppButton>
          </div>
        </div>

        <div key={activeRoom} className="animate-fade-in">
          {loading ? (
             <div className="flex h-64 w-full items-center justify-center rounded-lg border border-border bg-secondary/20">
               <p className="text-sm text-muted-foreground animate-pulse">Loading room schedule...</p>
             </div>
          ) : (
            activeRoom && allGrids[activeRoom] ? (
                <TimetableGrid
                  section={activeRoom}
                  grid={allGrids[activeRoom]}
                  timeSlots={timeSlots} 
                  breakTimes={breakTimes}
                  onGridChange={(g) => handleGridChange(activeRoom, g)}
                  onDelete={(id) => handleDelete(activeRoom, id)}
                  onDropFromClipboard={handleDropFromClipboard}
                />
            ) : (
                <div className="flex h-64 w-full items-center justify-center rounded-lg border border-border bg-secondary/10">
                   <div className="flex flex-col items-center gap-2 text-muted-foreground">
                      <DoorOpen size={40} strokeWidth={1} />
                      <p className="text-sm">
                        {rooms.length === 0 ? "No room data available." : "Select a room to view occupancy."}
                      </p>
                   </div>
                </div>
            )
          )}
        </div>

        <ClipboardArea 
          items={clipboardItems}
          onDropFromGrid={(slot, fromRoom, fromDay, fromTime) => 
            handleMoveToClipboard(slot, fromRoom, fromDay, fromTime)
          }
          onRemoveItem={handleRemoveFromClipboard}
        />
      </div>

      <Modal
        open={addModalOpen}
        onClose={() => setAddModalOpen(false)}
        title={`Booking for ${activeRoom}`}
        actions={
          <>
            <AppButton variant="ghost" size="sm" onClick={() => setAddModalOpen(false)}>Cancel</AppButton>
            <AppButton variant="primary" size="sm" onClick={handleAddClass}>Book Room</AppButton>
          </>
        }
      >
        <div className="space-y-1">
          <InputField label="Subject" placeholder="e.g. Data Structures" value={newSubject} onChange={setNewSubject} />
          <InputField label="Teacher" placeholder="e.g. Dr. Smith" value={newTeacher} onChange={setNewTeacher} />
          <InputField label="Section" placeholder="e.g. CS-3A" value={newSection} onChange={setNewSection} />
          <InputField label="Credits" type="number" placeholder="3" value={newCredits} onChange={setNewCredits} />
          <div className="grid grid-cols-2 gap-3">
            <div className="mb-5">
              <label className="mb-1.5 block text-xs font-medium uppercase tracking-widest text-muted-foreground">Day</label>
              <select value={newDay} onChange={e => setNewDay(e.target.value)} className="focus-glow w-full border border-border bg-secondary px-4 py-3 text-sm text-foreground outline-none transition-colors duration-200 focus:border-foreground/30">
                {DAYS.map(d => <option key={d} value={d}>{d}</option>)}
              </select>
            </div>
            <div className="mb-5">
              <label className="mb-1.5 block text-xs font-medium uppercase tracking-widest text-muted-foreground">Time</label>
              <select value={newTime} onChange={e => setNewTime(e.target.value)} className="focus-glow w-full border border-border bg-secondary px-4 py-3 text-sm text-foreground outline-none transition-colors duration-200 focus:border-foreground/30">
                {timeSlots.map(t => (
                  <option key={t} value={t}>{formatTimeDisplay(t)}</option>
                ))}
              </select>
            </div>
          </div>
        </div>
      </Modal>

      <HistoryModal 
        open={historyModalOpen} 
        onClose={() => setHistoryModalOpen(false)}
        onLoadRun={handleHistoryLoad}
      />

      <div className="mt-8 border-t border-border pt-6">
        <h3 className="text-lg font-semibold text-foreground mb-2">Room Usage Notice</h3>
        <p className="text-sm text-muted-foreground">
          This view tracks room occupancy. To prevent double-booking, changes should be finalized in the primary Section Timetable.
        </p>
      </div>
    </DashboardLayout>
  );
};

export default RoomTimetable;
