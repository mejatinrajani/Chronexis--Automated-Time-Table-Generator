import { ReactNode } from "react";
import AppSidebar from "./AppSidebar";
import HeaderBar from "./HeaderBar";

interface DashboardLayoutProps {
  title: string;
  children: ReactNode;
}

const DashboardLayout = ({ title, children }: DashboardLayoutProps) => (
  <div className="flex min-h-screen w-full">
    <AppSidebar />
    <div className="flex flex-1 flex-col pl-16 lg:pl-56">
      <HeaderBar title={title} />
      <main className="flex-1 p-6">{children}</main>
    </div>
  </div>
);

export default DashboardLayout;
