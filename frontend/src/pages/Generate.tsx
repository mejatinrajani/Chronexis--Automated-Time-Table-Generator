import { useState, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import DashboardLayout from "@/components/DashboardLayout";
import InputField from "@/components/InputField";
import AppButton from "@/components/AppButton";
import { Plus, Trash2, LayoutGrid, Users, BookOpen, Layers, Check, X, Zap } from "lucide-react";
import { toast } from "sonner";

// --- Types ---
interface Subject {
  id: string; // Added ID for easier linking
  name: string;
  credits: number;
  isLab: boolean;
}

interface RoomBlock {
  block: string;
  start: number;
  end: number;
}

interface Faculty {
  id: string;
  name: string;
  subjects: string[]; // List of subject names
}

const Generate = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);

  // 1. Time Config
  const [startTime, setStartTime] = useState("09:00");
  const [endTime, setEndTime] = useState("17:00");
  const [duration, setDuration] = useState("50");

  // 2. Subjects
  const [subjects, setSubjects] = useState<Subject[]>([
    { id: "sub-1", name: "", credits: 3, isLab: false }
  ]);

  // 3. Rooms
  const [rooms, setRooms] = useState<RoomBlock[]>([{ block: "AB1", start: 101, end: 110 }]);

  // 4. Faculty
  const [faculty, setFaculty] = useState<Faculty[]>([
    { id: "fac-1", name: "", subjects: [] }
  ]);

  // 5. Sections (Hybrid State)
  const [sectionPrefix, setSectionPrefix] = useState("CS-3");
  const [sectionStart, setSectionStart] = useState("A");
  const [sectionEnd, setSectionEnd] = useState("E");
  const [customSections, setCustomSections] = useState<string[]>([]); // For manual adds like "3AA"
  const [newCustomSection, setNewCustomSection] = useState("");

  // --- Derived State (Memoized) ---
  const validSubjectNames = useMemo(() => 
    subjects.filter(s => s.name.trim() !== "").map(s => s.name), 
  [subjects]);

  const generatedSectionList = useMemo(() => {
    const list = [...customSections];
    const startCode = sectionStart.charCodeAt(0);
    const endCode = sectionEnd.charCodeAt(0);
    
    if (endCode >= startCode) {
      for (let i = startCode; i <= endCode; i++) {
        list.unshift(`${sectionPrefix}${String.fromCharCode(i)}`);
      }
    }
    return Array.from(new Set(list)); // Remove duplicates
  }, [sectionPrefix, sectionStart, sectionEnd, customSections]);

  // --- Handlers ---

  const handleGenerate = async () => {
    const validSubjects = subjects.filter(s => s.name.trim());
    const validRooms = rooms.filter(r => r.block.trim());
    const validFaculty = faculty.filter(f => f.name.trim());

    if (validSubjects.length === 0 || validRooms.length === 0 || validFaculty.length === 0) {
        toast.error("Please fill in all required fields.");
        return;
    }

    if (generatedSectionList.length === 0) {
        toast.error("Please define at least one section.");
        return;
    }

    const payload = {
        start_time: startTime,
        end_time: endTime,
        duration: parseInt(duration),
        subjects: validSubjects.map(s => ({ name: s.name, credits: s.credits, is_lab: s.isLab })),
        rooms: validRooms.map(r => ({ block: r.block, start: r.start, end: r.end })),
        faculty: validFaculty.map(f => ({ name: f.name, subjects: f.subjects })),
        sections: generatedSectionList
    };

    setLoading(true);
    try {
        const response = await fetch("http://localhost:8000/api/generate/", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        if (response.ok) {
            toast.success("Timetable Generated Successfully!");
            navigate("/timetable"); 
        } else {
            const err = await response.json();
            toast.error(`Generation Failed: ${err.detail}`);
        }
    } catch (e) {
        toast.error("Server Error. Is the backend running?");
    } finally {
        setLoading(false);
    }
  };

  // --- List Management ---

  const addCustomSection = () => {
    if (newCustomSection && !customSections.includes(newCustomSection)) {
      setCustomSections([...customSections, newCustomSection]);
      setNewCustomSection("");
    }
  };

  const removeCustomSection = (sec: string) => {
    setCustomSections(customSections.filter(s => s !== sec));
  };

  const updateFaculty = (i: number, val: string) => {
    const newFac = [...faculty];
    newFac[i].name = val;
    setFaculty(newFac);
  };

  const toggleFacSubject = (facIndex: number, subjectName: string) => {
    const newFac = [...faculty];
    const currentSubjects = newFac[facIndex].subjects;
    
    if (currentSubjects.includes(subjectName)) {
        newFac[facIndex].subjects = currentSubjects.filter(s => s !== subjectName);
    } else {
        newFac[facIndex].subjects.push(subjectName);
    }
    setFaculty(newFac);
  };

  return (
    <DashboardLayout title="Setup & Generate">
      <div className="mx-auto max-w-5xl space-y-8 pb-32 animate-fade-in">
        
        {/* 1. TIME CONFIG */}
        <div className="rounded-xl border border-border bg-card p-6 shadow-sm">
            <h3 className="mb-5 flex items-center gap-3 text-lg font-semibold uppercase tracking-wider text-muted-foreground">
                <LayoutGrid size={20} /> Time Settings
            </h3>
            <div className="grid grid-cols-1 gap-6 sm:grid-cols-3">
                <InputField label="Start Time" type="time" value={startTime} onChange={setStartTime} />
                <InputField label="End Time" type="time" value={endTime} onChange={setEndTime} />
                <InputField label="Slot Duration (min)" type="number" value={duration} onChange={setDuration} />
            </div>
        </div>

        {/* 2. SUBJECTS */}
        <div className="rounded-xl border border-border bg-card p-6 shadow-sm">
            <div className="mb-5 flex items-center justify-between">
                <h3 className="flex items-center gap-3 text-lg font-semibold uppercase tracking-wider text-muted-foreground">
                    <BookOpen size={20} /> Subjects
                </h3>
                <AppButton variant="ghost" onClick={() => setSubjects([...subjects, { id: `sub-${Date.now()}`, name: "", credits: 3, isLab: false }])}>
                    <Plus size={18} className="mr-2"/> Add Subject
                </AppButton>
            </div>
            <div className="space-y-4">
                {subjects.map((sub, i) => (
                    <div key={sub.id} className="flex items-end gap-4 p-4 border border-border rounded-lg bg-secondary/10 hover:bg-secondary/20 transition-colors">
                        <div className="flex-1">
                            <InputField label={i === 0 ? "Subject Name" : ""} placeholder="e.g. Operating Systems" value={sub.name} onChange={(v) => {
                                const newSubs = [...subjects];
                                newSubs[i].name = v;
                                setSubjects(newSubs);
                            }} />
                        </div>
                        <div className="w-32">
                            <InputField label={i === 0 ? "Credits" : ""} type="number" value={String(sub.credits)} onChange={(v) => {
                                const newSubs = [...subjects];
                                newSubs[i].credits = Number(v);
                                setSubjects(newSubs);
                            }} />
                        </div>
                        <div className="flex items-center mb-2 h-[60px] pb-1">
                            <label className="flex items-center gap-3 cursor-pointer px-4 py-2.5 rounded-md border border-border bg-background hover:border-primary/50 transition-all">
                                <input 
                                    type="checkbox" 
                                    checked={sub.isLab} 
                                    onChange={(e) => {
                                        const newSubs = [...subjects];
                                        newSubs[i].isLab = e.target.checked;
                                        setSubjects(newSubs);
                                    }} 
                                    className="w-5 h-5 accent-primary rounded cursor-pointer" 
                                />
                                <span className="text-sm font-medium text-foreground">Lab Subject</span>
                            </label>
                        </div>
                        <button onClick={() => setSubjects(subjects.filter((_, idx) => idx !== i))} className="mb-3 p-2 text-muted-foreground hover:text-red-500 transition-colors">
                            <Trash2 size={20} />
                        </button>
                    </div>
                ))}
            </div>
        </div>

        {/* 3. ROOMS */}
        <div className="rounded-xl border border-border bg-card p-6 shadow-sm">
            <div className="mb-5 flex items-center justify-between">
                <h3 className="flex items-center gap-3 text-lg font-semibold uppercase tracking-wider text-muted-foreground">
                    <LayoutGrid size={20} /> Rooms
                </h3>
                <AppButton variant="ghost" onClick={() => setRooms([...rooms, { block: "AB1", start: 101, end: 110 }])}>
                    <Plus size={18} className="mr-2" /> Add Block
                </AppButton>
            </div>
            <div className="space-y-4">
                {rooms.map((room, i) => (
                    <div key={i} className="flex items-end gap-4 p-4 border border-border rounded-lg bg-secondary/10">
                        <div className="w-48">
                            <InputField label={i === 0 ? "Block Name" : ""} placeholder="e.g. AB-1" value={room.block} onChange={(v) => {
                                const newRooms = [...rooms];
                                newRooms[i].block = v;
                                setRooms(newRooms);
                            }} />
                        </div>
                        <div className="flex-1">
                            <div className="flex items-end gap-3 bg-background border border-border rounded-md px-4 py-2.5">
                                <div className="flex-1">
                                    <span className="text-xs text-muted-foreground uppercase tracking-wider mb-1 block">Start Room</span>
                                    <input 
                                        type="number" 
                                        className="w-full bg-transparent border-b-2 border-border focus:border-primary outline-none text-lg font-medium text-center py-1" 
                                        value={room.start} 
                                        onChange={(e) => {
                                            const newRooms = [...rooms];
                                            newRooms[i].start = Number(e.target.value);
                                            setRooms(newRooms);
                                        }}
                                    />
                                </div>
                                <span className="pb-2 text-muted-foreground font-bold text-xl">→</span>
                                <div className="flex-1">
                                    <span className="text-xs text-muted-foreground uppercase tracking-wider mb-1 block">End Room</span>
                                    <input 
                                        type="number" 
                                        className="w-full bg-transparent border-b-2 border-border focus:border-primary outline-none text-lg font-medium text-center py-1" 
                                        value={room.end} 
                                        onChange={(e) => {
                                            const newRooms = [...rooms];
                                            newRooms[i].end = Number(e.target.value);
                                            setRooms(newRooms);
                                        }}
                                    />
                                </div>
                            </div>
                        </div>
                        <div className="flex items-center justify-center h-[50px] px-4 min-w-[120px] bg-secondary/20 rounded-md border border-border/50">
                             <span className="text-sm font-medium text-muted-foreground">
                                {room.end >= room.start ? `${room.end - room.start + 1} Rooms` : "Invalid Range"}
                             </span>
                        </div>
                        <button onClick={() => setRooms(rooms.filter((_, idx) => idx !== i))} className="mb-3 p-2 text-muted-foreground hover:text-red-500 transition-colors">
                            <Trash2 size={20} />
                        </button>
                    </div>
                ))}
            </div>
        </div>

        {/* 4. FACULTY (With Subject Linking) */}
        <div className="rounded-xl border border-border bg-card p-6 shadow-sm">
            <div className="mb-5 flex items-center justify-between">
                <h3 className="flex items-center gap-3 text-lg font-semibold uppercase tracking-wider text-muted-foreground">
                    <Users size={20} /> Faculty
                </h3>
                <AppButton variant="ghost" onClick={() => setFaculty([...faculty, { id: `fac-${Date.now()}`, name: "", subjects: [] }])}>
                    <Plus size={18} className="mr-2" /> Add Faculty
                </AppButton>
            </div>
            
            <div className="space-y-6">
                {faculty.map((fac, i) => (
                    <div key={fac.id} className="flex flex-col gap-4 p-5 border border-border rounded-xl bg-secondary/10 hover:bg-secondary/20 transition-all">
                        <div className="flex items-start gap-4">
                            <div className="w-1/3">
                                <InputField label={i === 0 ? "Faculty Name" : ""} placeholder="e.g. Dr. A.P.J. Abdul Kalam" value={fac.name} onChange={(v) => updateFaculty(i, v)} />
                            </div>
                            
                            {/* Subject Selection Area */}
                            <div className="flex-1">
                                {i === 0 && <label className="mb-2 block text-sm font-medium text-muted-foreground">Teaches Subjects (Click to Select)</label>}
                                
                                {validSubjectNames.length === 0 ? (
                                    <div className="h-[50px] flex items-center px-4 rounded-md border border-dashed border-border text-muted-foreground bg-background/50">
                                        <span className="text-sm italic">Add subjects in the section above first.</span>
                                    </div>
                                ) : (
                                    <div className="flex flex-wrap gap-2 min-h-[50px] p-2 bg-background border border-border rounded-md">
                                        {validSubjectNames.map(subName => {
                                            const isSelected = fac.subjects.includes(subName);
                                            return (
                                                <button
                                                    key={subName}
                                                    onClick={() => toggleFacSubject(i, subName)}
                                                    className={`
                                                        group flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-medium border transition-all duration-200
                                                        ${isSelected 
                                                            ? "bg-primary text-primary-foreground border-primary shadow-sm" 
                                                            : "bg-secondary text-muted-foreground border-transparent hover:border-border hover:bg-secondary/80"
                                                        }
                                                    `}
                                                >
                                                    {subName}
                                                    {isSelected && <Check size={14} />}
                                                </button>
                                            );
                                        })}
                                    </div>
                                )}
                            </div>

                            <button onClick={() => setFaculty(faculty.filter((_, idx) => idx !== i))} className="mt-8 p-2 text-muted-foreground hover:text-red-500 transition-colors">
                                <Trash2 size={20} />
                            </button>
                        </div>
                    </div>
                ))}
            </div>
        </div>

        {/* 5. SECTIONS (Hybrid: Slider + Custom) */}
        <div className="rounded-xl border border-border bg-card p-6 shadow-sm">
            <h3 className="mb-5 flex items-center gap-3 text-lg font-semibold uppercase tracking-wider text-muted-foreground">
                <Layers size={20} /> Sections
            </h3>
            
            {/* A. Standard Range Generator */}
            <div className="mb-6 p-5 bg-secondary/10 rounded-lg border border-border">
                <div className="flex items-end gap-6">
                    <div className="w-40">
                        <InputField label="Series Prefix" value={sectionPrefix} onChange={setSectionPrefix} placeholder="e.g. CS-3" />
                    </div>
                    <div className="flex-1">
                        <label className="text-sm font-medium text-muted-foreground mb-3 block">Auto-Generate Series (A - Z)</label>
                        <div className="flex items-center gap-4 bg-background p-3 rounded-md border border-border">
                            <input 
                                type="range" min="65" max="90" value={sectionStart.charCodeAt(0)} 
                                onChange={(e) => setSectionStart(String.fromCharCode(Number(e.target.value)))}
                                className="flex-1 accent-primary h-2 bg-secondary rounded-lg appearance-none cursor-pointer"
                            />
                            <span className="font-mono font-bold text-2xl text-primary w-10 text-center">{sectionStart}</span>
                            <span className="text-muted-foreground font-medium">to</span>
                            <span className="font-mono font-bold text-2xl text-primary w-10 text-center">{sectionEnd}</span>
                            <input 
                                type="range" min="65" max="90" value={sectionEnd.charCodeAt(0)} 
                                onChange={(e) => setSectionEnd(String.fromCharCode(Number(e.target.value)))}
                                className="flex-1 accent-primary h-2 bg-secondary rounded-lg appearance-none cursor-pointer"
                            />
                        </div>
                    </div>
                </div>
            </div>

            {/* B. Custom Sections */}
            <div className="p-5 bg-secondary/10 rounded-lg border border-border">
                <label className="text-sm font-medium text-muted-foreground mb-3 block">Add Custom Sections (e.g. 3AA, 3AB)</label>
                <div className="flex gap-3 mb-4">
                    <div className="w-64">
                        <InputField 
                            label="" 
                            placeholder="Type section name..." 
                            value={newCustomSection} 
                            onChange={setNewCustomSection} 
                        />
                    </div>
                    <AppButton onClick={addCustomSection} className="h-10 mt-2" disabled={!newCustomSection}>
                        Add Section
                    </AppButton>
                </div>

                {/* List Preview */}
                <div className="mt-4">
                    <p className="text-xs uppercase tracking-widest text-muted-foreground mb-2">
                        Total Sections to Generate: {generatedSectionList.length}
                    </p>
                    <div className="flex flex-wrap gap-2 max-h-[150px] overflow-y-auto p-2 border border-border rounded-md bg-background">
                        {generatedSectionList.length === 0 ? (
                            <span className="text-sm text-muted-foreground italic p-2">No sections defined yet.</span>
                        ) : (
                            generatedSectionList.map((sec) => (
                                <div key={sec} className="group relative px-3 py-1.5 bg-secondary text-foreground text-sm font-medium rounded-md border border-border">
                                    {sec}
                                    {/* Only allow deleting custom ones from this view? Or maybe just show read-only list for generated ones */}
                                    {customSections.includes(sec) && (
                                        <button 
                                            onClick={() => removeCustomSection(sec)}
                                            className="ml-2 text-muted-foreground hover:text-red-500"
                                        >
                                            <X size={12} />
                                        </button>
                                    )}
                                </div>
                            ))
                        )}
                    </div>
                </div>
            </div>
        </div>

        {/* SUBMIT BUTTON */}
        <div className="fixed bottom-6 left-0 right-0 flex justify-center z-50">
            <AppButton 
                className="w-full max-w-xl h-16 text-xl font-bold shadow-2xl shadow-primary/30 hover:scale-[1.01] transition-transform flex items-center justify-center"
                variant="primary" 
                onClick={handleGenerate}
                disabled={loading}
            >
                {loading ? (
                    <span className="flex items-center justify-center gap-3">
                        <span className="animate-spin rounded-full h-6 w-6 border-b-2 border-white"></span>
                        Running Solver... (Please wait ~30s)
                    </span>
                ) : (
                    <span className="flex items-center justify-center gap-3">
                        <Zap size={24} fill="currentColor" />
                        Launch Timetable Generator
                        <Zap size={24} fill="currentColor" />
                    </span>
                )}
            </AppButton>
        </div>
      </div>
    </DashboardLayout>
  );
};

export default Generate;