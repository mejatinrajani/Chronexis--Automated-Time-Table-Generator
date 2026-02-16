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
import { Undo2, Plus, FileSpreadsheet, History, GraduationCap, XCircle, AlertTriangle, Activity, ShieldCheck, CheckCircle2 } from "lucide-react";
import { SlotData } from "@/components/DraggableSlot";
import { APISlot, formatTimeDisplay } from "@/utils/dataMapper";
import { mapApiToTeacherGrid } from "@/utils/teacherMapper";
import { validateTimetable, ValidationError } from "@/utils/Validator";
import { exportTimetableToExcel } from "@/utils/excelExport";

const DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"];

type GridData = Record<string, Record<string, SlotData | null>>;

let nextId = 2000; 

const TeacherTimetable = () => {
  const [teachers, setTeachers] = useState<string[]>([]);
  const [activeTeacher, setActiveTeacher] = useState("");
  const [loading, setLoading] = useState(false);
  const [allGrids, setAllGrids] = useState<Record<string, GridData>>({});
  const [validationErrors, setValidationErrors] = useState<ValidationError[] | null>(null);
  
  const [timeSlots, setTimeSlots] = useState<string[]>([]);
  const [breakTimes, setBreakTimes] = useState<string[]>([]); 

  const [clipboardItems, setClipboardItems] = useState<SlotData[]>([]);
  const [addModalOpen, setAddModalOpen] = useState(false);
  const [historyModalOpen, setHistoryModalOpen] = useState(false);
  
  const [newSubject, setNewSubject] = useState("");
  const [newSection, setNewSection] = useState("");
  const [newRoom, setNewRoom] = useState("");
  const [newCredits, setNewCredits] = useState("");
  const [newDay, setNewDay] = useState(DAYS[0]);
  const [newTime, setNewTime] = useState("");

  const [history, setHistory] = useState<{ grids: Record<string, GridData>, clipboard: SlotData[] }[]>([]);

  useEffect(() => {
    const fetchSchedule = async () => {
      setLoading(true);
      try {
        const response = await fetch("http://localhost:8000/api/latest/");
        const result = await response.json();
        
        const data: APISlot[] = Array.isArray(result) ? result : result.schedule; 
        
        console.log("RAW API DATA (Teacher View):", data); 

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

  useEffect(() => {
    if (Object.keys(allGrids).length > 0) {
        const errors = validateTimetable(allGrids);
        setValidationErrors(errors);
    }
  }, [allGrids]); 

  const handleExportExcel = () => {
    exportTimetableToExcel(allGrids, timeSlots, "Faculty_Schedules");
  };

  const processAndLoadData = (data: APISlot[]) => {
      const result = mapApiToTeacherGrid(data); 
      
      console.log("✅ Teachers Found:", result.uniqueTeachers);
      
      setTeachers(result.uniqueTeachers);
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
                  section={activeTeacher}
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

       <div className="mt-8 border-t border-border pt-6 transition-all duration-300">
          <div className="flex items-center justify-between mb-4">
             <div>
                <h3 className="text-lg font-semibold text-foreground flex items-center gap-2">
                   <ShieldCheck className="text-primary" /> Live Validator
                   <span className="flex h-2 w-2 relative ml-1">
                      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                      <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
                   </span>
                </h3>
                <p className="text-sm text-muted-foreground">Monitoring faculty double-booking and room clashes.</p>
             </div>
          </div>

          {validationErrors && (
             <div className="animate-fade-in">
                {validationErrors.length === 0 ? (
                   <div className="flex items-center gap-3 rounded-lg border border-green-200 bg-green-50 p-4 text-green-800">
                      <CheckCircle2 size={24} />
                      <div><p className="font-semibold">All Systems Nominal</p></div>
                   </div>
                ) : (
                   <div className="space-y-3">
                      <div className="flex items-center gap-2 text-sm font-medium text-red-600 mb-2 animate-pulse">
                         <Activity size={16} /> Detected {validationErrors.length} Issues
                      </div>
                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                         {validationErrors.map((err) => (
                            <div key={err.id} className={`rounded-md border p-3 shadow-sm ${err.severity === 'critical' ? 'border-red-200 bg-red-50' : 'border-amber-200 bg-amber-50'}`}>
                               <div className="flex items-start gap-2">
                                  {err.severity === 'critical' ? <XCircle className="text-red-600" size={16} /> : <AlertTriangle className="text-amber-600" size={16} />}
                                  <div>
                                     <p className="text-sm font-bold text-red-800">{err.message}</p>
                                     {err.details?.map((d, i) => <p key={i} className="text-xs mt-1 text-red-600">{d}</p>)}
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
    </DashboardLayout>
  );
};

export default TeacherTimetable;