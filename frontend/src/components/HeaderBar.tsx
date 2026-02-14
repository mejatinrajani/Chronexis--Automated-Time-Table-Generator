import { Search, Bell, ChevronDown } from "lucide-react";
import { useState } from "react";

interface HeaderBarProps {
  title: string;
}

const HeaderBar = ({ title }: HeaderBarProps) => {
  return (
    <header className="flex h-14 items-center justify-between border-b border-border bg-background px-6">
      <h2 className="text-[30px] font-medium tracking-wide text-foreground">{title}</h2>

      <div className="flex items-center gap-3">
        {/* Profile */}
        <button className="flex items-center gap-2 text-sm text-muted-foreground transition-colors hover:text-foreground">
          <div className="flex h-12 w-12 items-center justify-center border border-border bg-secondary text-[25px] font-medium text-foreground">
            JR
          </div>
          <span className="hidden text-[22px] md:block">Jatin Rajani</span>
        </button>
      </div>
    </header>
  );
};

export default HeaderBar;
