import AdminSidebar from "@/components/AdminSidebar";
import { Search, Filter, Mail, Calendar, Star, CheckCircle2 } from "lucide-react";

const mockUsers = [
  { name: "Prince Mehra", email: "mrgaiusjuliusceasar@gmail.com", role: "Owner", verified: true, added: "Apr 5, 2026", initials: "PM" },
  { name: "Sarah Johnson", email: "sarah.j@school.edu", role: "Teacher", verified: true, added: "Mar 20, 2026", initials: "SJ" },
  { name: "Mike Chen", email: "mike.chen@school.edu", role: "Student", verified: false, added: "Mar 15, 2026", initials: "MC" },
];

const roleColors: Record<string, string> = {
  Owner: "bg-amber-100 text-amber-700 border-amber-200",
  Teacher: "bg-emerald-100 text-emerald-700 border-emerald-200",
  Student: "bg-blue-100 text-blue-700 border-blue-200",
};

const AdminUsers = () => {
  return (
    <div className="flex min-h-screen bg-background">
      <AdminSidebar />
      <main className="flex-1 ml-64 p-8">
        <div className="mb-6">
          <h1 className="text-2xl font-display font-bold text-foreground">Users</h1>
          <p className="text-muted-foreground text-sm mt-1">Manage your organization members and their permissions</p>
        </div>

        {/* Search & Filter */}
        <div className="flex items-center gap-3 mb-6">
          <div className="flex-1 relative">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <input
              type="text"
              placeholder="Search users..."
              className="w-full rounded-lg bg-card text-foreground border border-border pl-10 pr-4 py-2.5 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring transition"
            />
          </div>
          <button className="flex items-center gap-2 px-4 py-2.5 rounded-lg border border-border bg-card text-foreground text-sm hover:bg-muted transition">
            <Filter className="w-4 h-4" />
            Filter
          </button>
        </div>

        {/* User List */}
        <div className="space-y-3">
          {mockUsers.map((user) => (
            <div key={user.email} className="bg-card border border-border rounded-xl p-5 flex items-center gap-4">
              <div className="w-12 h-12 rounded-full bg-primary/15 flex items-center justify-center text-primary font-bold text-sm shrink-0">
                {user.initials}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <span className="font-semibold text-foreground">{user.name}</span>
                  <span className={`text-xs px-2 py-0.5 rounded-full border font-medium flex items-center gap-1 ${roleColors[user.role] || ""}`}>
                    {user.role === "Owner" && <Star className="w-3 h-3" />}
                    {user.role}
                  </span>
                  {user.verified && (
                    <span className="text-xs text-emerald-600 flex items-center gap-1">
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      Verified
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-4 text-sm text-muted-foreground">
                  <span className="flex items-center gap-1.5">
                    <Mail className="w-3.5 h-3.5" />
                    {user.email}
                  </span>
                  <span className="flex items-center gap-1.5">
                    <Calendar className="w-3.5 h-3.5" />
                    Added {user.added}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
};

export default AdminUsers;
