// frontend/src/pages/StudentDashboard.tsx
import React, { useState, useEffect } from 'react';
import timetableService, { Branch, TimetableData } from '../services/timetable_service';
import authService from '../services/auth.service';

const StudentDashboard: React.FC = () => {
  const [branches, setBranches] = useState<Branch[]>([]);
  const [filters, setFilters] = useState({ branch: 'CSE', year: 1, section: 'A' });
  const [timetable, setTimetable] = useState<TimetableData | null>(null);
  const [loading, setLoading] = useState(false);
  const user = authService.getCurrentUser();

  useEffect(() => {
    loadBranches();
  }, []);

  const loadBranches = async () => {
    try {
      const data = await timetableService.getBranches();
      setBranches(data);
    } catch (error) {
      console.error('Error loading branches:', error);
    }
  };

  const loadTimetable = async () => {
    setLoading(true);
    try {
      const data = await timetableService.viewTimetable(filters.branch, filters.year, filters.section);
      setTimetable(data);
    } catch (error) {
      console.error('Error loading timetable:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100">
      <div className="bg-gradient-to-r from-green-600 to-teal-600 text-white p-6">
        <h1 className="text-3xl font-bold">Student Dashboard</h1>
        <p>Welcome, {user?.full_name || user?.username}!</p>
      </div>

      <div className="container mx-auto p-6">
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="text-xl font-bold mb-4">View Your Timetable</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-4">
            <select 
              className="p-2 border rounded" 
              value={filters.branch} 
              onChange={e => setFilters({...filters, branch: e.target.value})}
            >
              {branches.map((b: Branch) => (
                <option key={b.code} value={b.code}>{b.name}</option>
              ))}
            </select>
            <select 
              className="p-2 border rounded" 
              value={filters.year} 
              onChange={e => setFilters({...filters, year: parseInt(e.target.value)})}
            >
              <option value={1}>1st Year</option>
              <option value={2}>2nd Year</option>
              <option value={3}>3rd Year</option>
              <option value={4}>4th Year</option>
            </select>
            <input 
              type="text" 
              placeholder="Section (A/B/C)" 
              className="p-2 border rounded" 
              value={filters.section} 
              onChange={e => setFilters({...filters, section: e.target.value})} 
            />
          </div>
          <button 
            onClick={loadTimetable} 
            className="bg-blue-600 text-white px-6 py-2 rounded hover:bg-blue-700"
            disabled={loading}
          >
            {loading ? 'Loading...' : 'View Timetable'}
          </button>
        </div>

        {timetable && (
          <div className="bg-white rounded-lg shadow p-6 overflow-x-auto">
            <h3 className="text-lg font-bold mb-4">
              {timetable.branch} - Year {timetable.year} - Section {timetable.section}
            </h3>
            <table className="w-full border-collapse">
              <thead>
                <tr className="bg-green-600 text-white">
                  <th className="border p-2">Time / Day</th>
                  {timetable.days?.map((day: string) => (
                    <th key={day} className="border p-2">{day}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {timetable.time_slots?.map((slot: string) => (
                  <tr key={slot}>
                    <td className="border p-2 font-semibold">{slot}</td>
                    {timetable.days?.map((day: string) => (
                      <td 
                        key={day} 
                        className="border p-2 text-center"
                        dangerouslySetInnerHTML={{ 
                          __html: timetable.timetable?.[day]?.[slot] || '—' 
                        }}
                      />
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default StudentDashboard;