// frontend/src/components/AppLayout.tsx
import { useState } from "react";
import { Outlet, useNavigate } from "react-router-dom";
import { Menu } from "lucide-react";
import AppSidebar from "./AppSidebar";
import StarBackground from "./StarBackground";

const AppLayout = () => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const navigate = useNavigate();

  return (
    <div className="min-h-screen relative">
      <StarBackground />
      <AppSidebar
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        onNavigate={(page) => navigate(`/admin/${page}`)}
      />
      
      <div className="lg:ml-64 relative z-10">
        <header className="sticky top-0 z-30 border-b border-gray-800 bg-gray-900/40 backdrop-blur-xl px-6 py-4">
          <div className="flex items-center gap-4">
            <button onClick={() => setSidebarOpen(true)} className="lg:hidden text-white">
              <Menu size={24} />
            </button>
            <div>
              <h1 className="text-2xl font-bold flex items-center gap-2 text-white">
                🏫 <span>SGSITS Timetable Generator</span>
              </h1>
              <p className="text-sm text-gray-400">Shri Govindram Seksaria Institute of Technology and Science</p>
            </div>
          </div>
        </header>
        
        <main className="p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default AppLayout;