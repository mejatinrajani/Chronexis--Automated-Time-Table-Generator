import { ReactNode, ButtonHTMLAttributes } from "react";
import { cn } from "@/lib/utils";

interface AppButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "ghost" | "outline";
  size?: "sm" | "md" | "lg";
  children: ReactNode;
}

const variants = {
  primary: "bg-primary text-primary-foreground hover:bg-foreground/90",
  secondary: "bg-secondary text-secondary-foreground hover:bg-accent",
  ghost: "text-muted-foreground hover:text-foreground hover:bg-accent",
  outline: "border border-border text-foreground hover:bg-accent",
};

const sizes = {
  sm: "px-3 py-1.5 text-xs",
  md: "px-5 py-2.5 text-sm",
  lg: "px-6 py-3 text-sm",
};

const AppButton = ({ variant = "primary", size = "md", className, children, ...props }: AppButtonProps) => (
  <button
    className={cn(
      "hover-sharp-to-round font-medium tracking-wide uppercase transition-all duration-200",
      variants[variant],
      sizes[size],
      className
    )}
    {...props}
  >
    {children}
  </button>
);

export default AppButton;
