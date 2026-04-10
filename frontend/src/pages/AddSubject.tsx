// frontend/src/pages/AddSubject.tsx
import { useState } from "react";
import { store, BRANCHES, YEARS } from "@/lib/store";
import { toast } from "sonner";

const AddSubject = () => {
  const [code, setCode] = useState("");
  const [name, setName] = useState("");
  const [branch, setBranch] = useState("");
  const [year, setYear] = useState("1st Year");
  const [semester, setSemester] = useState("Semester 1");
  const [credits, setCredits] = useState(3);
  const [hours, setHours] = useState(3);
  const [isLab, setIsLab] = useState(false);
  const [subjects, setSubjects] = useState(store.getSubjects());

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!code || !name) {
      toast.error("Code and Name are required");
      return;
    }
    store.addSubject({ code, name, branch, year, semester, credits, hoursPerWeek: hours, isLab });
    setSubjects(store.getSubjects());
    setCode("");
    setName("");
    toast.success("Subject added!");
  };

  return (
    <div className="bg-gray-800/60 backdrop-blur-md rounded-xl p-8 border border-gray-700">
      <h2 className="text-2xl font-bold mb-6 text-white">📚 Add New Subject</h2>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div><label className="block text-sm font-medium mb-1 text-gray-300">Subject Code *</label>
            <input value={code} onChange={e => setCode(e.target.value)} className="w-full px-4 py-2.5 rounded-lg bg-gray-900/50 border border-gray-700 text-white focus:ring-2 focus:ring-purple-500 focus:outline-none" /></div>
          <div><label className="block text-sm font-medium mb-1 text-gray-300">Subject Name *</label>
            <input value={name} onChange={e => setName(e.target.value)} className="w-full px-4 py-2.5 rounded-lg bg-gray-900/50 border border-gray-700 text-white focus:ring-2 focus:ring-purple-500 focus:outline-none" /></div>
          <div><label className="block text-sm font-medium mb-1 text-gray-300">Branch</label>
            <select value={branch} onChange={e => setBranch(e.target.value)} className="w-full px-4 py-2.5 rounded-lg bg-gray-900/50 border border-gray-700 text-white focus:ring-2 focus:ring-purple-500 focus:outline-none">
              <option value="">Select Branch</option>{BRANCHES.map(b => <option key={b} value={b}>{b}</option>)}
            </select></div>
          <div><label className="block text-sm font-medium mb-1 text-gray-300">Year</label>
            <select value={year} onChange={e => setYear(e.target.value)} className="w-full px-4 py-2.5 rounded-lg bg-gray-900/50 border border-gray-700 text-white focus:ring-2 focus:ring-purple-500 focus:outline-none">
              {YEARS.map(y => <option key={y} value={y}>{y}</option>)}
            </select></div>
          <div><label className="block text-sm font-medium mb-1 text-gray-300">Semester</label>
            <select value={semester} onChange={e => setSemester(e.target.value)} className="w-full px-4 py-2.5 rounded-lg bg-gray-900/50 border border-gray-700 text-white focus:ring-2 focus:ring-purple-500 focus:outline-none">
              {[1,2,3,4,5,6,7,8].map(s => <option key={s} value={`Semester ${s}`}>Semester {s}</option>)}
            </select></div>
          <div><label className="block text-sm font-medium mb-1 text-gray-300">Credits</label>
            <input type="number" value={credits} onChange={e => setCredits(Number(e.target.value))} className="w-full px-4 py-2.5 rounded-lg bg-gray-900/50 border border-gray-700 text-white focus:ring-2 focus:ring-purple-500 focus:outline-none" /></div>
          <div><label className="block text-sm font-medium mb-1 text-gray-300">Hours/Week</label>
            <input type="number" value={hours} onChange={e => setHours(Number(e.target.value))} className="w-full px-4 py-2.5 rounded-lg bg-gray-900/50 border border-gray-700 text-white focus:ring-2 focus:ring-purple-500 focus:outline-none" /></div>
          <div className="flex items-center gap-3 pt-6">
            <input type="checkbox" checked={isLab} onChange={e => setIsLab(e.target.checked)} className="w-4 h-4 rounded border-gray-700" />
            <label className="text-sm font-medium text-gray-300">Is Lab Course?</label>
          </div>
        </div>
        <button type="submit" className="px-6 py-2.5 rounded-lg text-white font-medium bg-gradient-to-r from-purple-600 to-pink-600 hover:opacity-90 transition">+ Add Subject</button>
      </form>

      {subjects.length > 0 && (
        <div className="mt-8">
          <h3 className="text-lg font-bold mb-4 text-white">📚 Existing Subjects</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-gray-300">
              <thead><tr className="border-b border-gray-700">
                <th className="text-left py-3 px-4 text-sm">Code</th><th className="text-left py-3 px-4 text-sm">Name</th>
                <th className="text-left py-3 px-4 text-sm">Branch</th><th className="text-left py-3 px-4 text-sm">Year</th>
                <th className="text-left py-3 px-4 text-sm">Hours/Week</th>
              </tr></thead>
              <tbody>{subjects.map(s => (
                <tr key={s.id} className="border-b border-gray-800">
                  <td className="py-3 px-4">{s.code}</td><td className="py-3 px-4">{s.name}</td>
                  <td className="py-3 px-4">{s.branch}</td><td className="py-3 px-4">{s.year}</td>
                  <td className="py-3 px-4">{s.hoursPerWeek}</td>
                </tr>
              ))}</tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

export default AddSubject;