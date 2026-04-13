// frontend/src/pages/AddSubject.tsx
import { useState, useEffect, useCallback } from "react";
import { BRANCHES, YEARS } from "@/lib/store";
import { toast } from "sonner";
import api from "../services/api";

interface Teacher {
  id: string | number;
  name: string;
  department?: string;
  email?: string;
}

const AddSubject = () => {
  const [code, setCode] = useState("");
  const [name, setName] = useState("");
  const [branch, setBranch] = useState("");
  const [year, setYear] = useState<number>(1);
  const [semester, setSemester] = useState<number>(1);
  const [credits, setCredits] = useState(3);
  const [hours, setHours] = useState(3);
  const [isLab, setIsLab] = useState(false);
  const [teachers, setTeachers] = useState<Teacher[]>([]);
  const [teacherId, setTeacherId] = useState<number | null>(null);
  const [teacher2Id, setTeacher2Id] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);

  // Semester options based on year
  const getSemesterOptions = () => {
    if (year === 1) return [1, 2];
    if (year === 2) return [3, 4];
    if (year === 3) return [5, 6];
    if (year === 4) return [7, 8];
    return [1, 2];
  };

  const loadTeachers = useCallback(async () => {
    try {
      const response = await api.get("/admin/teachers");
      console.log("Teachers loaded:", response.data.teachers);
      setTeachers(response.data.teachers || []);
      
      if (response.data.teachers?.length === 0) {
        toast.warning("No teachers found. Please add a teacher first.");
      }
    } catch (error) {
      console.error("Error loading teachers:", error);
      toast.error("Failed to load teachers list");
    }
  }, []);

  useEffect(() => {
    loadTeachers();
  }, [loadTeachers]);

  // Reset semester when year changes
  useEffect(() => {
    const semesters = getSemesterOptions();
    setSemester(semesters[0]);
  }, [year]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!code) {
      toast.error("Subject Code is required");
      return;
    }
    if (!name) {
      toast.error("Subject Name is required");
      return;
    }
    if (!branch) {
      toast.error("Branch is required");
      return;
    }
    if (!teacherId) {
      toast.error("Please select a Primary Teacher");
      return;
    }
    
    setLoading(true);
    
    try {
      const token = localStorage.getItem('token');
      
      const requestData = {
        code: code.toUpperCase(),
        name: name,
        branch: branch,
        year: year,
        semester: semester,
        teacher_id: teacherId,
        teacher2_id: teacher2Id
      };
      
      console.log("Sending subject data:", JSON.stringify(requestData, null, 2));
      
      const response = await api.post("/admin/subjects", requestData, {
        headers: { 
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      console.log("Response:", response.data);
      
      if (response.data.success) {
        toast.success(`Subject "${name}" added successfully!`);
        // Reset form
        setCode("");
        setName("");
        setBranch("");
        setYear(1);
        setSemester(1);
        setTeacherId(null);
        setTeacher2Id(null);
        setCredits(3);
        setHours(3);
        setIsLab(false);
      } else {
        toast.error(response.data.message || "Failed to add subject");
      }
    } catch (error: any) {
      console.error("Error adding subject:", error);
      if (error.response) {
        console.error("Response data:", error.response.data);
        const errorMsg = error.response.data?.detail || error.response.data?.message || "Server error";
        toast.error(errorMsg);
      } else if (error.request) {
        toast.error("No response from server. Check if backend is running.");
      } else {
        toast.error("Failed to add subject. Please try again.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-card/60 backdrop-blur-md rounded-xl p-8 border border-border">
      <h2 className="text-2xl font-bold mb-6">📚 Add New Subject</h2>
      
      {teachers.length === 0 && (
        <div className="mb-4 p-3 bg-yellow-500/20 border border-yellow-500 rounded-lg text-yellow-200">
          ⚠️ No teachers found! Please go to "Add Teacher" first.
        </div>
      )}
      
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium mb-1">Subject Code *</label>
            <input 
              value={code} 
              onChange={e => setCode(e.target.value.toUpperCase())} 
              placeholder="e.g., EE301, CS201"
              className="w-full px-4 py-2.5 rounded-lg bg-background/50 border border-border focus:ring-2 focus:ring-primary focus:outline-none" 
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Subject Name *</label>
            <input 
              value={name} 
              onChange={e => setName(e.target.value)} 
              placeholder="e.g., Power System, Data Structures"
              className="w-full px-4 py-2.5 rounded-lg bg-background/50 border border-border focus:ring-2 focus:ring-primary focus:outline-none" 
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Branch *</label>
            <select 
              value={branch} 
              onChange={e => setBranch(e.target.value)} 
              className="w-full px-4 py-2.5 rounded-lg bg-background/50 border border-border focus:ring-2 focus:ring-primary focus:outline-none"
            >
              <option value="">Select Branch</option>
              {BRANCHES.map((b, idx) => <option key={`branch-${idx}`} value={b}>{b}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Year *</label>
            <select 
              value={year} 
              onChange={e => setYear(parseInt(e.target.value))} 
              className="w-full px-4 py-2.5 rounded-lg bg-background/50 border border-border focus:ring-2 focus:ring-primary focus:outline-none"
            >
              <option value="1">1st Year</option>
              <option value="2">2nd Year</option>
              <option value="3">3rd Year</option>
              <option value="4">4th Year</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Semester *</label>
            <select 
              value={semester} 
              onChange={e => setSemester(parseInt(e.target.value))} 
              className="w-full px-4 py-2.5 rounded-lg bg-background/50 border border-border focus:ring-2 focus:ring-primary focus:outline-none"
            >
              {getSemesterOptions().map(s => (
                <option key={s} value={s}>Semester {s}</option>
              ))}
            </select>
            <p className="text-xs text-muted-foreground mt-1">
              {year === 1 && "1st Year → Semester 1 or 2"}
              {year === 2 && "2nd Year → Semester 3 or 4"}
              {year === 3 && "3rd Year → Semester 5 or 6"}
              {year === 4 && "4th Year → Semester 7 or 8"}
            </p>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Primary Teacher *</label>
            <select 
              value={teacherId || ""} 
              onChange={e => setTeacherId(e.target.value ? parseInt(e.target.value) : null)} 
              className="w-full px-4 py-2.5 rounded-lg bg-background/50 border border-border focus:ring-2 focus:ring-primary focus:outline-none"
            >
              <option value="">Select Primary Teacher</option>
              {teachers.map((t, idx) => (
                <option key={`teacher-${t.id || idx}`} value={t.id}>{t.name}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Second Teacher (Optional)</label>
            <select 
              value={teacher2Id || ""} 
              onChange={e => setTeacher2Id(e.target.value ? parseInt(e.target.value) : null)} 
              className="w-full px-4 py-2.5 rounded-lg bg-background/50 border border-border focus:ring-2 focus:ring-primary focus:outline-none"
            >
              <option value="">Select Second Teacher</option>
              {teachers.map((t, idx) => (
                <option key={`teacher2-${t.id || idx}`} value={t.id}>{t.name}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Credits</label>
            <input 
              type="number" 
              value={credits} 
              onChange={e => setCredits(Number(e.target.value))} 
              min="1"
              max="6"
              className="w-full px-4 py-2.5 rounded-lg bg-background/50 border border-border focus:ring-2 focus:ring-primary focus:outline-none" 
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Hours/Week</label>
            <input 
              type="number" 
              value={hours} 
              onChange={e => setHours(Number(e.target.value))} 
              min="1"
              max="8"
              className="w-full px-4 py-2.5 rounded-lg bg-background/50 border border-border focus:ring-2 focus:ring-primary focus:outline-none" 
            />
          </div>
          <div className="flex items-center gap-3 pt-6">
            <input 
              type="checkbox" 
              checked={isLab} 
              onChange={e => setIsLab(e.target.checked)} 
              className="w-4 h-4 rounded border-border" 
            />
            <label className="text-sm font-medium">Is Lab Course?</label>
          </div>
        </div>
        <button 
          type="submit" 
          disabled={loading || teachers.length === 0}
          className="px-6 py-2.5 rounded-lg text-primary-foreground font-medium disabled:opacity-50"
          style={{ background: "var(--gradient-nebula)" }}
        >
          {loading ? "Adding..." : "+ Add Subject"}
        </button>
      </form>
    </div>
  );
};

export default AddSubject;