import { useState } from "react";
import { BRANCHES, YEARS } from "@/lib/store";
import { toast } from "sonner";

const CreateSection = () => {
  const [branch, setBranch] = useState("");
  const [year, setYear] = useState("1st Year");
  const [name, setName] = useState("");
  const [count, setCount] = useState(60);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!branch || !name) { toast.error("Branch and Section Name are required"); return; }
    store.addSection({ branch, year, name, studentCount: count });
    toast.success("Section created!");
    setName("");
  };

  return (
    <div className="bg-card/60 backdrop-blur-md rounded-xl p-8 border border-border">
      <h2 className="text-2xl font-bold mb-6">📋 Create New Section</h2>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div><label className="block text-sm font-medium mb-1">Branch *</label>
            <select value={branch} onChange={e => setBranch(e.target.value)} className="w-full px-4 py-2.5 rounded-lg bg-background/50 border border-border focus:ring-2 focus:ring-primary focus:outline-none">
              <option value="">Select Branch</option>{BRANCHES.map(b => <option key={b} value={b}>{b}</option>)}
            </select></div>
          <div><label className="block text-sm font-medium mb-1">Year *</label>
            <select value={year} onChange={e => setYear(e.target.value)} className="w-full px-4 py-2.5 rounded-lg bg-background/50 border border-border focus:ring-2 focus:ring-primary focus:outline-none">
              {YEARS.map(y => <option key={y} value={y}>{y}</option>)}
            </select></div>
          <div><label className="block text-sm font-medium mb-1">Section Name *</label>
            <input value={name} onChange={e => setName(e.target.value)} placeholder="e.g., A, B, C" className="w-full px-4 py-2.5 rounded-lg bg-background/50 border border-border focus:ring-2 focus:ring-primary focus:outline-none" /></div>
          <div><label className="block text-sm font-medium mb-1">Student Count</label>
            <input type="number" value={count} onChange={e => setCount(Number(e.target.value))} className="w-full px-4 py-2.5 rounded-lg bg-background/50 border border-border focus:ring-2 focus:ring-primary focus:outline-none" /></div>
        </div>
        <button type="submit" className="px-6 py-2.5 rounded-lg text-primary-foreground font-medium" style={{ background: "var(--gradient-nebula)" }}>+ Create Section</button>
      </form>
    </div>
  );
};

export default CreateSection;
