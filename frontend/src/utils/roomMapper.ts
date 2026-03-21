import { SlotData } from "@/components/DraggableSlot";
import { APISlot } from "@/utils/dataMapper";

const DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"];
const SLOT_DURATION = 50;

type GridData = Record<string, Record<string, SlotData | null>>;

const parseTime = (t: string) => {
  if (!t) return 0;
  const [h, m] = t.split(":").map(Number);
  return h * 60 + m;
};

export const mapApiToRoomGrid = (apiData: APISlot[]) => {
  const grids: Record<string, GridData> = {};
  const timeSet = new Set<string>();
  const roomSet = new Set<string>();


  apiData.forEach((item) => {
    if (item.room) {
      roomSet.add(item.room);
    }
    timeSet.add(item.start_time);
  });

  const uniqueRooms = Array.from(roomSet).sort();


  const sortedTimes = Array.from(timeSet).sort(
    (a, b) => parseTime(a) - parseTime(b)
  );


  uniqueRooms.forEach((room) => {
    grids[room] = {};
    DAYS.forEach((day) => {
      grids[room][day] = {};
    });
  });

  apiData.forEach((item) => {
    if (!item.room || !grids[item.room]) return;

    const duration = item.duration || 1;
    const startIndex = sortedTimes.indexOf(item.start_time);

    for (let i = 0; i < duration; i++) {
      const timeKey = sortedTimes[startIndex + i];
      if (!timeKey) continue;

      const slot: SlotData = {
        id: String(item.id),
        subject: item.subject,
        teacher: `${item.teacher} (${item.section})`, 
        room: item.room,
        credits: item.total_credits ?? item.credits,
        duration: duration,
      };

      if (!grids[item.room][item.day]) {
        grids[item.room][item.day] = {};
      }

      grids[item.room][item.day][timeKey] = slot;
    }
  });

  const finalTimes: string[] = [];

  for (let i = 0; i < sortedTimes.length; i++) {
    finalTimes.push(sortedTimes[i]);

    if (i < sortedTimes.length - 1) {
      const current = parseTime(sortedTimes[i]);
      const next = parseTime(sortedTimes[i + 1]);

      if (next - current > 60) {
        const breakStart = current + SLOT_DURATION;
        const breakStr = `${Math.floor(breakStart / 60)}:${(breakStart % 60)
          .toString()
          .padStart(2, "0")}`;

        if (!timeSet.has(breakStr)) {
          finalTimes.push(breakStr);
        }
      }
    }
  }

  const breakTimes = finalTimes.filter((t) => !timeSet.has(t));

  return {
    grids,
    uniqueRooms,
    uniqueTimes: finalTimes,
    breakTimes,
  };
};