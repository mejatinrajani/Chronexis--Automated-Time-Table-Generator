import { ReactNode } from "react";
import { X } from "lucide-react";
import AppButton from "./AppButton";

interface ModalProps {
  open: boolean;
  onClose: () => void;
  title: string;
  children: ReactNode;
  actions?: ReactNode;
}

const Modal = ({ open, onClose, title, children, actions }: ModalProps) => {
  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-background/80 backdrop-blur-sm" onClick={onClose} />
      <div className="relative w-full max-w-md border border-border bg-card p-6 animate-fade-in">
        <div className="mb-4 flex items-center justify-between">
          <h3 className="text-sm font-semibold uppercase tracking-wider text-foreground">{title}</h3>
          <button onClick={onClose} className="text-muted-foreground transition-colors hover:text-foreground">
            <X size={16} />
          </button>
        </div>
        <div className="text-sm text-muted-foreground">{children}</div>
        {actions && <div className="mt-6 flex justify-end gap-2">{actions}</div>}
      </div>
    </div>
  );
};

export default Modal;
