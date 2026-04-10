import AdminSidebar from "@/components/AdminSidebar";
import { User, Building2, CreditCard, CalendarOff, ArrowLeftRight, Bell, Key, ArrowRight } from "lucide-react";

const accountSettings = [
  { title: "Personal Profile", desc: "Update your personal information and account details", icon: User, color: "bg-blue-100 text-blue-600" },
  { title: "Organization", desc: "Manage institute details and organizational settings", icon: Building2, color: "bg-indigo-100 text-indigo-600" },
  { title: "Billing & Subscription", desc: "View your plan, billing history, and payment methods", icon: CreditCard, color: "bg-sky-100 text-sky-600" },
];

const preferences = [
  { title: "Leave Types", desc: "Configure leave types and policies for your organization", icon: CalendarOff, color: "bg-purple-100 text-purple-600" },
  { title: "Substitute Settings", desc: "Configure auto-substitute rules and teacher eligibility", icon: ArrowLeftRight, color: "bg-amber-100 text-amber-600" },
  { title: "Notifications", desc: "Control which push notifications are sent to your team", icon: Bell, color: "bg-yellow-100 text-yellow-600" },
];

const security = [
  { title: "API Keys", desc: "Generate and manage API keys for integrations", icon: Key, color: "bg-red-100 text-red-600" },
];

const SettingsSection = ({ title, subtitle, items }: { title: string; subtitle: string; items: typeof accountSettings }) => (
  <div className="bg-card border border-border rounded-xl p-6 mb-6">
    <h2 className="text-lg font-semibold text-foreground">{title}</h2>
    <p className="text-sm text-muted-foreground mb-5">{subtitle}</p>
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      {items.map((item) => (
        <div key={item.title} className="border border-border rounded-xl p-5 hover:shadow-md transition-shadow cursor-pointer group">
          <div className={`w-10 h-10 rounded-lg flex items-center justify-center mb-3 ${item.color}`}>
            <item.icon className="w-5 h-5" />
          </div>
          <h3 className="font-semibold text-foreground mb-1">{item.title}</h3>
          <p className="text-sm text-muted-foreground mb-3">{item.desc}</p>
          <span className="text-primary text-sm font-medium flex items-center gap-1 group-hover:gap-2 transition-all">
            Configure <ArrowRight className="w-4 h-4" />
          </span>
        </div>
      ))}
    </div>
  </div>
);

const AdminSettings = () => {
  return (
    <div className="flex min-h-screen bg-background">
      <AdminSidebar />
      <main className="flex-1 ml-64 p-8">
        <div className="mb-6">
          <h1 className="text-2xl font-display font-bold text-foreground">Settings</h1>
          <p className="text-muted-foreground text-sm mt-1">Manage your account settings, security, and preferences</p>
        </div>

        <SettingsSection title="Account Settings" subtitle="Manage your personal and organizational preferences" items={accountSettings} />
        <SettingsSection title="Preferences" subtitle="Customize your TimeTableX experience" items={preferences} />
        <SettingsSection title="Security & API" subtitle="Configure security settings and manage integrations" items={security} />
      </main>
    </div>
  );
};

export default AdminSettings;
