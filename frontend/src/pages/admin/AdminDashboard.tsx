// frontend/src/pages/AdminDashboard.tsx
import { useState } from "react";
import { Outlet } from "react-router-dom";
import { Menu } from "lucide-react";
import AppSidebar from "../../components/AppSidebar";
import StarBackground from "../../components/StarBackground";
import AddTeacher from "../../pages/AddTeacher";
import AddSubject from "../../pages/AddSubject";
import AssignSubject from "../../pages/AssignSubject";
import CreateSection from "../../pages/CreateSection";
import GenerateTimetable from "../../pages/GenerateTimetable";
import ViewTimetable from "../../pages/ViewTimetable"

const AdminDashboard = () => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [activePage, setActivePage] = useState("dashboard");

  const renderPage = () => {
    switch(activePage) {
      case "add-teacher":
        return <AddTeacher />;
      case "add-subject":
        return <AddSubject />;
      case "assign-subject":
        return <AssignSubject />;
      case "create-section":
        return <CreateSection />;
      case "generate-timetable":
        return <GenerateTimetable />;
      case "view-timetable":
        return <ViewTimetable />;
      default:
        return (
          <div className="space-y-6">
            <div className="bg-card/60 backdrop-blur-md rounded-xl p-8 border border-border">
              <h2 className="text-2xl font-bold mb-4">👋 Welcome Admin</h2>
              <p className="text-muted-foreground">Manage teachers, subjects, sections, and generate timetables.</p>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              <div className="bg-card/60 backdrop-blur-md rounded-xl p-6 border border-border cursor-pointer hover:border-primary/50 transition-all" onClick={() => setActivePage("add-teacher")}>
                <div className="text-4xl mb-3">👨‍🏫</div>
                <h3 className="text-lg font-bold">Add Teacher</h3>
                <p className="text-sm text-muted-foreground">Register faculty members</p>
              </div>
              <div className="bg-card/60 backdrop-blur-md rounded-xl p-6 border border-border cursor-pointer hover:border-primary/50 transition-all" onClick={() => setActivePage("add-subject")}>
                <div className="text-4xl mb-3">📚</div>
                <h3 className="text-lg font-bold">Add Subject</h3>
                <p className="text-sm text-muted-foreground">Define courses with credits</p>
              </div>
              <div className="bg-card/60 backdrop-blur-md rounded-xl p-6 border border-border cursor-pointer hover:border-primary/50 transition-all" onClick={() => setActivePage("assign-subject")}>
                <div className="text-4xl mb-3">🔗</div>
                <h3 className="text-lg font-bold">Assign Subject</h3>
                <p className="text-sm text-muted-foreground">Link subjects to teachers</p>
              </div>
              <div className="bg-card/60 backdrop-blur-md rounded-xl p-6 border border-border cursor-pointer hover:border-primary/50 transition-all" onClick={() => setActivePage("create-section")}>
                <div className="text-4xl mb-3">📋</div>
                <h3 className="text-lg font-bold">Create Section</h3>
                <p className="text-sm text-muted-foreground">Organize student groups</p>
              </div>
              <div className="bg-card/60 backdrop-blur-md rounded-xl p-6 border border-border cursor-pointer hover:border-primary/50 transition-all" onClick={() => setActivePage("generate-timetable")}>
                <div className="text-4xl mb-3">⚡</div>
                <h3 className="text-lg font-bold">Generate Timetable</h3>
                <p className="text-sm text-muted-foreground">Auto-create schedules</p>
              </div>
              <div className="bg-card/60 backdrop-blur-md rounded-xl p-6 border border-border cursor-pointer hover:border-primary/50 transition-all" onClick={() => setActivePage("view-timetable")}>
                <div className="text-4xl mb-3">👁️</div>
                <h3 className="text-lg font-bold">View Timetable</h3>
                <p className="text-sm text-muted-foreground">See generated schedules</p>
              </div>
            </div>
          </div>
        );
    }
  };

  return (
    <div className="min-h-screen relative">
      <StarBackground />
      <AppSidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} onNavigate={setActivePage} />
      
      <div className="lg:ml-64 relative z-10">
        <header className="sticky top-0 z-30 border-b border-border bg-background/40 backdrop-blur-xl px-6 py-4">
          <div className="flex items-center gap-4">
            <button onClick={() => setSidebarOpen(true)} className="lg:hidden text-foreground">
              <Menu size={24} />
            </button>
            <div>
              <h1 className="text-2xl font-bold flex items-center gap-2">
                🏫 <span>SGSITS Admin Panel</span>
              </h1>
              <p className="text-sm text-muted-foreground">Complete Timetable Management System</p>
            </div>
          </div>
        </header>
        
        <main className="p-6">
          {renderPage()}
        </main>
      </div>
    </div>
  );
};

export default AdminDashboard;