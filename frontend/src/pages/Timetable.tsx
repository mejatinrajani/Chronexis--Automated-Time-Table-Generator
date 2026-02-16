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
import { Undo2, Plus, FileSpreadsheet, History } from "lucide-react";
import { ShieldCheck, AlertTriangle, XCircle, CheckCircle2, Activity } from "lucide-react";
import { validateTimetable, ValidationError } from "@/utils/Validator";
import { SlotData } from "@/components/DraggableSlot";
import { exportTimetableToExcel } from "@/utils/excelExport";
import { mapApiToGrid, APISlot, formatTimeDisplay } from "@/utils/dataMapper";

const DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"];

type GridData = Record<string, Record<string, SlotData | null>>;

let nextId = 100;

const Timetable = () => {
  const [sections, setSections] = useState<string[]>([]);
  const [activeSection, setActiveSection] = useState("");
  const [loading, setLoading] = useState(false);
  const [allGrids, setAllGrids] = useState<Record<string, GridData>>({});

  const [timeSlots, setTimeSlots] = useState<string[]>([]);
  const [breakTimes, setBreakTimes] = useState<string[]>([]);

  const [clipboardItems, setClipboardItems] = useState<SlotData[]>([]);
  const [addModalOpen, setAddModalOpen] = useState(false);
  const [historyModalOpen, setHistoryModalOpen] = useState(false);

  const [newSubject, setNewSubject] = useState("");
  const [newTeacher, setNewTeacher] = useState("");
  const [newRoom, setNewRoom] = useState("");
  const [newCredits, setNewCredits] = useState("");
  const [newDay, setNewDay] = useState(DAYS[0]);
  const [newTime, setNewTime] = useState("");

  const [history, setHistory] = useState<{ grids: Record<string, GridData>, clipboard: SlotData[] }[]>([]);

  const [validationErrors, setValidationErrors] = useState<ValidationError[] | null>(null);

  useEffect(() => {
    const fetchSchedule = async () => {
      setLoading(true);
      try {
        const response = await fetch("http://localhost:8000/api/latest/");
        const result = await response.json();
        
        const data: APISlot[] = Array.isArray(result) ? result : result.schedule; 
        const serverTimeSlots: string[] = Array.isArray(result) ? [] : result.time_slots;

        console.log("✅ API DATA:", data); 
        console.log("✅ SERVER SLOTS:", serverTimeSlots);

        if (Array.isArray(data) && data.length > 0) {
           processAndLoadData(data, serverTimeSlots);
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

  useEffect(() => {
    if (Object.keys(allGrids).length > 0) {
        const errors = validateTimetable(allGrids);
        setValidationErrors(errors);
    }
  }, [allGrids]); 

  const processAndLoadData = (data: APISlot[], forcedSlots?: string[]) => {
      const uniqueSections = Array.from(new Set(data.map((item) => item.section))).sort();
      
      setSections(uniqueSections);
      setActiveSection(prev => uniqueSections.includes(prev) ? prev : uniqueSections[0]);

      const result = mapApiToGrid(data, uniqueSections, forcedSlots); 
      
      console.log("✅ Restoring Timetable...");
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
    exportTimetableToExcel(allGrids, timeSlots, "Student's_Schedules");
  };

  const handleHistoryLoad = (data: APISlot[], forcedSlots?: string[]) => {
    processAndLoadData(data, forcedSlots);
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

        <div className="mt-8 border-t border-border pt-6 transition-all duration-600">
          <div className="flex items-center justify-between mb-4">
             <div>
                <h3 className="text-[25px] font-semibold text-foreground flex items-center gap-2">
                   <ShieldCheck size={30} className="text-primary" /> Live Validator
                   <span className="flex h-4 w-4 relative ml-1">
                      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-80"></span>
                      <span className="relative inline-flex rounded-full h-4 w-4 bg-green-500"></span>
                   </span>
                </h3>
                <p className="text-lg text-muted-foreground">Monitoring clashes and credit hours in real-time.</p>
             </div>
          </div>

          {validationErrors && (
             <div className="animate-fade-in">
                {validationErrors.length === 0 ? (
                   <div className="flex items-center gap-3 rounded-lg border border-green-200 bg-green-50 p-4 text-green-800 transition-all">
                      <CheckCircle2 size={32} />
                      <div>
                         <p className="font-semibold text-[20px]">All Systems Nominal</p>
                         <p className="text-lg opacity-80">No faculty clashes, room conflicts, or credit mismatches detected.</p>
                      </div>
                   </div>
                ) : (
                   <div className="space-y-3">
                      <div className="flex items-center gap-2 text-lg font-medium text-red-600 mb-2 animate-pulse">
                         <Activity size={16} /> Detected {validationErrors.length} Issues
                      </div>
                      
                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                         {validationErrors.map((err) => (
                            <div key={err.id} className={`rounded-md border p-3 shadow-sm transition-all duration-300 ${
                               err.severity === 'critical' 
                               ? 'border-red-200 bg-red-50 hover:bg-red-100' 
                               : 'border-amber-200 bg-amber-50 hover:bg-amber-100'
                            }`}>
                               <div className="flex items-start gap-2">
                                  {err.severity === 'critical' ? (
                                     <XCircle className="text-red-600 mt-0.5 shrink-0" size={25} />
                                  ) : (
                                     <AlertTriangle className="text-amber-600 mt-0.5 shrink-0" size={25} />
                                  )}
                                  <div>
                                     <p className={`text-lg font-bold ${
                                        err.severity === 'critical' ? 'text-red-800' : 'text-amber-800'
                                     }`}>
                                        {err.message}
                                     </p>
                                     {err.details?.map((d, i) => (
                                        <p key={i} className={`text-lg mt-1 ${
                                           err.severity === 'critical' ? 'text-red-600' : 'text-amber-600'
                                        }`}>
                                           {d}
                                        </p>
                                     ))}
                                  </div>
                               </div>
                            </div>
                         ))}
                      </div>
                   </div>
                )}
             </div>
          )}
        </div>
      </div>

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

      <HistoryModal 
        open={historyModalOpen} 
        onClose={() => setHistoryModalOpen(false)}
        onLoadRun={handleHistoryLoad}
      />
    </DashboardLayout>
  );
};

export default Timetable;