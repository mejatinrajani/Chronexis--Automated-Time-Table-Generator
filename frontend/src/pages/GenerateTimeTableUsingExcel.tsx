import { useState, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import * as XLSX from "xlsx"; // Import Excel Parser
import DashboardLayout from "@/components/DashboardLayout";
import InputField from "@/components/InputField";
import AppButton from "@/components/AppButton";
import { LayoutGrid, Layers, Zap, Upload, FileSpreadsheet, AlertCircle, Check, X } from "lucide-react";
import { toast } from "sonner";

interface Subject {
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
  name: string;
  subjects: string[];
}

interface ExcelRow {
  "Faculty Name": string;
  "Subject": string;
  "Credits": number;
  "Is Lab": string | boolean; // Can be "Yes"/"No" or TRUE/FALSE
}

const GenerateTimetableUsingExcel = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [startTime, setStartTime] = useState("09:00");
  const [endTime, setEndTime] = useState("17:00");
  const [duration, setDuration] = useState("50");
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [faculty, setFaculty] = useState<Faculty[]>([]);
  const [fileName, setFileName] = useState<string | null>(null);
  const [rooms, setRooms] = useState<RoomBlock[]>([{ block: "AB1", start: 101, end: 110 }]);

  // 4. Sections
  const [sectionPrefix, setSectionPrefix] = useState("CS-3");
  const [sectionStart, setSectionStart] = useState("A");
  const [sectionEnd, setSectionEnd] = useState("E");
  const [customSections, setCustomSections] = useState<string[]>([]);
  const [newCustomSection, setNewCustomSection] = useState("");
  const generatedSectionList = useMemo(() => {
    const list = [...customSections];
    const startCode = sectionStart.charCodeAt(0);
    const endCode = sectionEnd.charCodeAt(0);
    
    if (endCode >= startCode) {
      for (let i = startCode; i <= endCode; i++) {
        list.unshift(`${sectionPrefix}${String.fromCharCode(i)}`);
      }
    }
    return Array.from(new Set(list));
  }, [sectionPrefix, sectionStart, sectionEnd, customSections]);
  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setFileName(file.name);

    const reader = new FileReader();
    reader.onload = (evt) => {
      try {
        const bstr = evt.target?.result;
        const wb = XLSX.read(bstr, { type: "binary" });
        const wsName = wb.SheetNames[0];
        const ws = wb.Sheets[wsName];
        
        // Parse JSON
        const data = XLSX.utils.sheet_to_json<ExcelRow>(ws);

        // Process Data
        const uniqueSubjects = new Map<string, Subject>();
        const uniqueFaculty = new Map<string, Set<string>>();

        data.forEach((row) => {
            const facName = row["Faculty Name"]?.trim();
            const subName = row["Subject"]?.trim();
            const credits = Number(row["Credits"]) || 3;
            let isLab = false;
            const rawLab = row["Is Lab"];
            if (typeof rawLab === 'string') {
                isLab = rawLab.toLowerCase() === 'yes' || rawLab.toLowerCase() === 'true';
            } else if (typeof rawLab === 'boolean') {
                isLab = rawLab;
            }

            if (!facName || !subName) return;

            if (!uniqueSubjects.has(subName)) {
                uniqueSubjects.set(subName, { name: subName, credits, isLab });
            }
            if (!uniqueFaculty.has(facName)) {
                uniqueFaculty.set(facName, new Set());
            }
            uniqueFaculty.get(facName)?.add(subName);
        });
        setSubjects(Array.from(uniqueSubjects.values()));
        
        const facultyList: Faculty[] = [];
        uniqueFaculty.forEach((subs, name) => {
            facultyList.push({ name, subjects: Array.from(subs) });
        });
        setFaculty(facultyList);

        toast.success(`Parsed ${data.length} rows successfully!`);

      } catch (error) {
        console.error("Excel Error:", error);
        toast.error("Failed to parse Excel file. Check format.");
      }
    };
    reader.readAsBinaryString(file);
  };
  const handleGenerate = async () => {
    const validRooms = rooms.filter(r => r.block.trim());

    if (subjects.length === 0 || faculty.length === 0) {
        toast.error("Please upload a valid Excel file first.");
        return;
    }

    if (validRooms.length === 0) {
        toast.error("Please add at least one Room Block.");
        return;
    }

    if (generatedSectionList.length === 0) {
        toast.error("Please define at least one section.");
        return;
    }
    const formattedSubjects = subjects.map(sub => ({
        name: sub.name,
        credits: sub.credits,
        is_lab: sub.isLab
    }));

    const payload = {
        start_time: startTime,
        end_time: endTime,
        duration: parseInt(duration),
        subjects: formattedSubjects,
        rooms: validRooms,
        faculty: faculty,
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
            navigate("/student-timetable"); 
        } else {
            const err = await response.json();
            if (Array.isArray(err.detail)) {
                 const msgs = err.detail.map((e: any) => `${e.loc[e.loc.length-1]}: ${e.msg}`).join(", ");
                 toast.error(`Validation Error: ${msgs}`);
                 console.error("Validation Details:", err.detail);
            } else {
                 toast.error(`Generation Failed: ${err.detail}`);
            }
        }
    } catch (e) {
        toast.error("Server Error. Is the backend running?");
        console.error(e);
    } finally {
        setLoading(false);
    }
  };

  const addCustomSection = () => {
    if (newCustomSection && !customSections.includes(newCustomSection)) {
      setCustomSections([...customSections, newCustomSection]);
      setNewCustomSection("");
    }
  };

  const removeCustomSection = (sec: string) => {
    setCustomSections(customSections.filter(s => s !== sec));
  };

  return (
    <DashboardLayout title="Import & Generate">
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

        {/* 2. EXCEL UPLOAD SECTION */}
        <div className="rounded-xl border border-border bg-card p-6 shadow-sm">
            <div className="mb-4 flex items-center justify-between">
                <h3 className="flex items-center gap-3 text-lg font-semibold uppercase tracking-wider text-muted-foreground">
                    <FileSpreadsheet size={20} /> Data Import
                </h3>
                <div className="text-xs text-muted-foreground bg-secondary/50 px-3 py-1 rounded-md">
                    Required Columns: <strong>Faculty Name, Subject, Credits, Is Lab</strong>
                </div>
            </div>

            <div className="border-2 border-dashed border-border rounded-xl p-8 text-center bg-secondary/5 transition-colors hover:bg-secondary/10 relative group">
                <input 
                    type="file" 
                    accept=".xlsx, .xls"
                    onChange={handleFileUpload}
                    className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10"
                />
                <div className="flex flex-col items-center gap-3">
                    <div className="h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center text-primary group-hover:scale-110 transition-transform">
                        <Upload size={24} />
                    </div>
                    <div>
                        <p className="text-lg font-medium text-foreground">
                            {fileName ? fileName : "Click to Upload Excel File"}
                        </p>
                        <p className="text-sm text-muted-foreground mt-1">
                            Supports .xlsx and .xls
                        </p>
                    </div>
                </div>
            </div>
            {subjects.length > 0 && (
                <div className="mt-8 animate-fade-in">
                    <h4 className="text-sm font-semibold mb-3 flex items-center gap-2">
                        <Check size={16} className="text-green-500"/>
                        Successfully Loaded Data
                    </h4>
                    <div className="border border-border rounded-lg overflow-hidden">
                        <div className="grid grid-cols-12 bg-secondary/40 p-3 text-xs font-bold uppercase tracking-wider text-muted-foreground border-b border-border">
                            <div className="col-span-3">Faculty Name</div>
                            <div className="col-span-4">Subject</div>
                            <div className="col-span-2 text-center">Credits</div>
                            <div className="col-span-3 text-center">Type</div>
                        </div>
                        <div className="max-h-[300px] overflow-y-auto">
                            {faculty.map((fac, i) => (
                                fac.subjects.map((subName, j) => {
                                    // Find subject details for display
                                    const subDetails = subjects.find(s => s.name === subName);
                                    return (
                                        <div key={`${i}-${j}`} className="grid grid-cols-12 p-3 text-sm border-b border-border/50 hover:bg-secondary/10 last:border-0 items-center">
                                            <div className="col-span-3 font-medium text-foreground truncate pr-2">{fac.name}</div>
                                            <div className="col-span-4 text-muted-foreground truncate pr-2">{subName}</div>
                                            <div className="col-span-2 text-center text-muted-foreground">{subDetails?.credits || '-'}</div>
                                            <div className="col-span-3 text-center">
                                                {subDetails?.isLab ? (
                                                    <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-purple-100 text-purple-800">
                                                        LAB
                                                    </span>
                                                ) : (
                                                    <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-800">
                                                        THEORY
                                                    </span>
                                                )}
                                            </div>
                                        </div>
                                    );
                                })
                            ))}
                        </div>
                        <div className="bg-secondary/20 p-2 text-xs text-center text-muted-foreground">
                            Total: {faculty.length} Faculty, {subjects.length} Subjects found.
                        </div>
                    </div>
                </div>
            )}
        </div>
        <div className="rounded-xl border border-border bg-card p-6 shadow-sm">
            <div className="mb-5 flex items-center justify-between">
                <h3 className="flex items-center gap-3 text-lg font-semibold uppercase tracking-wider text-muted-foreground">
                    <LayoutGrid size={20} /> Rooms
                </h3>
            </div>
            <div className="space-y-4">
                 {rooms.map((room, i) => (
                    <div key={i} className="flex items-end gap-4 p-4 border border-border rounded-lg bg-secondary/10">
                        <div className="w-48">
                            <InputField label="Block Name" value={room.block} onChange={(v) => {
                                const newRooms = [...rooms]; newRooms[i].block = v; setRooms(newRooms);
                            }} />
                        </div>
                        <div className="flex-1 flex gap-2">
                             <div className="flex-1"><InputField label="Start" type="number" value={String(room.start)} onChange={(v) => {
                                 const newRooms = [...rooms]; newRooms[i].start = Number(v); setRooms(newRooms);
                             }} /></div>
                             <div className="flex-1"><InputField label="End" type="number" value={String(room.end)} onChange={(v) => {
                                 const newRooms = [...rooms]; newRooms[i].end = Number(v); setRooms(newRooms);
                             }} /></div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
        <div className="rounded-xl border border-border bg-card p-6 shadow-sm">
            <h3 className="mb-5 flex items-center gap-3 text-lg font-semibold uppercase tracking-wider text-muted-foreground">
                <Layers size={20} /> Sections
            </h3>
            
            <div className="mb-6 p-5 bg-secondary/10 rounded-lg border border-border">
                <div className="flex items-end gap-6">
                    <div className="w-40">
                        <InputField label="Series Prefix" value={sectionPrefix} onChange={setSectionPrefix} placeholder="e.g. CS-3" />
                    </div>
                    <div className="flex-1">
                        <label className="text-sm font-medium text-muted-foreground mb-3 block">Auto-Generate Series</label>
                        <div className="flex items-center gap-4 bg-background p-3 rounded-md border border-border">
                            <input type="range" min="65" max="90" value={sectionStart.charCodeAt(0)} onChange={(e) => setSectionStart(String.fromCharCode(Number(e.target.value)))} className="flex-1 accent-primary h-2 bg-secondary rounded-lg appearance-none cursor-pointer" />
                            <span className="font-mono font-bold text-xl text-primary">{sectionStart}</span>
                            <span>to</span>
                            <span className="font-mono font-bold text-xl text-primary">{sectionEnd}</span>
                            <input type="range" min="65" max="90" value={sectionEnd.charCodeAt(0)} onChange={(e) => setSectionEnd(String.fromCharCode(Number(e.target.value)))} className="flex-1 accent-primary h-2 bg-secondary rounded-lg appearance-none cursor-pointer" />
                        </div>
                    </div>
                </div>
            </div>

            <div className="p-5 bg-secondary/10 rounded-lg border border-border">
                <div className="flex gap-3 mb-4">
                    <InputField label="Add Custom Section" placeholder="Custom Section (e.g. 3AA)" value={newCustomSection} onChange={setNewCustomSection} />
                    <AppButton onClick={addCustomSection} className="h-10 mt-6" disabled={!newCustomSection}>Add Section</AppButton>
                </div>
                <div className="flex flex-wrap gap-2">
                    {generatedSectionList.map(sec => (
                        <div key={sec} className="px-3 py-1.5 bg-secondary text-sm font-medium rounded-md border border-border flex items-center gap-2">
                            {sec}
                            {customSections.includes(sec) && <button onClick={() => removeCustomSection(sec)}><X size={12}/></button>}
                        </div>
                    ))}
                </div>
            </div>
        </div>
        <div className="fixed bottom-6 left-0 right-0 flex justify-center z-50">
            <AppButton 
                className="w-full max-w-xl h-16 text-xl font-bold shadow-2xl shadow-primary/30 hover:scale-[1.01] transition-transform flex items-center justify-center" 
                variant="primary" 
                onClick={handleGenerate}
                disabled={loading}
            >
                {loading ? "Processing..." : (
                    <span className="flex items-center gap-2">
                        <Zap size={24} fill="currentColor" /> Generate from Excel
                    </span>
                )}
            </AppButton>
        </div>

      </div>
    </DashboardLayout>
  );
};

export default GenerateTimetableUsingExcel;