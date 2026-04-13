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
  room_code: string;
}

const TeacherSchedule = () => {
  const [schedule, setSchedule] = useState<ScheduleEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [teacherName, setTeacherName] = useState("");

  const loadSchedule = async () => {
    setLoading(true);
    try {
      const user = JSON.parse(localStorage.getItem('user') || '{}');
      const teacherId = user?.id;
      const teacherNameValue = user?.full_name || user?.name || '';

      if (!teacherId) {
        toast.error('Teacher ID not found. Please login again.');
        setLoading(false);
        return;
      }

      const response = await api.get(`/teachers/${teacherId}/schedule`, {
        params: { week: 1 }
      });
      setSchedule(response.data.schedule || []);
      setTeacherName(teacherNameValue || `Teacher ${teacherId}`);
    } catch (error) {
      console.error("Error loading schedule:", error);
      toast.error("Failed to load schedule");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSchedule();
  }, []);

  const scheduleByDay: Record<string, ScheduleEntry[]> = {};
  schedule.forEach(entry => {
    if (!scheduleByDay[entry.day_name]) {
      scheduleByDay[entry.day_name] = [];
    }
    scheduleByDay[entry.day_name].push(entry);
  });

  const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'];

  if (loading) {
    return (
      <div className="bg-card/60 backdrop-blur-md rounded-xl p-8 border border-border text-center">
        <Loader2 className="w-12 h-12 animate-spin mx-auto mb-4 text-primary" />
        <p className="text-muted-foreground">Loading your schedule...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="bg-card/60 backdrop-blur-md rounded-xl p-8 border border-border">
        <div className="flex items-center gap-3 mb-2">
          <Calendar className="w-8 h-8 text-primary" />
          <h2 className="text-2xl font-bold">My Teaching Schedule</h2>
        </div>
        <p className="text-muted-foreground">Welcome, {teacherName || "Teacher"}! Here is your weekly class schedule.</p>
        <p className="text-sm text-muted-foreground mt-2">📊 Total Classes: {schedule.length}</p>
      </div>

      {schedule.length === 0 ? (
        <div className="bg-card/60 backdrop-blur-md rounded-xl p-8 border border-border text-center">
          <p className="text-muted-foreground">No classes assigned yet.</p>
          <p className="text-sm text-muted-foreground mt-2">Admin will assign your classes when generating timetable.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {days.map(day => (
            scheduleByDay[day] && scheduleByDay[day].length > 0 && (
              <div key={day} className="bg-card/60 backdrop-blur-md rounded-xl border border-border overflow-hidden">
                <div className="bg-gradient-to-r from-primary to-accent p-3">
                  <h3 className="text-white font-bold text-lg">{day}</h3>
                </div>
                <div className="divide-y divide-border">
                  {scheduleByDay[day].map((entry, idx) => (
                    <div key={idx} className="p-4 hover:bg-muted/20 transition-colors">
                      <div className="flex flex-wrap items-center justify-between gap-4">
                        <div className="flex items-center gap-3">
                          <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center">
                            <Clock className="w-6 h-6 text-primary" />
                          </div>
                          <div>
                            <p className="font-semibold text-lg">
                              {entry.start_time} - {entry.end_time}
                            </p>
                            <p className="text-sm text-muted-foreground">Time Slot</p>
                          </div>
                        </div>
                        
                        <div className="flex items-center gap-3">
                          <div className="w-12 h-12 rounded-full bg-blue-500/10 flex items-center justify-center">
                            <BookOpen className="w-6 h-6 text-blue-500" />
                          </div>
                          <div>
                            <p className="font-semibold">{entry.course_name}</p>
                            <p className="text-sm text-muted-foreground">{entry.course_code}</p>
                          </div>
                        </div>
                        
                        <div className="flex items-center gap-3">
                          <div className="w-12 h-12 rounded-full bg-green-500/10 flex items-center justify-center">
                            <Users className="w-6 h-6 text-green-500" />
                          </div>
                          <div>
                            <p className="font-semibold">{entry.group_name}</p>
                            <p className="text-sm text-muted-foreground">Section</p>
                          </div>
                        </div>
                        
                        <div className="flex items-center gap-3">
                          <div className="w-12 h-12 rounded-full bg-orange-500/10 flex items-center justify-center">
                            <MapPin className="w-6 h-6 text-orange-500" />
                          </div>
                          <div>
                            <p className="font-semibold">{entry.room_code}</p>
                            <p className="text-sm text-muted-foreground">Room</p>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )
          ))}
        </div>
      )}

      {schedule.length > 0 && (
        <div className="bg-card/60 backdrop-blur-md rounded-xl p-6 border border-border">
          <h3 className="text-lg font-bold mb-3">📊 Weekly Summary</h3>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
            {days.map(day => (
              <div key={day} className="text-center p-3 rounded-lg bg-background/50">
                <p className="font-semibold">{day}</p>
                <p className="text-2xl font-bold text-primary">
                  {scheduleByDay[day]?.length || 0}
                </p>
                <p className="text-xs text-muted-foreground">classes</p>
              </div>
            ))}
          </div>
          <div className="mt-4 pt-3 border-t border-border text-center">
            <p className="text-sm text-muted-foreground">
              Total Teaching Hours: {schedule.length} periods this week
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

export default TeacherSchedule;