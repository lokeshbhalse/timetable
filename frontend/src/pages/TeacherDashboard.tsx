// frontend/src/pages/TeacherDashboard.tsx
import { useState } from "react";
import { Menu } from "lucide-react";
import StarBackground from "../components/StarBackground";
import ViewTimetable from "./ViewTimetable";
import authService from "../services/auth.service";

const TeacherDashboard = () => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const user = authService.getCurrentUser();

  return (
    <div className="min-h-screen relative">
      <StarBackground />
      
      <div className="relative z-10">
        <header className="sticky top-0 z-30 border-b border-border bg-background/40 backdrop-blur-xl px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold flex items-center gap-2">
                🏫 <span>Teacher Dashboard</span>
              </h1>
              <p className="text-sm text-muted-foreground">Welcome, {user?.full_name || user?.username}!</p>
            </div>
          </div>
        </header>
        
        <main className="p-6">
          <ViewTimetable />
        </main>
      </div>
    </div>
  );
};

export default TeacherDashboard;