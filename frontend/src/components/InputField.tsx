import { useState } from "react";
import { Eye, EyeOff } from "lucide-react";

interface InputFieldProps {
  label: string;
  type?: string;
  placeholder?: string;
  value: string;
  onChange: (value: string) => void;
  showToggle?: boolean;
}

const InputField = ({ label, type = "text", placeholder, value, onChange, showToggle }: InputFieldProps) => {
  const [visible, setVisible] = useState(false);
  const inputType = showToggle ? (visible ? "text" : "password") : type;

  return (
    <div className="mb-5">
      <label className="mb-1.5 block text-xs font-medium uppercase tracking-widest text-muted-foreground">
        {label}
      </label>
      <div className="relative">
        <input
          type={inputType}
          placeholder={placeholder}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="focus-glow w-full border border-border bg-secondary px-4 py-3 text-sm text-foreground placeholder:text-muted-foreground outline-none transition-colors duration-200 focus:border-foreground/30"
        />
        {showToggle && (
          <button
            type="button"
            onClick={() => setVisible(!visible)}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground transition-colors hover:text-foreground"
          >
            {visible ? <EyeOff size={16} /> : <Eye size={16} />}
          </button>
        )}
      </div>
    </div>
  );
};

export default InputField;
