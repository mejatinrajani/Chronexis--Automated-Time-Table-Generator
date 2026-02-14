import { useState, useCallback, useEffect } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import TimetableGrid from "@/components/TimetableGrid";
import SectionTabs from "@/components/SectionTabs";
import AppButton from "@/components/AppButton";
import Modal from "@/components/Modal";
import InputField from "@/components/InputField";
import ClipboardArea from "@/components/ClipboardArea";
import DeleteZone from "@/components/DeleteZone"; 
import HistoryModal from "@/components/HistoryModal"; // NEW COMPONENT
import { Undo2, Plus, FileSpreadsheet, History } from "lucide-react"; // Added History Icon
import { SlotData } from "@/components/DraggableSlot";
import { exportTimetableToExcel } from "@/utils/excelExport";
import { mapApiToGrid, APISlot, formatTimeDisplay } from "@/utils/dataMapper";

const DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"];

type GridData = Record<string, Record<string, SlotData | null>>;

let nextId = 100;

const Timetable = () => {
  // --- State ---
  const [sections, setSections] = useState<string[]>([]);
  const [activeSection, setActiveSection] = useState("");
  const [loading, setLoading] = useState(false);
  const [allGrids, setAllGrids] = useState<Record<string, GridData>>({});
  
  // Dynamic Time & Break Slots
  const [timeSlots, setTimeSlots] = useState<string[]>([]);
  const [breakTimes, setBreakTimes] = useState<string[]>([]); 

  const [clipboardItems, setClipboardItems] = useState<SlotData[]>([]);
  const [addModalOpen, setAddModalOpen] = useState(false);
  const [historyModalOpen, setHistoryModalOpen] = useState(false); // NEW STATE
  
  // Form State
  const [newSubject, setNewSubject] = useState("");
  const [newTeacher, setNewTeacher] = useState("");
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
        
        console.log("✅ RAW API DATA:", data); 

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
      // 1. Extract Sections
      const uniqueSections = Array.from(new Set(data.map((item) => item.section))).sort();
      
      setSections(uniqueSections);
      // Only reset active section if current one is invalid
      setActiveSection(prev => uniqueSections.includes(prev) ? prev : uniqueSections[0]);

      // 2. Map Grid & Detect Times
      const result = mapApiToGrid(data, uniqueSections); 
      
      console.log("✅ Restoring Timetable...");
      setAllGrids(result.grids);
      setTimeSlots(result.uniqueTimes);
      setBreakTimes(result.breakTimes);
      
      // Set default time for the "Add Class" modal
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

  const handleGridChange = useCallback((section: string, newGrid: GridData) => {
    pushHistory();
    setAllGrids(prev => ({ ...prev, [section]: newGrid }));
  }, [pushHistory]);

  const handleDelete = useCallback((section: string, id: string) => {
    pushHistory();
    setAllGrids(prev => {
      const next = { ...prev };
      const grid = { ...next[section] };
      for (const day of DAYS) {
        const daySlots = { ...grid[day] };
        for (const time of timeSlots) {
          if (daySlots[time]?.id === id) {
            delete daySlots[time];
            grid[day] = daySlots;
            next[section] = grid;
            return next;
          }
        }
      }
      return next;
    });
  }, [pushHistory, timeSlots]);

  const handleDeleteByDrag = useCallback((section: string, day: string, time: string) => {
    pushHistory();
    setAllGrids(prev => {
      const next = { ...prev };
      const grid = { ...next[section] };
      const daySlots = { ...grid[day] };
      delete daySlots[time];
      grid[day] = daySlots;
      next[section] = grid;
      return next;
    });
  }, [pushHistory]);

  const handleMoveToClipboard = useCallback((slot: SlotData, fromSection: string, fromDay: string, fromTime: string) => {
    pushHistory();
    setAllGrids(prev => {
      const next = { ...prev };
      const sectionGrid = { ...next[fromSection] };
      const daySlots = { ...sectionGrid[fromDay] };
      
      if (daySlots[fromTime]?.id === slot.id) {
        delete daySlots[fromTime];
        sectionGrid[fromDay] = daySlots;
        next[fromSection] = sectionGrid;
      }
      return next;
    });
    setClipboardItems(prev => [...prev, slot]);
  }, [pushHistory]);

  const handleDropFromClipboard = useCallback((slot: SlotData, day: string, time: string, clipboardIndex: number) => {
    pushHistory();
    setAllGrids(prev => {
      const next = { ...prev };
      const sectionGrid = { ...next[activeSection] };
      sectionGrid[day] = { ...sectionGrid[day], [time]: slot };
      next[activeSection] = sectionGrid;
      return next;
    });
    setClipboardItems(prev => prev.filter((_, i) => i !== clipboardIndex));
  }, [activeSection, pushHistory]);

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
      teacher: newTeacher,
      room: newRoom || undefined,
      credits: newCredits ? Number(newCredits) : undefined,
    };
    setAllGrids(prev => {
      const next = { ...prev };
      if (!activeSection) return prev;
      const grid = { ...next[activeSection] };
      if(!grid[newDay]) grid[newDay] = {};
      grid[newDay] = { ...grid[newDay], [newTime]: slot };
      next[activeSection] = grid;
      return next;
    });
    setNewSubject("");
    setNewTeacher("");
    setNewRoom("");
    setNewCredits("");
    setAddModalOpen(false);
  };

  const handleExportExcel = () => {
    exportTimetableToExcel(allGrids);
  };

  // --- History Handler ---
  const handleHistoryLoad = (data: APISlot[]) => {
    // We use the same helper function to process history data
    processAndLoadData(data);
    setHistoryModalOpen(false);
  };

  return (
    <DashboardLayout title="Timetable">
      <div className="animate-fade-in space-y-5 pb-20">
        
        {/* Toolbar */}
        <div className="flex flex-wrap items-center w-full gap-3">
          {sections.length > 0 ? (
             <SectionTabs sections={sections} active={activeSection} onChange={setActiveSection} />
          ) : (
             <div className="text-sm text-muted-foreground italic">No sections found</div>
          )}
          
          <div className="flex items-center gap-2 ml-auto">
            <DeleteZone 
              onDeleteFromGrid={handleDeleteByDrag} 
              onDeleteFromClipboard={handleRemoveFromClipboard} 
            />
            
            <div className="h-6 w-px bg-border mx-1" />

            {/* NEW: History Button */}
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
        <div key={activeSection} className="animate-fade-in">
          {loading ? (
             <div className="flex h-64 w-full items-center justify-center rounded-lg border border-border bg-secondary/20">
               <p className="text-sm text-muted-foreground animate-pulse">Loading schedule...</p>
             </div>
          ) : (
            activeSection && allGrids[activeSection] ? (
                <TimetableGrid
                  section={activeSection}
                  grid={allGrids[activeSection]}
                  timeSlots={timeSlots} 
                  breakTimes={breakTimes}
                  onGridChange={(g) => handleGridChange(activeSection, g)}
                  onDelete={(id) => handleDelete(activeSection, id)}
                  onDropFromClipboard={handleDropFromClipboard}
                />
            ) : (
                <div className="flex h-64 w-full items-center justify-center rounded-lg border border-border bg-secondary/10">
                   <p className="text-sm text-muted-foreground">
                      {sections.length === 0 ? "No schedule data available." : "Select a section to view timetable."}
                   </p>
                </div>
            )
          )}
        </div>

        <ClipboardArea 
          items={clipboardItems}
          onDropFromGrid={(slot, fromSection, fromDay, fromTime) => 
            handleMoveToClipboard(slot, fromSection, fromDay, fromTime)
          }
          onRemoveItem={handleRemoveFromClipboard}
        />
      </div>

      {/* Add Class Modal */}
      <Modal
        open={addModalOpen}
        onClose={() => setAddModalOpen(false)}
        title="Add Class"
        actions={
          <>
            <AppButton variant="ghost" size="sm" onClick={() => setAddModalOpen(false)}>Cancel</AppButton>
            <AppButton variant="primary" size="sm" onClick={handleAddClass}>Add</AppButton>
          </>
        }
      >
        <div className="space-y-1">
          <InputField label="Subject" placeholder="e.g. Data Structures" value={newSubject} onChange={setNewSubject} />
          <InputField label="Teacher" placeholder="e.g. Dr. Smith" value={newTeacher} onChange={setNewTeacher} />
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

      {/* History Modal */}
      <HistoryModal 
        open={historyModalOpen} 
        onClose={() => setHistoryModalOpen(false)}
        onLoadRun={handleHistoryLoad}
      />
    </DashboardLayout>
  );
};

export default Timetable;