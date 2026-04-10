import React, { useState } from "react";
import { Plus, Trash2, Clock, BookOpen } from "lucide-react";

interface TimetableEntry {
  id: string;
  day: string;
  time: string;
  subject: string;
  room?: string;
}

const DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"];
const TIME_SLOTS = [
  "08:00 - 09:00",
  "09:00 - 10:00",
  "10:00 - 11:00",
  "11:00 - 12:00",
  "12:00 - 13:00",
  "13:00 - 14:00",
  "14:00 - 15:00",
  "15:00 - 16:00",
];

const COLORS = [
  "from-primary/30 to-primary/10 border-primary/30",
  "from-sun-corona/30 to-sun-corona/10 border-sun-corona/30",
  "from-space-nebula/50 to-space-nebula/20 border-space-nebula/50",
  "from-emerald-500/30 to-emerald-500/10 border-emerald-500/30",
  "from-rose-500/30 to-rose-500/10 border-rose-500/30",
  "from-sky-500/30 to-sky-500/10 border-sky-500/30",
];

function getColorForSubject(subject: string): string {
  let hash = 0;
  for (let i = 0; i < subject.length; i++) hash = subject.charCodeAt(i) + ((hash << 5) - hash);
  return COLORS[Math.abs(hash) % COLORS.length];
}

