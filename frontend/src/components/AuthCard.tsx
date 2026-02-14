import { ReactNode } from "react";

interface AuthCardProps {
  title: string;
  subtitle: string;
  children: ReactNode;
  footer?: ReactNode;
}

const AuthCard = ({ title, subtitle, children, footer }: AuthCardProps) => (
  <div className="w-full max-w-md animate-fade-in">
    <div className="mb-8 text-center">
      <h1 className="text-3xl font-bold tracking-tight text-foreground">{title}</h1>
      <p className="mt-2 text-sm text-muted-foreground">{subtitle}</p>
    </div>
    <div className="border border-border bg-card p-8">
      {children}
    </div>
    {footer && <div className="mt-6 text-center text-sm text-muted-foreground">{footer}</div>}
  </div>
);

export default AuthCard;
