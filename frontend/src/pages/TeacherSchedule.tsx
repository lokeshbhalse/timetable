// frontend/src/pages/TeacherSchedule.tsx
import { useState, useEffect } from "react";
import { Calendar, Clock, BookOpen, Users, MapPin, Loader2 } from "lucide-react";
import { toast } from "sonner";
import api from "../services/api";

interface ScheduleEntry {
  id: number;
  day_name: string;
  start_time: string;
  end_time: string;
  course_code: string;
  course_name: string;
  group_name: string;
  group_code: string;
  room_code: string;
}

const DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'];

const TeacherSchedule = () => {
  const [schedule,    setSchedule]    = useState<ScheduleEntry[]>([]);
  const [loading,     setLoading]     = useState(true);
  const [teacherName, setTeacherName] = useState("");
  const [error,       setError]       = useState("");

  const loadSchedule = async () => {
    setLoading(true);
    setError("");
    try {
      const user = JSON.parse(localStorage.getItem('user') || '{}');

      // ── Strategy 1: use /api/teacher/schedule (matches by username/email server-side)
      try {
        const res = await api.get('/teacher/schedule');
        if (res.data.schedule && res.data.schedule.length > 0) {
          setSchedule(res.data.schedule);
          setTeacherName(res.data.teacher_name || user?.full_name || "Teacher");
          return;
        }
      } catch (_) { /* fall through to strategy 2 */ }

      // ── Strategy 2: find teacher record by matching email, then fetch by teacher id
      const teachersRes = await api.get('/teachers');
      const teachers: any[] = teachersRes.data.teachers || [];

      const userEmail    = user?.email    || '';
      const userFullName = user?.full_name || user?.username || '';

      // match by email first, then by name
      let matched = teachers.find(t =>
        t.email && userEmail && t.email.toLowerCase() === userEmail.toLowerCase()
      );
      if (!matched) {
        matched = teachers.find(t =>
          t.name && userFullName &&
          t.name.toLowerCase().includes(userFullName.toLowerCase())
        );
      }

      if (!matched) {
        setError("Your teacher profile was not found. Ask the admin to add you as a teacher.");
        setSchedule([]);
        return;
      }

      const schedRes = await api.get(`/teachers/${matched.id}/schedule`);
      setSchedule(schedRes.data.schedule || []);
      setTeacherName(matched.name || userFullName);

    } catch (err: any) {
      console.error("Error loading schedule:", err);
      const msg = err?.response?.data?.detail ?? "Failed to load schedule";
      setError(msg);
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadSchedule(); }, []);

  // Group entries by day
  const byDay: Record<string, ScheduleEntry[]> = {};
  schedule.forEach(e => {
    if (!byDay[e.day_name]) byDay[e.day_name] = [];
    byDay[e.day_name].push(e);
  });

  // ── Loading ──────────────────────────────────────────────────────────────
  if (loading) {
    return (
      <div className="bg-card/60 backdrop-blur-md rounded-xl p-8 border border-border text-center">
        <Loader2 className="w-12 h-12 animate-spin mx-auto mb-4 text-primary" />
        <p className="text-muted-foreground">Loading your schedule…</p>
      </div>
    );
  }

  // ── Error ────────────────────────────────────────────────────────────────
  if (error) {
    return (
      <div className="bg-card/60 backdrop-blur-md rounded-xl p-8 border border-border text-center space-y-3">
        <p className="text-4xl">⚠️</p>
        <p className="font-semibold text-lg">{error}</p>
        <button
          onClick={loadSchedule}
          className="px-5 py-2 rounded-lg border border-border hover:bg-muted/30 transition text-sm"
        >
          Retry
        </button>
      </div>
    );
  }

  // ── Render ───────────────────────────────────────────────────────────────
  return (
    <div className="space-y-6">

      {/* Header card */}
      <div className="bg-card/60 backdrop-blur-md rounded-xl p-8 border border-border">
        <div className="flex items-center gap-3 mb-2">
          <Calendar className="w-8 h-8 text-primary" />
          <h2 className="text-2xl font-bold">My Teaching Schedule</h2>
        </div>
        <p className="text-muted-foreground">
          Welcome, {teacherName || "Teacher"}! Here is your weekly class schedule.
        </p>
        <p className="text-sm text-muted-foreground mt-2">
          📊 Total Classes This Week: {schedule.length}
        </p>
      </div>

      {/* Empty state */}
      {schedule.length === 0 && (
        <div className="bg-card/60 backdrop-blur-md rounded-xl p-8 border border-border text-center">
          <p className="text-4xl mb-3">📭</p>
          <p className="font-semibold">No classes assigned yet</p>
          <p className="text-sm text-muted-foreground mt-2">
            The admin will assign your classes when generating the timetable.
          </p>
        </div>
      )}

      {/* Schedule by day */}
      {schedule.length > 0 && (
        <div className="space-y-4">
          {DAYS.map(day => {
            const entries = byDay[day];
            if (!entries?.length) return null;
            return (
              <div key={day} className="bg-card/60 backdrop-blur-md rounded-xl border border-border overflow-hidden">
                <div className="bg-gradient-to-r from-primary to-accent p-3">
                  <h3 className="text-white font-bold text-lg">{day}</h3>
                </div>
                <div className="divide-y divide-border">
                  {entries
                    .sort((a, b) => a.start_time.localeCompare(b.start_time))
                    .map((entry, idx) => (
                      <div key={idx} className="p-4 hover:bg-muted/20 transition-colors">
                        <div className="flex flex-wrap items-center justify-between gap-4">

                          {/* Time */}
                          <div className="flex items-center gap-3">
                            <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center">
                              <Clock className="w-6 h-6 text-primary" />
                            </div>
                            <div>
                              <p className="font-semibold text-lg">
                                {entry.start_time} – {entry.end_time}
                              </p>
                              <p className="text-xs text-muted-foreground">Time Slot</p>
                            </div>
                          </div>

                          {/* Course */}
                          <div className="flex items-center gap-3">
                            <div className="w-12 h-12 rounded-full bg-blue-500/10 flex items-center justify-center">
                              <BookOpen className="w-6 h-6 text-blue-500" />
                            </div>
                            <div>
                              <p className="font-semibold">{entry.course_name}</p>
                              <p className="text-xs text-muted-foreground">{entry.course_code}</p>
                            </div>
                          </div>

                          {/* Group */}
                          <div className="flex items-center gap-3">
                            <div className="w-12 h-12 rounded-full bg-green-500/10 flex items-center justify-center">
                              <Users className="w-6 h-6 text-green-500" />
                            </div>
                            <div>
                              <p className="font-semibold">{entry.group_name}</p>
                              <p className="text-xs text-muted-foreground">
                                {entry.group_code || "Section"}
                              </p>
                            </div>
                          </div>

                          {/* Room */}
                          <div className="flex items-center gap-3">
                            <div className="w-12 h-12 rounded-full bg-orange-500/10 flex items-center justify-center">
                              <MapPin className="w-6 h-6 text-orange-500" />
                            </div>
                            <div>
                              <p className="font-semibold">{entry.room_code}</p>
                              <p className="text-xs text-muted-foreground">Room</p>
                            </div>
                          </div>

                        </div>
                      </div>
                    ))}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Weekly summary */}
      {schedule.length > 0 && (
        <div className="bg-card/60 backdrop-blur-md rounded-xl p-6 border border-border">
          <h3 className="text-lg font-bold mb-3">📊 Weekly Summary</h3>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
            {DAYS.map(day => (
              <div key={day} className="text-center p-3 rounded-lg bg-background/50">
                <p className="font-semibold text-sm">{day}</p>
                <p className="text-2xl font-bold text-primary">{byDay[day]?.length || 0}</p>
                <p className="text-xs text-muted-foreground">classes</p>
              </div>
            ))}
          </div>
          <div className="mt-4 pt-3 border-t border-border text-center">
            <p className="text-sm text-muted-foreground">
              Total Teaching Periods This Week: <strong>{schedule.length}</strong>
            </p>
          </div>
        </div>
      )}

    </div>
  );
};

export default TeacherSchedule;
