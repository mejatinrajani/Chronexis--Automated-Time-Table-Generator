import { useEffect, useState } from "react";
import Modal from "@/components/Modal";
import AppButton from "@/components/AppButton";
import { Clock, Calendar, CheckCircle2, Loader2 } from "lucide-react";
import { APISlot } from "@/utils/dataMapper";

// Matches your Supabase "timetable_runs" table
interface HistoryRun {
  id: number;
  created_at: string;
  total_classes: number;
}

interface HistoryModalProps {
  open: boolean;
  onClose: () => void;
  onLoadRun: (data: APISlot[], forcedSlots?: string[]) => void;
}

const HistoryModal = ({ open, onClose, onLoadRun }: HistoryModalProps) => {
  const [history, setHistory] = useState<HistoryRun[]>([]);
  const [loadingList, setLoadingList] = useState(false);
  const [loadingId, setLoadingId] = useState<number | null>(null);

  // 1. Fetch History List on Open
  useEffect(() => {
    if (open) {
      fetchHistory();
    }
  }, [open]);

  const fetchHistory = async () => {
    setLoadingList(true);
    try {
      const res = await fetch("http://localhost:8000/api/history/");
      const data = await res.json();
      setHistory(data);
    } catch (e) {
      console.error("Failed to fetch history", e);
    } finally {
      setLoadingList(false);
    }
  };

  // 2. Load Specific Run
  const handleLoad = async (runId: number) => {
    setLoadingId(runId);
    try {
      const res = await fetch(`http://localhost:8000/api/history/${runId}`);
      const result = await res.json();
      
      // NEW: Handle the object response
      const scheduleData: APISlot[] = Array.isArray(result) ? result : result.schedule;
      const timeSlots: string[] = Array.isArray(result) ? [] : result.time_slots;
      
      // Pass BOTH to the parent
      onLoadRun(scheduleData, timeSlots);
      
      onClose();
    } catch (e) {
      console.error("Failed to load run", e);
    } finally {
      setLoadingId(null);
    }
  };

  return (
    <Modal
      open={open}
      onClose={onClose}
      title="Saved Timetables"
      actions={
        <AppButton variant="ghost" size="sm" onClick={onClose}>
          Close
        </AppButton>
      }
    >
      <div className="min-h-[300px] max-h-[60vh] overflow-y-auto pr-1">
        {loadingList ? (
          <div className="flex h-40 items-center justify-center text-muted-foreground">
            <Loader2 className="animate-spin mr-2" /> Loading history...
          </div>
        ) : history.length === 0 ? (
          <div className="flex h-40 flex-col items-center justify-center text-muted-foreground opacity-50">
            <Clock size={40} strokeWidth={1} className="mb-2" />
            <p className="text-sm">No saved timetables found.</p>
          </div>
        ) : (
          <div className="space-y-2">
            {history.map((run) => (
              <div
                key={run.id}
                className="group flex items-center justify-between rounded-lg border border-border bg-secondary/30 p-3 transition-all hover:bg-secondary hover:border-foreground/20"
              >
                <div className="flex items-start gap-3">
                  <div className="mt-1 flex h-8 w-8 items-center justify-center rounded-full bg-primary/10 text-primary">
                    <Calendar size={14} />
                  </div>
                  <div>
                    <h4 className="text-sm font-medium text-foreground">
                      Timetable #{run.id}
                    </h4>
                    <p className="text-xs text-muted-foreground flex items-center gap-2 mt-0.5">
                      <span>
                        {new Date(run.created_at).toLocaleDateString(undefined, {
                          weekday: 'short', month: 'short', day: 'numeric'
                        })}
                      </span>
                      <span className="w-1 h-1 rounded-full bg-border" />
                      <span>
                        {new Date(run.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </span>
                    </p>
                    <div className="mt-1.5 inline-flex items-center rounded-sm bg-background px-1.5 py-0.5 text-[10px] font-medium text-muted-foreground border border-border">
                      {run.total_classes} Classes Generated
                    </div>
                  </div>
                </div>

                <AppButton
                  size="sm"
                  variant="outline"
                  onClick={() => handleLoad(run.id)}
                  disabled={loadingId !== null}
                  className="opacity-0 group-hover:opacity-100 transition-opacity"
                >
                  {loadingId === run.id ? (
                    <Loader2 size={14} className="animate-spin" />
                  ) : (
                    <>Load <CheckCircle2 size={14} className="ml-1.5" /></>
                  )}
                </AppButton>
              </div>
            ))}
          </div>
        )}
      </div>
    </Modal>
  );
};

export default HistoryModal;