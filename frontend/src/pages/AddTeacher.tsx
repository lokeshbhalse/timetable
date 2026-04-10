// frontend/src/pages/AddTeacher.tsx
import { useState } from "react";
import { store, BRANCHES } from "@/lib/store";
import { toast } from "sonner";

const AddTeacher = () => {
  const [name, setName] = useState("");
  const [department, setDepartment] = useState("");
  const [email, setEmail] = useState("");
  const [maxHours, setMaxHours] = useState(6);
  const [teachers, setTeachers] = useState(store.getTeachers());

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name || !department) {
      toast.error("Name and Department are required");
      return;
    }
    store.addTeacher({ name, department, email, maxHoursPerDay: maxHours });
    setTeachers(store.getTeachers());
    setName("");
    setDepartment("");
    setEmail("");
    setMaxHours(6);
    toast.success("Teacher added successfully!");
  };

  return (
    <div className="bg-gray-800/60 backdrop-blur-md rounded-xl p-8 border border-gray-700">
      <h2 className="text-2xl font-bold mb-6 text-white">👨‍🏫 Add New Teacher</h2>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium mb-1 text-gray-300">Teacher Name *</label>
            <input value={name} onChange={e => setName(e.target.value)} className="w-full px-4 py-2.5 rounded-lg bg-gray-900/50 border border-gray-700 text-white focus:ring-2 focus:ring-purple-500 focus:outline-none" />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1 text-gray-300">Department *</label>
            <select value={department} onChange={e => setDepartment(e.target.value)} className="w-full px-4 py-2.5 rounded-lg bg-gray-900/50 border border-gray-700 text-white focus:ring-2 focus:ring-purple-500 focus:outline-none">
              <option value="">Select Department</option>
              {BRANCHES.map(b => <option key={b} value={b}>{b}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1 text-gray-300">Email</label>
            <input type="email" value={email} onChange={e => setEmail(e.target.value)} className="w-full px-4 py-2.5 rounded-lg bg-gray-900/50 border border-gray-700 text-white focus:ring-2 focus:ring-purple-500 focus:outline-none" />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1 text-gray-300">Max Hours/Day</label>
            <input type="number" value={maxHours} onChange={e => setMaxHours(Number(e.target.value))} className="w-full px-4 py-2.5 rounded-lg bg-gray-900/50 border border-gray-700 text-white focus:ring-2 focus:ring-purple-500 focus:outline-none" />
          </div>
        </div>
        <button type="submit" className="px-6 py-2.5 rounded-lg text-white font-medium bg-gradient-to-r from-purple-600 to-pink-600 hover:opacity-90 transition">
          + Add Teacher
        </button>
      </form>

      {teachers.length > 0 && (
        <div className="mt-8">
          <h3 className="text-lg font-bold mb-4 text-white">📋 Existing Teachers</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-gray-300">
              <thead>
                <tr className="border-b border-gray-700">
                  <th className="text-left py-3 px-4 text-sm">Name</th>
                  <th className="text-left py-3 px-4 text-sm">Department</th>
                  <th className="text-left py-3 px-4 text-sm">Max Hours/Day</th>
                </tr>
              </thead>
              <tbody>
                {teachers.map(t => (
                  <tr key={t.id} className="border-b border-gray-800">
                    <td className="py-3 px-4">{t.name}</td>
                    <td className="py-3 px-4">{t.department}</td>
                    <td className="py-3 px-4">{t.maxHoursPerDay}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

export default AddTeacher;