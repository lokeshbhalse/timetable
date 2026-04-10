import { useNavigate, useLocation } from "react-router-dom";
import {
  LayoutDashboard,
  CalendarDays,
  Calendar,
  BarChart3,
  Gift,
  Users,
  Database,
  Settings,
  HelpCircle,
  FileText,
  PhoneCall,
  MessageCircle,
  Clock,
  LogOut,
} from "lucide-react";

const mainLinks = [
  { label: "Dashboard", icon: LayoutDashboard, path: "/admin/dashboard" },
  { label: "My Timetables", icon: CalendarDays, path: "/admin/timetables" },
  { label: "Calendar", icon: Calendar, path: "/admin/calendar" },
  { label: "Reports & Analytics", icon: BarChart3, path: "/admin/reports" },
];

const managementLinks = [
  { label: "Users", icon: Users, path: "/admin/users" },
  { label: "Master Data", icon: Database, path: "/admin/master-data" },
  { label: "Settings", icon: Settings, path: "/admin/settings" },
];

const helpLinks = [
  { label: "Support", icon: HelpCircle, path: "#" },
  { label: "Help Docs", icon: FileText, path: "#", external: true },
  { label: "Schedule a Call", icon: PhoneCall, path: "#", external: true },
  { label: "WhatsApp Us", icon: MessageCircle, path: "#", external: true },
];

const AdminSidebar = () => {
  const navigate = useNavigate();
  const location = useLocation();

  const isActive = (path: string) => location.pathname === path;

  const renderLink = (link: typeof mainLinks[0] & { external?: boolean }) => {
    const active = isActive(link.path);
    return (
      <button
        key={link.label}
        onClick={() => link.path !== "#" && navigate(link.path)}
        className={`w-full flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm font-medium transition-all ${
          active
            ? "bg-primary/10 text-primary"
            : "text-muted-foreground hover:bg-muted hover:text-foreground"
        }`}
      >
        <link.icon className="w-4.5 h-4.5 shrink-0" />
        <span className="flex-1 text-left">{link.label}</span>
        {link.external && (
          <span className="text-muted-foreground/50 text-xs">↗</span>
        )}
      </button>
    );
  };

  return (
    <aside className="w-64 h-screen bg-card border-r border-border flex flex-col fixed left-0 top-0 z-40">
      {/* Logo */}
      <div className="p-6 pb-4">
        <div className="flex items-center gap-2">
          <Clock className="w-6 h-6 text-primary" />
          <span className="text-lg font-display font-bold text-foreground">
            TimeTable<span className="text-primary">X</span>
          </span>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto px-3 space-y-6">
        {/* Main */}
        <div>
          <p className="px-4 text-xs font-semibold text-muted-foreground/70 uppercase tracking-wider mb-2">Main</p>
          <div className="space-y-1">{mainLinks.map(renderLink)}</div>
        </div>

        {/* Request Free Trial */}
        <div className="px-3">
          <button className="w-full flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm font-medium bg-gradient-to-r from-emerald-500 to-teal-500 text-white hover:brightness-110 transition">
            <Gift className="w-4.5 h-4.5" />
            Request Free Trial
          </button>
        </div>

        {/* Management */}
        <div>
          <p className="px-4 text-xs font-semibold text-muted-foreground/70 uppercase tracking-wider mb-2">Management</p>
          <div className="space-y-1">{managementLinks.map(renderLink)}</div>
        </div>

        {/* Help & Support */}
        <div>
          <p className="px-4 text-xs font-semibold text-muted-foreground/70 uppercase tracking-wider mb-2">Help & Support</p>
          <div className="space-y-1">{helpLinks.map(renderLink)}</div>
        </div>
      </nav>

      {/* User Profile */}
      <div className="border-t border-border p-4">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-full bg-primary/20 flex items-center justify-center text-primary font-bold text-sm">
            A
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-foreground truncate">Admin User</p>
            <p className="text-xs text-muted-foreground truncate">admin@timetablex.com</p>
          </div>
          <button
            onClick={() => navigate("/")}
            className="text-muted-foreground hover:text-destructive transition"
            title="Logout"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
    </aside>
  );
};

export default AdminSidebar;
