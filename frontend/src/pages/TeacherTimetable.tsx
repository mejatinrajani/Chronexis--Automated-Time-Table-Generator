import { useState, useCallback, useEffect } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import TimetableGrid from "@/components/TimetableGrid";
import SectionTabs from "@/components/SectionTabs"; // Reusing this for Teacher names
import AppButton from "@/components/AppButton";
import Modal from "@/components/Modal";
import InputField from "@/components/InputField";
import ClipboardArea from "@/components/ClipboardArea";
import DeleteZone from "@/components/DeleteZone"; 
import HistoryModal from "@/components/HistoryModal";
import { Undo2, Plus, FileSpreadsheet, History, GraduationCap } from "lucide-react";
import { SlotData } from "@/components/DraggableSlot";
import { exportTimetableToExcel } from "@/utils/excelExport";
import { APISlot, formatTimeDisplay } from "@/utils/dataMapper";
import { mapApiToTeacherGrid } from "@/utils/teacherMapper"; // IMPORT NEW MAPPER

const DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"];

type GridData = Record<string, Record<string, SlotData | null>>;

let nextId = 2000; // Distinct ID range

const TeacherTimetable = () => {
  // --- State ---
  const [teachers, setTeachers] = useState<string[]>([]);
  const [activeTeacher, setActiveTeacher] = useState("");
  const [loading, setLoading] = useState(false);
  const [allGrids, setAllGrids] = useState<Record<string, GridData>>({});
  
  // Dynamic Time & Break Slots
  const [timeSlots, setTimeSlots] = useState<string[]>([]);
  const [breakTimes, setBreakTimes] = useState<string[]>([]); 

  const [clipboardItems, setClipboardItems] = useState<SlotData[]>([]);
  const [addModalOpen, setAddModalOpen] = useState(false);
  const [historyModalOpen, setHistoryModalOpen] = useState(false);
  
  // Form State (Adapted for Teachers)
  const [newSubject, setNewSubject] = useState("");
  const [newSection, setNewSection] = useState(""); // Changed from Teacher to Section
  const [newRoom, setNewRoom] = useState("");
  const [newCredits, setNewCredits] = useState("");
  const [newDay, setNewDay] = useState(DAYS[0]);
  const [newTime, setNewTime] = useState("");

  const [history, setHistory] = useState<{ grids: Record<string, GridData>, clipboard: SlotData[] }[]>([]);

  // --- 1. Fetch Latest Data on Mount ---
  useEffect(() => {
    const fetchSchedule = async () => {
      setLoading(true);
      try {
        const response = await fetch("http://localhost:8000/api/get-schedule/");
        const data: APISlot[] = await response.json();
        
        console.log("✅ RAW API DATA (Teacher View):", data); 

        if (Array.isArray(data) && data.length > 0) {
           processAndLoadData(data);
        } else {
            console.warn("⚠️ API returned empty array");
        }
      } catch (error) {
        console.error("❌ Failed to fetch schedule:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchSchedule();
  }, []);

  // --- Helper to Process API Data ---
  const processAndLoadData = (data: APISlot[]) => {
      // USE NEW TEACHER MAPPER
      const result = mapApiToTeacherGrid(data); 
      
      console.log("✅ Teachers Found:", result.uniqueTeachers);
      
      setTeachers(result.uniqueTeachers);
      // Reset active teacher if invalid
      setActiveTeacher(prev => result.uniqueTeachers.includes(prev) ? prev : result.uniqueTeachers[0]);

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

  // --- Handlers ---

  const handleGridChange = useCallback((teacher: string, newGrid: GridData) => {
    pushHistory();
    setAllGrids(prev => ({ ...prev, [teacher]: newGrid }));
  }, [pushHistory]);

  const handleDelete = useCallback((teacher: string, id: string) => {
    pushHistory();
    setAllGrids(prev => {
      const next = { ...prev };
      const grid = { ...next[teacher] };
      for (const day of DAYS) {
        const daySlots = { ...grid[day] };
        for (const time of timeSlots) {
          if (daySlots[time]?.id === id) {
            delete daySlots[time];
            grid[day] = daySlots;
            next[teacher] = grid;
            return next;
          }
        }
      }
      return next;
    });
  }, [pushHistory, timeSlots]);

  const handleDeleteByDrag = useCallback((teacher: string, day: string, time: string) => {
    pushHistory();
    setAllGrids(prev => {
      const next = { ...prev };
      const grid = { ...next[teacher] };
      const daySlots = { ...grid[day] };
      delete daySlots[time];
      grid[day] = daySlots;
      next[teacher] = grid;
      return next;
    });
  }, [pushHistory]);

  const handleMoveToClipboard = useCallback((slot: SlotData, fromTeacher: string, fromDay: string, fromTime: string) => {
    pushHistory();
    setAllGrids(prev => {
      const next = { ...prev };
      const teacherGrid = { ...next[fromTeacher] };
      const daySlots = { ...teacherGrid[fromDay] };
      
      if (daySlots[fromTime]?.id === slot.id) {
        delete daySlots[fromTime];
        teacherGrid[fromDay] = daySlots;
        next[fromTeacher] = teacherGrid;
      }
      return next;
    });
    setClipboardItems(prev => [...prev, slot]);
  }, [pushHistory]);

  const handleDropFromClipboard = useCallback((slot: SlotData, day: string, time: string, clipboardIndex: number) => {
    pushHistory();
    setAllGrids(prev => {
      const next = { ...prev };
      const teacherGrid = { ...next[activeTeacher] };
      teacherGrid[day] = { ...teacherGrid[day], [time]: slot };
      next[activeTeacher] = teacherGrid;
      return next;
    });
    setClipboardItems(prev => prev.filter((_, i) => i !== clipboardIndex));
  }, [activeTeacher, pushHistory]);

  const handleRemoveFromClipboard = useCallback((index: number) => {
    pushHistory();
    setClipboardItems(prev => prev.filter((_, i) => i !== index));
  }, [pushHistory]);

  const handleAddClass = () => {
    if (!newSubject || !newSection) return; // Validate Section instead of Teacher
    pushHistory();
    const slot: SlotData = {
      id: String(nextId++),
      subject: newSubject,
      teacher: `Section ${newSection}`, // Store Section as "Teacher" for display consistency
      room: newRoom || undefined,
      credits: newCredits ? Number(newCredits) : undefined,
    };
    setAllGrids(prev => {
      const next = { ...prev };
      if (!activeTeacher) return prev;
      const grid = { ...next[activeTeacher] };
      if(!grid[newDay]) grid[newDay] = {};
      grid[newDay] = { ...grid[newDay], [newTime]: slot };
      next[activeTeacher] = grid;
      return next;
    });
    setNewSubject("");
    setNewSection("");
    setNewRoom("");
    setNewCredits("");
    setAddModalOpen(false);
  };

  const handleExportExcel = () => {
    exportTimetableToExcel(allGrids);
  };

  const handleHistoryLoad = (data: APISlot[]) => {
    processAndLoadData(data);
    setHistoryModalOpen(false);
  };

  return (
    <DashboardLayout title="Faculty Timetable">
      <div className="animate-fade-in space-y-5 pb-20">
        
        {/* Toolbar */}
        <div className="flex flex-wrap items-center w-full gap-3">
          {teachers.length > 0 ? (
             <SectionTabs sections={teachers} active={activeTeacher} onChange={setActiveTeacher} />
          ) : (
             <div className="text-sm text-muted-foreground italic">No faculty found</div>
          )}
          
          <div className="flex items-center gap-2 ml-auto">
            <DeleteZone 
              onDeleteFromGrid={handleDeleteByDrag} 
              onDeleteFromClipboard={handleRemoveFromClipboard} 
            />
            
            <div className="h-6 w-px bg-border mx-1" />

            <AppButton 
              variant="ghost" 
              size="sm" 
              onClick={() => setHistoryModalOpen(true)} 
              className="flex items-center text-muted-foreground text-[18px] hover:text-foreground"
            >
              <History size={20} className="mr-1.5" /> History
            </AppButton>

            <AppButton variant="ghost" size="lg" onClick={handleUndo} disabled={history.length === 0} className="flex text-[18px] items-center">
              <Undo2 size={20} className="mr-1.5" /> Undo
            </AppButton>
            
            <AppButton 
              variant="outline" 
              size="lg" 
              className="flex items-center justify-center text-[18px] min-w-[140px]"
              onClick={handleExportExcel}
            >
              <FileSpreadsheet size={20} className="mr-2 text-green-600" /> Export Excel
            </AppButton>
            
            <AppButton variant="primary" size="lg" onClick={() => setAddModalOpen(true)} className="flex text-[18px] items-center">
              <Plus size={20} className="mr-1.5" /> Add Class
            </AppButton>
          </div>
        </div>

        {/* Grid */}
        <div key={activeTeacher} className="animate-fade-in">
          {loading ? (
             <div className="flex h-64 w-full items-center justify-center rounded-lg border border-border bg-secondary/20">
               <p className="text-sm text-muted-foreground animate-pulse">Loading faculty schedule...</p>
             </div>
          ) : (
            activeTeacher && allGrids[activeTeacher] ? (
                <TimetableGrid
                  section={activeTeacher} // Passing Teacher Name as "Section" header
                  grid={allGrids[activeTeacher]}
                  timeSlots={timeSlots} 
                  breakTimes={breakTimes}
                  onGridChange={(g) => handleGridChange(activeTeacher, g)}
                  onDelete={(id) => handleDelete(activeTeacher, id)}
                  onDropFromClipboard={handleDropFromClipboard}
                />
            ) : (
                <div className="flex h-64 w-full items-center justify-center rounded-lg border border-border bg-secondary/10">
                   <div className="flex flex-col items-center gap-2 text-muted-foreground">
                      <GraduationCap size={40} strokeWidth={1} />
                      <p className="text-sm">
                        {teachers.length === 0 ? "No faculty data available." : "Select a professor to view schedule."}
                      </p>
                   </div>
                </div>
            )
          )}
        </div>

        <ClipboardArea 
          items={clipboardItems}
          onDropFromGrid={(slot, fromTeacher, fromDay, fromTime) => 
            handleMoveToClipboard(slot, fromTeacher, fromDay, fromTime)
          }
          onRemoveItem={handleRemoveFromClipboard}
        />
      </div>

      {/* Add Class Modal - MODIFIED FOR TEACHERS */}
      <Modal
        open={addModalOpen}
        onClose={() => setAddModalOpen(false)}
        title={`Add Class for ${activeTeacher}`}
        actions={
          <>
            <AppButton variant="ghost" size="sm" onClick={() => setAddModalOpen(false)}>Cancel</AppButton>
            <AppButton variant="primary" size="sm" onClick={handleAddClass}>Add</AppButton>
          </>
        }
      >
        <div className="space-y-1">
          <InputField label="Subject" placeholder="e.g. Data Structures" value={newSubject} onChange={setNewSubject} />
          
          {/* Changed 'Teacher' input to 'Section' input */}
          <InputField label="Section" placeholder="e.g. CS-3A" value={newSection} onChange={setNewSection} />
          
          <InputField label="Room" placeholder="e.g. R-201" value={newRoom} onChange={setNewRoom} />
          <InputField label="Credits" type="number" placeholder="3" value={newCredits} onChange={setNewCredits} />
          <div className="grid grid-cols-2 gap-3">
            <div className="mb-5">
              <label className="mb-1.5 block text-xs font-medium uppercase tracking-widest text-muted-foreground">Day</label>
              <select
                value={newDay}
                onChange={e => setNewDay(e.target.value)}
                className="focus-glow w-full border border-border bg-secondary px-4 py-3 text-sm text-foreground outline-none transition-colors duration-200 focus:border-foreground/30"
              >
                {DAYS.map(d => <option key={d} value={d}>{d}</option>)}
              </select>
            </div>
            <div className="mb-5">
              <label className="mb-1.5 block text-xs font-medium uppercase tracking-widest text-muted-foreground">Time</label>
              <select
                value={newTime}
                onChange={e => setNewTime(e.target.value)}
                className="focus-glow w-full border border-border bg-secondary px-4 py-3 text-sm text-foreground outline-none transition-colors duration-200 focus:border-foreground/30"
              >
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
    </DashboardLayout>
  );
};

export default TeacherTimetable;