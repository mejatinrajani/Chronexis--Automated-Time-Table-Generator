import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import AuthCard from "@/components/AuthCard";
import InputField from "@/components/InputField";
import AppButton from "@/components/AppButton";

const Signup = () => {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const navigate = useNavigate();

  const handleSignup = (e: React.FormEvent) => {
    e.preventDefault();
    navigate("/dashboard");
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-background p-4">
      <AuthCard
        title="Create account"
        subtitle="Start building your timetables"
        footer={
          <span>
            Already have an account?{" "}
            <Link to="/login" className="text-foreground underline underline-offset-4 transition-colors hover:text-foreground/80">
              Sign in
            </Link>
          </span>
        }
      >
        <form onSubmit={handleSignup}>
          <InputField label="Full Name" placeholder="John Doe" value={name} onChange={setName} />
          <InputField label="Email" type="email" placeholder="you@example.com" value={email} onChange={setEmail} />
          <InputField label="Password" placeholder="••••••••" value={password} onChange={setPassword} showToggle />
          <InputField label="Confirm Password" placeholder="••••••••" value={confirm} onChange={setConfirm} showToggle />
          <AppButton type="submit" className="mt-2 w-full" size="lg">
            Create Account
          </AppButton>
        </form>
      </AuthCard>
    </div>
  );
};

export default Signup;