const Timetable: React.FC = () => {
  const [entries, setEntries] = useState<TimetableEntry[]>([
    { id: "1", day: "Monday", time: "09:00 - 10:00", subject: "Mathematics", room: "A101" },
    { id: "2", day: "Monday", time: "10:00 - 11:00", subject: "Physics", room: "B203" },
    { id: "3", day: "Tuesday", time: "08:00 - 09:00", subject: "Chemistry", room: "C102" },
    { id: "4", day: "Wednesday", time: "11:00 - 12:00", subject: "English", room: "A205" },
    { id: "5", day: "Thursday", time: "14:00 - 15:00", subject: "Computer Science", room: "D301" },
    { id: "6", day: "Friday", time: "09:00 - 10:00", subject: "Mathematics", room: "A101" },
  ]);

  const [showForm, setShowForm] = useState(false);
  const [newEntry, setNewEntry] = useState({ day: "Monday", time: TIME_SLOTS[0], subject: "", room: "" });

  const addEntry = () => {
    if (!newEntry.subject.trim()) return;
    setEntries([...entries, { ...newEntry, id: Date.now().toString() }]);
    setNewEntry({ day: "Monday", time: TIME_SLOTS[0], subject: "", room: "" });
    setShowForm(false);
  };

  const removeEntry = (id: string) => setEntries(entries.filter((e) => e.id !== id));

  const getEntry = (day: string, time: string) => entries.find((e) => e.day === day && e.time === time);

  return (
    <div className="relative z-10 w-full max-w-7xl mx-auto px-4 sm:px-6 py-8">
      {/* Header */}
      <div className="text-center mb-10 float-animation">
        <div className="flex items-center justify-center gap-3 mb-3">
          <Clock className="w-8 h-8 text-primary" />
          <h1 className="text-4xl sm:text-5xl font-display font-bold text-foreground tracking-tight">
            Timetable
          </h1>
        </div>
        <p className="text-muted-foreground text-lg">Organize your schedule across the stars</p>
      </div>

      {/* Add button */}
      <div className="flex justify-end mb-6">
        <button
          onClick={() => setShowForm(!showForm)}
          className="flex items-center gap-2 px-5 py-2.5 rounded-lg bg-primary text-primary-foreground font-medium text-sm hover:brightness-110 transition-all"
        >
          <Plus className="w-4 h-4" />
          Add Class
        </button>
      </div>

      {/* Add form */}
      {showForm && (
        <div className="mb-6 p-5 rounded-xl bg-card/80 backdrop-blur-xl border border-border">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div>
              <label className="block text-sm text-muted-foreground mb-1.5">Day</label>
              <select
                value={newEntry.day}
                onChange={(e) => setNewEntry({ ...newEntry, day: e.target.value })}
                className="w-full rounded-lg bg-secondary text-secondary-foreground border border-border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
              >
                {DAYS.map((d) => <option key={d} value={d}>{d}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-sm text-muted-foreground mb-1.5">Time</label>
              <select
                value={newEntry.time}
                onChange={(e) => setNewEntry({ ...newEntry, time: e.target.value })}
                className="w-full rounded-lg bg-secondary text-secondary-foreground border border-border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
              >
                {TIME_SLOTS.map((t) => <option key={t} value={t}>{t}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-sm text-muted-foreground mb-1.5">Subject</label>
              <input
                type="text"
                value={newEntry.subject}
                onChange={(e) => setNewEntry({ ...newEntry, subject: e.target.value })}
                placeholder="e.g. Mathematics"
                className="w-full rounded-lg bg-secondary text-secondary-foreground border border-border px-3 py-2 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
              />
            </div>
            <div>
              <label className="block text-sm text-muted-foreground mb-1.5">Room</label>
              <input
                type="text"
                value={newEntry.room}
                onChange={(e) => setNewEntry({ ...newEntry, room: e.target.value })}
                placeholder="e.g. A101"
                className="w-full rounded-lg bg-secondary text-secondary-foreground border border-border px-3 py-2 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
              />
            </div>
          </div>
          <div className="flex gap-3 mt-4">
            <button
              onClick={addEntry}
              className="px-5 py-2 rounded-lg bg-primary text-primary-foreground font-medium text-sm hover:brightness-110 transition"
            >
              Save
            </button>
            <button
              onClick={() => setShowForm(false)}
              className="px-5 py-2 rounded-lg bg-secondary text-secondary-foreground font-medium text-sm hover:bg-muted transition"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Timetable grid */}
      <div className="rounded-xl overflow-hidden border border-border bg-card/60 backdrop-blur-xl">
        <div className="overflow-x-auto">
          <table className="w-full min-w-[700px]">
            <thead>
              <tr>
                <th className="p-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wider border-b border-border bg-secondary/50 w-32">
                  <Clock className="w-3.5 h-3.5 inline mr-1.5 -mt-0.5" />
                  Time
                </th>
                {DAYS.map((day) => (
                  <th
                    key={day}
                    className="p-3 text-center text-xs font-semibold text-muted-foreground uppercase tracking-wider border-b border-border bg-secondary/50"
                  >
                    {day}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {TIME_SLOTS.map((time, i) => (
                <tr key={time} className={i % 2 === 0 ? "" : "bg-secondary/20"}>
                  <td className="p-3 text-xs font-mono text-muted-foreground border-r border-border whitespace-nowrap">
                    {time}
                  </td>
                  {DAYS.map((day) => {
                    const entry = getEntry(day, time);
                    return (
                      <td key={day} className="p-1.5 border-r border-border last:border-r-0">
                        {entry ? (
                          <div
                            className={`group relative rounded-lg p-2.5 bg-gradient-to-br border ${getColorForSubject(entry.subject)} transition-all hover:scale-[1.02]`}
                          >
                            <div className="flex items-start justify-between">
                              <div>
                                <div className="flex items-center gap-1.5">
                                  <BookOpen className="w-3 h-3 text-foreground/70" />
                                  <span className="text-sm font-medium text-foreground">{entry.subject}</span>
                                </div>
                                {entry.room && (
                                  <span className="text-xs text-muted-foreground mt-1 block">{entry.room}</span>
                                )}
                              </div>
                              <button
                                onClick={() => removeEntry(entry.id)}
                                className="opacity-0 group-hover:opacity-100 transition-opacity text-destructive hover:text-destructive/80"
                              >
                                <Trash2 className="w-3.5 h-3.5" />
                              </button>
                            </div>
                          </div>
                        ) : (
                          <div className="h-12 rounded-lg" />
                        )}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default Timetable;
