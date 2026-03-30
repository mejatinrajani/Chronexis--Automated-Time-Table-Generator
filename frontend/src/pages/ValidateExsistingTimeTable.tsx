import { useState, useCallback, useEffect } from "react";
import * as XLSX from "xlsx";
import DashboardLayout from "@/components/DashboardLayout";
import TimetableGrid from "@/components/TimetableGrid";
import SectionTabs from "@/components/SectionTabs";
import AppButton from "@/components/AppButton";
import Modal from "@/components/Modal";
import InputField from "@/components/InputField";
import ClipboardArea from "@/components/ClipboardArea";
import DeleteZone from "@/components/DeleteZone"; 
import { Undo2, Plus, FileSpreadsheet, Upload, CheckCircle2, Activity, XCircle, AlertTriangle, RefreshCw, ShieldCheck } from "lucide-react";
import { validateExcelTimetable, ExcelValidationError } from "@/utils/excelValidator";
import { SlotData } from "@/components/DraggableSlot";
import { exportTimetableToExcel } from "@/utils/excelExport";
import { toast } from "sonner";

const DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"];

type GridData = Record<string, Record<string, SlotData | null>>;

let nextId = 5000;

const ValidateExsistingTimeTable = () => {
  // --- Upload State --- (Moved INSIDE the component)
  const [isLoaded, setIsLoaded] = useState(false);
  const [fileName, setFileName] = useState<string | null>(null);

  // --- Timetable State ---
  const [sections, setSections] = useState<string[]>([]);
  const [activeSection, setActiveSection] = useState("");
  const [allGrids, setAllGrids] = useState<Record<string, GridData>>({});
  
  const [timeSlots, setTimeSlots] = useState<string[]>([]);
  const [breakTimes, setBreakTimes] = useState<string[]>([]);
  const [clipboardItems, setClipboardItems] = useState<SlotData[]>([]);
  const [addModalOpen, setAddModalOpen] = useState(false);
  
  // Add Form State
  const [newSubject, setNewSubject] = useState("");
  const [newTeacher, setNewTeacher] = useState("");
  const [newRoom, setNewRoom] = useState("");
  const [newCredits, setNewCredits] = useState("");
  const [newDay, setNewDay] = useState(DAYS[0]);
  const [newTime, setNewTime] = useState("");
  
  const [history, setHistory] = useState<{ grids: Record<string, GridData>, clipboard: SlotData[] }[]>([]);
  const [validationErrors, setValidationErrors] = useState<ExcelValidationError[] | null>(null);

  // --- LIVE VALIDATOR ---
  useEffect(() => {
    if (Object.keys(allGrids).length > 0) {
        const errors = validateExcelTimetable(allGrids);
        setValidationErrors(errors);
    }
  }, [allGrids]); 

  // --- EXCEL PARSER ---
  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (!file) return;
      
      // Check if user accidentally uploaded a CSV
      if (file.name.endsWith('.csv')) {
          toast.error("Please upload the full .xlsx workbook, not a single .csv file!");
          return;
      }

      setFileName(file.name);
      const reader = new FileReader();

      reader.onload = (evt) => {
        try {
          const bstr = evt.target?.result;
          const wb = XLSX.read(bstr, { type: "binary" });
          
          const newGrids: Record<string, GridData> = {};
          const parsedSections = wb.SheetNames; // Grabs all sections from XLSX
          let parsedTimeSlots: string[] = [];
          const detectedBreaks: string[] = [];

          // Helper to convert "8:00 AM - 8:50 AM" back to "08:00"
          const reverseParseTime = (header: string) => {
              if (header.toUpperCase().includes("LUNCH") || header.toUpperCase().includes("BREAK")) return header;
              try {
                  const startTimeStr = header.split("-")[0].trim();
                  const [time, period] = startTimeStr.split(" ");
                  let [h, m] = time.split(":").map(Number);
                  if (period.toUpperCase() === "PM" && h !== 12) h += 12;
                  if (period.toUpperCase() === "AM" && h === 12) h = 0;
                  return `${h.toString().padStart(2, "0")}:${m.toString().padStart(2, "0")}`;
              } catch {
                  return header; // Fallback
              }
          };

          parsedSections.forEach(section => {
              const ws = wb.Sheets[section];
              const rows = XLSX.utils.sheet_to_json<string[]>(ws, { header: 1 });
              if (rows.length === 0) return;
            
              // Extract & Reverse Parse Time Headers
              if (parsedTimeSlots.length === 0) {
                  const rawHeaders = rows[0].slice(1).map(String); 
                  parsedTimeSlots = rawHeaders.map(reverseParseTime);
                  
                  parsedTimeSlots.forEach(t => {
                      if (t.toUpperCase().includes("LUNCH") || t.toUpperCase().includes("BREAK")) {
                          detectedBreaks.push(t);
                      }
                  });
              }

              newGrids[section] = {};
              DAYS.forEach(d => newGrids[section][d] = {});

              for (let r = 1; r < rows.length; r++) {
                 const dayStr = String(rows[r][0] || "").trim();
                 if (!DAYS.includes(dayStr)) continue; 

                 for (let c = 1; c < rows[r].length; c++) {
                    const cellVal = String(rows[r][c] || "").trim();
                    const timeKey = parsedTimeSlots[c - 1]; // Uses the clean "08:00" key
                    
                    if (cellVal && timeKey && !detectedBreaks.includes(timeKey)) {
                        const lines = cellVal.split('\n').map(l => l.trim()).filter(Boolean);
                        
                        let subject = lines[0] || "Unknown";
                        let teacher = "TBA";
                        let room = "TBA";
                        let credits = 1;

                        lines.forEach((line, index) => {
                            if (index === 1 && !line.startsWith("Room:")) teacher = line;
                            if (line.startsWith("Room:")) room = line.replace("Room:", "").trim();
                            if (line.includes("cr") || line.includes("credits")) {
                                const match = line.match(/(\d+)/);
                                if (match) credits = parseInt(match[1]);
                            }
                        });

                        newGrids[section][dayStr][timeKey] = {
                           id: `imp-${section}-${dayStr}-${timeKey}-${nextId++}`,
                           subject,
                           teacher,
                           room,
                           credits,
                           duration: 1 
                        };
                    }
                 }
              }
          });

          // Apply Data to State
          setAllGrids(newGrids);
          setSections(parsedSections);
          setActiveSection(parsedSections[0]);
          setTimeSlots(parsedTimeSlots);
          setBreakTimes(detectedBreaks);
          
          if (parsedTimeSlots.length > 0) setNewTime(parsedTimeSlots[0]);
          
          toast.success(`Successfully loaded ${parsedSections.length} sections!`);
          setIsLoaded(true);

        } catch (error) {
          console.error("Excel Parse Error:", error);
          toast.error("Failed to parse Excel. Please ensure it is the correct exported format.");
        }
      };
      reader.readAsBinaryString(file);
  };

  // --- HANDLERS ---
  const pushHistory = useCallback(() => {
    setHistory(prev => [
      ...prev.slice(-20), 
      { grids: JSON.parse(JSON.stringify(allGrids)), clipboard: JSON.parse(JSON.stringify(clipboardItems)) }
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
    exportTimetableToExcel(allGrids, timeSlots, "Validated_Fixed_Schedules");
  };

  const handleReset = () => {
      setIsLoaded(false);
      setFileName(null);
      setAllGrids({});
      setSections([]);
      setClipboardItems([]);
      setHistory([]);
      setValidationErrors(null);
  };

  return (
    <DashboardLayout title="Excel Validator Sandbox">
      <div className="animate-fade-in space-y-5 pb-20">

        {/* --- STATE 1: UPLOAD SCREEN --- */}
        {!isLoaded && (
            <div className="rounded-xl border border-border bg-card p-10 shadow-sm max-w-3xl mx-auto mt-10">
                <div className="text-center mb-8">
                    <h2 className="text-2xl font-bold text-foreground mb-2">Upload Timetable for Validation</h2>
                    <p className="text-muted-foreground">
                        Upload a previously exported Excel file. We will parse it, check for any human errors (clashes, missing credits), and let you fix them interactively.
                    </p>
                </div>

                <div className="border-2 border-dashed border-border rounded-xl p-12 text-center bg-secondary/5 transition-colors hover:bg-secondary/10 relative group">
                    <input 
                        type="file" 
                        accept=".xlsx, .xls"
                        onChange={handleFileUpload}
                        className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10"
                    />
                    <div className="flex flex-col items-center gap-4">
                        <div className="h-16 w-16 rounded-full bg-primary/10 flex items-center justify-center text-primary group-hover:scale-110 transition-transform">
                            <Upload size={32} />
                        </div>
                        <div>
                            <p className="text-xl font-medium text-foreground">
                                {fileName ? fileName : "Click or Drag Excel File Here"}
                            </p>
                            <p className="text-sm text-muted-foreground mt-2">
                                Supports .xlsx and .xls (Exported Format)
                            </p>
                        </div>
                    </div>
                </div>
            </div>
        )}

        {/* --- STATE 2: EDITOR SCREEN --- */}
        {isLoaded && (
            <div className="animate-fade-in space-y-5">
                {/* Sandbox Warning */}
                <div className="bg-amber-50 border border-amber-200 text-amber-800 px-4 py-3 rounded-lg flex items-center justify-between shadow-sm">
                    <div className="flex items-center gap-3">
                        <AlertTriangle size={20} className="text-amber-600" />
                        <div>
                            <p className="font-semibold">Sandbox Mode Active</p>
                            <p className="text-sm opacity-90">Changes made here are not saved to the main database. Export to Excel when finished.</p>
                        </div>
                    </div>
                    <AppButton variant="outline" size="sm" onClick={handleReset} className="border-amber-300 text-amber-700 hover:bg-amber-100">
                        <RefreshCw size={16} className="mr-2" /> Start Over
                    </AppButton>
                </div>

                {/* Toolbar */}
                <div className="flex flex-wrap items-center w-full gap-3">
                    <SectionTabs sections={sections} active={activeSection} onChange={setActiveSection} />
                    
                    <div className="flex items-center gap-2 ml-auto">
                        <DeleteZone 
                            onDeleteFromGrid={handleDeleteByDrag} 
                            onDeleteFromClipboard={handleRemoveFromClipboard} 
                        />
                        <div className="h-6 w-px bg-border mx-1" />
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

                {/* Grid */}
                <div key={activeSection} className="animate-fade-in">
                    {activeSection && allGrids[activeSection] && (
                        <TimetableGrid
                            section={activeSection}
                            grid={allGrids[activeSection]}
                            timeSlots={timeSlots} 
                            breakTimes={breakTimes}
                            onGridChange={(g) => handleGridChange(activeSection, g)}
                            onDelete={() => {}} // Use drag-to-delete instead
                            onDropFromClipboard={handleDropFromClipboard}
                        />
                    )}
                </div>

                <ClipboardArea 
                    items={clipboardItems}
                    onDropFromGrid={(slot, fromSection, fromDay, fromTime) => 
                        handleMoveToClipboard(slot, fromSection, fromDay, fromTime)
                    }
                    onRemoveItem={handleRemoveFromClipboard}
                />

                {/* Live Validator UI */}
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
                            <p className="text-lg text-muted-foreground">Monitoring imported data for clashes and mismatches.</p>
                        </div>
                    </div>

                    {validationErrors && (
                        <div className="animate-fade-in">
                            {validationErrors.length === 0 ? (
                                <div className="flex items-center gap-3 rounded-lg border border-green-200 bg-green-50 p-4 text-green-800 transition-all">
                                    <CheckCircle2 size={32} />
                                    <div>
                                        <p className="font-semibold text-[20px]">Excel Data is Perfect!</p>
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
                                                err.severity === 'critical' ? 'border-red-200 bg-red-50 hover:bg-red-100' : 'border-amber-200 bg-amber-50 hover:bg-amber-100'
                                            }`}>
                                                <div className="flex items-start gap-2">
                                                    {err.severity === 'critical' ? <XCircle className="text-red-600 mt-0.5 shrink-0" size={25} /> : <AlertTriangle className="text-amber-600 mt-0.5 shrink-0" size={25} />}
                                                    <div>
                                                        <p className={`text-lg font-bold ${err.severity === 'critical' ? 'text-red-800' : 'text-amber-800'}`}>
                                                            {err.message}
                                                        </p>
                                                        {err.details?.map((d, i) => (
                                                            <p key={i} className={`text-sm mt-1 ${err.severity === 'critical' ? 'text-red-600' : 'text-amber-600'}`}>{d}</p>
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
        )}

      </div>

      <Modal
        open={addModalOpen}
        onClose={() => setAddModalOpen(false)}
        title="Add Class to Sandbox"
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
              <select value={newDay} onChange={e => setNewDay(e.target.value)} className="focus-glow w-full border border-border bg-secondary px-4 py-3 text-sm text-foreground outline-none transition-colors duration-200 focus:border-foreground/30">
                {DAYS.map(d => <option key={d} value={d}>{d}</option>)}
              </select>
            </div>
            <div className="mb-5">
              <label className="mb-1.5 block text-xs font-medium uppercase tracking-widest text-muted-foreground">Time</label>
              <select value={newTime} onChange={e => setNewTime(e.target.value)} className="focus-glow w-full border border-border bg-secondary px-4 py-3 text-sm text-foreground outline-none transition-colors duration-200 focus:border-foreground/30">
                {timeSlots.map(t => (
                  <option key={t} value={t}>{t}</option>
                ))}
              </select>
            </div>
          </div>
        </div>
      </Modal>

    </DashboardLayout>
  );
};

export default ValidateExsistingTimeTable;