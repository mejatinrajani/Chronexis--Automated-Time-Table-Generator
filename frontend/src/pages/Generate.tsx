import { useState } from "react";
import { useNavigate } from "react-router-dom";
import DashboardLayout from "@/components/DashboardLayout";
import InputField from "@/components/InputField";
import AppButton from "@/components/AppButton";
import { Plus, Trash2, Zap } from "lucide-react";
import { toast } from "sonner";

interface Subject {
  name: string;
  credits: string;
  room: string;
}

interface Teacher {
  name: string;
  subjects: string[];
}

const DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"];

const Generate = () => {
  const navigate = useNavigate();
  const [startTime, setStartTime] = useState("08:00");
  const [endTime, setEndTime] = useState("17:00");
  const [duration, setDuration] = useState("60");
  const [subjects, setSubjects] = useState<Subject[]>([
    { name: "", credits: "", room: "" },
  ]);
  const [teachers, setTeachers] = useState<Teacher[]>([
    { name: "", subjects: [] },
  ]);
  const [selectedSections, setSelectedSections] = useState<string[]>(["A"]);

  const addSubject = () => setSubjects([...subjects, { name: "", credits: "", room: "" }]);
  const removeSubject = (i: number) => setSubjects(subjects.filter((_, idx) => idx !== i));

  const addTeacher = () => setTeachers([...teachers, { name: "", subjects: [] }]);
  const removeTeacher = (i: number) => setTeachers(teachers.filter((_, idx) => idx !== i));

  const updateSubject = (i: number, field: keyof Subject, value: string) => {
    const updated = [...subjects];
    updated[i] = { ...updated[i], [field]: value };
    setSubjects(updated);
  };

  const updateTeacher = (i: number, value: string) => {
    const updated = [...teachers];
    updated[i] = { ...updated[i], name: value };
    setTeachers(updated);
  };

  const toggleTeacherSubject = (teacherIdx: number, subjectName: string) => {
    const updated = [...teachers];
    const subs = updated[teacherIdx].subjects.includes(subjectName)
      ? updated[teacherIdx].subjects.filter((x) => x !== subjectName)
      : [...updated[teacherIdx].subjects, subjectName];
    updated[teacherIdx] = { ...updated[teacherIdx], subjects: subs };
    setTeachers(updated);
  };

  const toggleSection = (s: string) => {
    setSelectedSections((prev) =>
      prev.includes(s) ? prev.filter((x) => x !== s) : [...prev, s]
    );
  };

  const generateTimeSlots = (): string[] => {
    const slots: string[] = [];
    const [startH, startM] = startTime.split(":").map(Number);
    const [endH, endM] = endTime.split(":").map(Number);
    const dur = parseInt(duration) || 60;
    let current = startH * 60 + startM;
    const end = endH * 60 + endM;

    while (current + dur <= end) {
      const h = Math.floor(current / 60);
      const displayH = h > 12 ? h - 12 : h === 0 ? 12 : h;
      const m = current % 60;
      slots.push(`${displayH}:${m.toString().padStart(2, "0")}`);
      current += dur;
    }
    return slots;
  };

  const handleGenerate = () => {
    const validSubjects = subjects.filter(s => s.name.trim());
    const validTeachers = teachers.filter(t => t.name.trim() && t.subjects.length > 0);

    if (validSubjects.length === 0) {
      toast.error("Please add at least one subject with a name.");
      return;
    }
    if (validTeachers.length === 0) {
      toast.error("Please add at least one teacher with assigned subjects.");
      return;
    }
    if (selectedSections.length === 0) {
      toast.error("Please select at least one section.");
      return;
    }

    const timeSlots = generateTimeSlots();
    if (timeSlots.length === 0) {
      toast.error("Invalid time configuration. Check start/end times and duration.");
      return;
    }

    // Build subject-teacher mapping
    const subjectTeacherMap: Record<string, string[]> = {};
    validSubjects.forEach(s => { subjectTeacherMap[s.name] = []; });
    validTeachers.forEach(t => {
      t.subjects.forEach(sName => {
        if (subjectTeacherMap[sName]) {
          subjectTeacherMap[sName].push(t.name);
        }
      });
    });

    // Generate timetable for each section
    let idCounter = 1000;
    const allGrids: Record<string, Record<string, Record<string, any>>> = {};

    selectedSections.forEach(sec => {
      const grid: Record<string, Record<string, any>> = {};
      DAYS.forEach(day => { grid[day] = {}; });

      // Distribute subjects across the week
      const subjectQueue = [...validSubjects];
      let subIdx = 0;

      for (const day of DAYS) {
        for (const time of timeSlots) {
          if (subIdx >= subjectQueue.length * 2) break; // ~2 classes per subject per week
          const sub = subjectQueue[subIdx % subjectQueue.length];
          const teachersForSub = subjectTeacherMap[sub.name] || [];
          const teacher = teachersForSub.length > 0
            ? teachersForSub[subIdx % teachersForSub.length]
            : "TBA";

          grid[day][time] = {
            id: String(idCounter++),
            subject: sub.name,
            teacher,
            room: sub.room || undefined,
            credits: sub.credits ? Number(sub.credits) : undefined,
          };
          subIdx++;
        }
      }

      allGrids[`Section ${sec}`] = grid;
    });

    // Store generated data and navigate
    localStorage.setItem("generatedTimetable", JSON.stringify(allGrids));
    toast.success("Timetable generated successfully!");
    navigate("/timetable");
  };

  return (
    <DashboardLayout title="Generate Timetable">
      <div className="animate-fade-in mx-auto max-w-3xl space-y-8">
        {/* Time Range */}
        <div className="border border-border bg-card p-6">
          <h3 className="mb-4 text-xs font-medium uppercase tracking-widest text-muted-foreground">Time Configuration</h3>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <div>
              <label className="mb-1.5 block text-xs font-medium uppercase tracking-widest text-muted-foreground">Start Time</label>
              <input
                type="time"
                value={startTime}
                onChange={(e) => setStartTime(e.target.value)}
                className="focus-glow w-full border border-border bg-secondary px-4 py-3 text-sm text-foreground outline-none transition-colors duration-200 focus:border-foreground/30"
              />
            </div>
            <div>
              <label className="mb-1.5 block text-xs font-medium uppercase tracking-widest text-muted-foreground">End Time</label>
              <input
                type="time"
                value={endTime}
                onChange={(e) => setEndTime(e.target.value)}
                className="focus-glow w-full border border-border bg-secondary px-4 py-3 text-sm text-foreground outline-none transition-colors duration-200 focus:border-foreground/30"
              />
            </div>
            <InputField label="Duration (min)" type="number" placeholder="60" value={duration} onChange={setDuration} />
          </div>
        </div>

        {/* Subjects */}
        <div className="border border-border bg-card p-6">
          <div className="mb-4 flex items-center justify-between">
            <h3 className="text-xs font-medium uppercase tracking-widest text-muted-foreground">Subjects</h3>
            <AppButton variant="ghost" size="sm" onClick={addSubject}>
              <Plus size={14} className="mr-1" /> Add
            </AppButton>
          </div>
          <div className="space-y-3">
            {subjects.map((sub, i) => (
              <div key={i} className="flex items-end gap-3 animate-fade-in">
                <div className="flex-1">
                  <InputField label="Subject Name" placeholder="e.g. Data Structures" value={sub.name} onChange={(v) => updateSubject(i, "name", v)} />
                </div>
                <div className="w-20">
                  <InputField label="Credits" type="number" placeholder="3" value={sub.credits} onChange={(v) => updateSubject(i, "credits", v)} />
                </div>
                <div className="w-28">
                  <InputField label="Room" placeholder="R-201" value={sub.room} onChange={(v) => updateSubject(i, "room", v)} />
                </div>
                {subjects.length > 1 && (
                  <button onClick={() => removeSubject(i)} className="mb-5 text-muted-foreground transition-colors hover:text-foreground">
                    <Trash2 size={14} />
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Teachers */}
        <div className="border border-border bg-card p-6">
          <div className="mb-4 flex items-center justify-between">
            <h3 className="text-xs font-medium uppercase tracking-widest text-muted-foreground">Teachers</h3>
            <AppButton variant="ghost" size="sm" onClick={addTeacher}>
              <Plus size={14} className="mr-1" /> Add
            </AppButton>
          </div>
          <div className="space-y-3">
            {teachers.map((t, i) => (
              <div key={i} className="flex items-end gap-3 animate-fade-in">
                <div className="flex-1">
                  <InputField label="Teacher Name" placeholder="e.g. Dr. Smith" value={t.name} onChange={(v) => updateTeacher(i, v)} />
                </div>
                <div className="flex-1">
                  <label className="mb-1.5 block text-xs font-medium uppercase tracking-widest text-muted-foreground">Subjects</label>
                  <div className="flex flex-wrap gap-1.5">
                    {subjects.filter((s) => s.name).map((s) => (
                      <button
                        key={s.name}
                        onClick={() => toggleTeacherSubject(i, s.name)}
                        className={`px-2.5 py-1 text-[10px] uppercase tracking-wider border transition-all duration-200 hover-sharp-to-round ${
                          t.subjects.includes(s.name)
                            ? "border-foreground bg-foreground text-background"
                            : "border-border text-muted-foreground hover:text-foreground"
                        }`}
                      >
                        {s.name}
                      </button>
                    ))}
                    {subjects.filter((s) => s.name).length === 0 && (
                      <span className="text-[10px] text-muted-foreground/50">Add subjects first</span>
                    )}
                  </div>
                </div>
                {teachers.length > 1 && (
                  <button onClick={() => removeTeacher(i)} className="mb-5 text-muted-foreground transition-colors hover:text-foreground">
                    <Trash2 size={14} />
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Sections */}
        <div className="border border-border bg-card p-6">
          <h3 className="mb-4 text-xs font-medium uppercase tracking-widest text-muted-foreground">Sections</h3>
          <div className="flex flex-wrap gap-2">
            {["A", "B", "C", "D", "E"].map((s) => (
              <button
                key={s}
                onClick={() => toggleSection(s)}
                className={`px-5 py-2.5 text-xs font-medium uppercase tracking-widest border transition-all duration-200 hover-sharp-to-round ${
                  selectedSections.includes(s)
                    ? "border-foreground bg-foreground text-background"
                    : "border-border text-muted-foreground hover:text-foreground"
                }`}
              >
                Section {s}
              </button>
            ))}
          </div>
        </div>

        {/* Generate */}
        <AppButton className="w-full" size="lg" onClick={handleGenerate}>
          <Zap size={16} className="mr-2" /> Generate Timetable
        </AppButton>
      </div>
    </DashboardLayout>
  );
};

export default Generate;
