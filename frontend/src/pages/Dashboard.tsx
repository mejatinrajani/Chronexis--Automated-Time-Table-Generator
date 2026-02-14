import DashboardLayout from "@/components/DashboardLayout";
import { Calendar, Grid3X3, Users, Clock } from "lucide-react";

const stats = [
  { label: "Total Classes", value: "24", icon: Grid3X3 },
  { label: "Sections", value: "3", icon: Users },
  { label: "Time Slots", value: "9", icon: Clock },
  { label: "Days Active", value: "5", icon: Calendar },
];

const Dashboard = () => (
  <DashboardLayout title="Dashboard">
    <div className="animate-fade-in space-y-8">
      {/* Stats */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat, i) => (
          <div
            key={stat.label}
            className="border border-border bg-card p-6 transition-all duration-200 cell-hover"
            style={{ animationDelay: `${i * 80}ms` }}
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-[10px] font-medium uppercase tracking-widest text-muted-foreground">{stat.label}</p>
                <p className="mt-2 text-3xl font-bold tracking-tight text-foreground">{stat.value}</p>
              </div>
              <stat.icon size={20} className="text-muted-foreground/40" />
            </div>
          </div>
        ))}
      </div>

      {/* Quick actions */}
      <div>
        <h3 className="mb-4 text-xs font-medium uppercase tracking-widest text-muted-foreground">Quick Actions</h3>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
          <a href="/student-timetable" className="group border border-border bg-card p-5 transition-all duration-200 cell-hover block">
            <Calendar size={20} className="mb-3 text-foreground" />
            <p className="text-sm font-medium text-foreground">View Timetable</p>
            <p className="mt-1 text-xs text-muted-foreground">See current schedule</p>
          </a>
          <a href="/generate" className="group border border-border bg-card p-5 transition-all duration-200 cell-hover block">
            <Grid3X3 size={20} className="mb-3 text-foreground" />
            <p className="text-sm font-medium text-foreground">Generate New</p>
            <p className="mt-1 text-xs text-muted-foreground">Create a new timetable</p>
          </a>
          <div className="border border-dashed border-border bg-card/50 p-5 flex items-center justify-center">
            <p className="text-xs text-muted-foreground">More features coming soon</p>
          </div>
        </div>
      </div>

      {/* Recent activity placeholder */}
      <div>
        <h3 className="mb-4 text-xs font-medium uppercase tracking-widest text-muted-foreground">Recent Activity</h3>
        <div className="space-y-2">
          {["Timetable for Section A updated", "New subject 'AI/ML' added", "Section C schedule generated"].map((item, i) => (
            <div key={i} className="flex items-center gap-3 border border-border bg-card p-4 transition-all duration-200 cell-hover">
              <div className="h-2 w-2 bg-foreground/30" />
              <p className="text-xs text-muted-foreground">{item}</p>
              <span className="ml-auto text-[10px] text-muted-foreground/50">{i + 1}h ago</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  </DashboardLayout>
);

export default Dashboard;
