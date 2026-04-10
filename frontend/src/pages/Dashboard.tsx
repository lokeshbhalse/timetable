import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { LogOut, Calendar, BookOpen, Clock, User } from "lucide-react";

const Dashboard = () => {
  const navigate = useNavigate();
  const [user, setUser] = useState<any>(null);

  useEffect(() => {
    const userStr = localStorage.getItem("timetable_user");
    if (userStr) {
      setUser(JSON.parse(userStr));
    } else {
      navigate("/login/student");
    }
  }, [navigate]);

  const handleLogout = () => {
    localStorage.removeItem("timetable_auth_token");
    localStorage.removeItem("timetable_user");
    navigate("/login/student");
  };

  if (!user) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      {/* Header */}
      <header className="bg-white/10 backdrop-blur-lg border-b border-white/20">
        <div className="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-gradient-to-r from-orange-500 to-red-500 flex items-center justify-center">
              <Calendar className="w-5 h-5 text-white" />
            </div>
            <h1 className="text-xl font-bold text-white">TimeTableX Dashboard</h1>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-full bg-white/20 flex items-center justify-center">
                <User className="w-4 h-4 text-white" />
              </div>
              <span className="text-white text-sm">{user.name || user.email}</span>
            </div>
            <button
              onClick={handleLogout}
              className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-red-500/20 text-red-300 hover:bg-red-500/30 transition"
            >
              <LogOut className="w-4 h-4" />
              Logout
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/20">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-white font-semibold">Welcome, {user.name?.split(' ')[0] || 'User'}!</h3>
              <BookOpen className="w-5 h-5 text-orange-400" />
            </div>
            <p className="text-white/70 text-sm">Role: {user.role}</p>
            <p className="text-white/70 text-sm">Email: {user.email}</p>
          </div>
          
          <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/20">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-white font-semibold">Quick Actions</h3>
              <Clock className="w-5 h-5 text-green-400" />
            </div>
            <button className="w-full bg-gradient-to-r from-orange-500 to-red-500 text-white py-2 rounded-lg mb-2 hover:opacity-90 transition">
              View Timetable
            </button>
            <button className="w-full bg-white/20 text-white py-2 rounded-lg hover:bg-white/30 transition">
              Generate New Timetable
            </button>
          </div>
          
          <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/20">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-white font-semibold">System Status</h3>
              <div className="w-2 h-2 rounded-full bg-green-400 animate-pulse"></div>
            </div>
            <p className="text-white/70 text-sm">Backend: Connected</p>
            <p className="text-white/70 text-sm">Database: Active</p>
            <p className="text-white/70 text-sm">API: Running on port 8000</p>
          </div>
        </div>

        <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/20">
          <h2 className="text-xl font-bold text-white mb-4">Welcome to TimeTableX</h2>
          <p className="text-white/70">
            Your timetable generation system is ready! Use the navigation to generate timetables, 
            manage courses, and view schedules.
          </p>
        </div>
      </main>
    </div>
  );
};

export default Dashboard;