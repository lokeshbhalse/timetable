// frontend/src/pages/AssignSubject.tsx
import { useState } from "react";
import { store, BRANCHES, YEARS } from "@/lib/store";
import { toast } from "sonner";

const AssignSubject = () => {
  const [branch, setBranch] = useState("");
  const [year, setYear] = useState("1st Year");
  const [subjectId, setSubjectId] = useState("");
  const [teacherId, setTeacherId] = useState("");
  const [section, setSection] = useState("");

  const subjects = store.getSubjects().filter(s => (!branch || s.branch === branch) && s.year === year);
  const teachers = store.getTeachers();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!branch || !subjectId || !teacherId || !section) {
      toast.error("All fields are required");
      return;
    }
    store.addAssignment({ branch, year, subjectId, teacherId, section });
    toast.success("Subject assigned!");
    setSubjectId(""); setTeacherId(""); setSection("");
  };

  return (
    <div className="bg-gray-800/60 backdrop-blur-md rounded-xl p-8 border border-gray-700">
      <h2 className="text-2xl font-bold mb-6 text-white">🔗 Assign Subject to Teacher & Section</h2>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div><label className="block text-sm font-medium mb-1 text-gray-300">Branch *</label>
            <select value={branch} onChange={e => setBranch(e.target.value)} className="w-full px-4 py-2.5 rounded-lg bg-gray-900/50 border border-gray-700 text-white focus:ring-2 focus:ring-purple-500 focus:outline-none">
              <option value="">Select Branch</option>{BRANCHES.map(b => <option key={b} value={b}>{b}</option>)}
            </select></div>
          <div><label className="block text-sm font-medium mb-1 text-gray-300">Year *</label>
            <select value={year} onChange={e => setYear(e.target.value)} className="w-full px-4 py-2.5 rounded-lg bg-gray-900/50 border border-gray-700 text-white focus:ring-2 focus:ring-purple-500 focus:outline-none">
              {YEARS.map(y => <option key={y} value={y}>{y}</option>)}
            </select></div>
          <div><label className="block text-sm font-medium mb-1 text-gray-300">Subject *</label>
            <select value={subjectId} onChange={e => setSubjectId(e.target.value)} className="w-full px-4 py-2.5 rounded-lg bg-gray-900/50 border border-gray-700 text-white focus:ring-2 focus:ring-purple-500 focus:outline-none">
              <option value="">Select Subject</option>{subjects.map(s => <option key={s.id} value={s.id}>{s.name} ({s.code})</option>)}
            </select></div>
          <div><label className="block text-sm font-medium mb-1 text-gray-300">Teacher *</label>
            <select value={teacherId} onChange={e => setTeacherId(e.target.value)} className="w-full px-4 py-2.5 rounded-lg bg-gray-900/50 border border-gray-700 text-white focus:ring-2 focus:ring-purple-500 focus:outline-none">
              <option value="">Select Teacher</option>{teachers.map(t => <option key={t.id} value={t.id}>{t.name}</option>)}
            </select></div>
        </div>
        <div><label className="block text-sm font-medium mb-1 text-gray-300">Section *</label>
          <input value={section} onChange={e => setSection(e.target.value)} placeholder="e.g., A, B, C" className="w-full px-4 py-2.5 rounded-lg bg-gray-900/50 border border-gray-700 text-white focus:ring-2 focus:ring-purple-500 focus:outline-none" /></div>
        <button type="submit" className="px-6 py-2.5 rounded-lg text-white font-medium bg-gradient-to-r from-purple-600 to-pink-600 hover:opacity-90 transition">🔗 Assign Subject</button>
      </form>
    </div>
  );
};

export default AssignSubject;