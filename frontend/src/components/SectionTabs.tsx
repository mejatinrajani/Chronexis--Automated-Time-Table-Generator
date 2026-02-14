import { cn } from "@/lib/utils";

interface SectionTabsProps {
  sections: string[];
  active: string;
  onChange: (section: string) => void;
}

const SectionTabs = ({ sections, active, onChange }: SectionTabsProps) => (
  <>
    {/* Style to hide scrollbar but keep functionality */}
    <style>{`
      .no-scrollbar::-webkit-scrollbar {
        display: none;
      }
      .no-scrollbar {
        -ms-overflow-style: none;
        scrollbar-width: none;
      }
    `}</style>

    <div 
      className={cn(
        "flex items-center gap-0 border border-border overflow-x-auto no-scrollbar",
        "bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60", // Optional: slight transparency
        "rounded-md", // Optional: rounded corners for the whole bar
        "min-w-0 flex-1", // CRITICAL: Allows it to shrink and scroll inside a flex parent
        "max-w-full sm:max-w-[calc(100vw-350px)]" // Responsive constraint: leaves space for buttons on right
      )}
    >
      {sections.map((section) => (
        <button
          key={section}
          onClick={() => onChange(section)}
          className={cn(
            "relative px-6 py-3 text-[20px] font-medium uppercase tracking-widest transition-all duration-200 whitespace-nowrap border-r border-border/50 last:border-r-0",
            active === section
              ? "bg-foreground text-background"
              : "text-muted-foreground hover:text-foreground hover:bg-accent"
          )}
        >
          {section}
        </button>
      ))}
    </div>
  </>
);

export default SectionTabs;