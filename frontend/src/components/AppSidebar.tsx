import { Calendar, Settings, Grid3X3, Check, User, Search, LogOut, LayoutDashboard } from "lucide-react";
import { NavLink, useLocation } from "react-router-dom";
import { cn } from "@/lib/utils";

const links = [
  { to: "/dashboard", icon: LayoutDashboard, label: "Dashboard" },
  { to: "/student-timetable", icon: Calendar, label: "Student's Timetable" },
  { to: "/teacher-timetable", icon: Calendar, label: "Teacher's Timetable" },
  { to: "/room's-schedule", icon: Calendar, label: "Room's Schedule" },
  { to: "/generate", icon: Grid3X3, label: "Generate" },
  { to: "/generate-with-excel", icon: Grid3X3, label: "Generate with Excel" },
  { to: "/validate-timetable", icon: Check, label: "Validate Exsisting TimeTable" },
  { to: "/profile", icon: User, label: "Profile" },
];

const AppSidebar = () => {
  const location = useLocation();

  return (
    <aside className="fixed left-0 top-0 z-40 flex h-screen w-16 flex-col items-center border-r border-border bg-sidebar py-6 transition-all duration-300 lg:w-56">
      {/* Logo */}
      <div className="mb-10 flex items-center gap-2 px-4">
        <div className="">
        </div>
        <span className="hidden text-[25px] font-semibold tracking-wider text-foreground lg:block">
          TIMETABLE
        </span>
      </div>

      {/* Navigation */}
      <nav className="flex flex-1 flex-col gap-1 w-full px-2">
        {links.map((link) => {
          const active = location.pathname === link.to;
          return (
            <NavLink
              key={link.to}
              to={link.to}
              className={cn(
                "flex items-center gap-5 px-4 py-4 text-lg transition-all duration-200 hover-sharp-to-round",
                active
                  ? "bg-accent text-foreground"
                  : "text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
              )}
            >
              <link.icon size={18} />
              <span className="hidden lg:block">{link.label}</span>
            </NavLink>
          );
        })}
      </nav>

      {/* Bottom */}
      <div className="w-full px-2">
        <button className="flex w-full items-center gap-5 px-4 py-4 text-lg text-sidebar-foreground transition-all duration-200 hover-sharp-to-round hover:bg-sidebar-accent hover:text-sidebar-accent-foreground">
          <LogOut size={18} />
          <span className="hidden lg:block">Logout</span>
        </button>
      </div>
    </aside>
  );
};

export default AppSidebar;
