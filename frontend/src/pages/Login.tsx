import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import AuthCard from "@/components/AuthCard";
import InputField from "@/components/InputField";
import AppButton from "@/components/AppButton";

const Login = () => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const navigate = useNavigate();

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    navigate("/dashboard");
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-background p-4">
      <AuthCard
        title="Welcome back"
        subtitle="Sign in to manage your timetables"
        footer={
          <span>
            Don't have an account?{" "}
            <Link to="/signup" className="text-foreground underline underline-offset-4 transition-colors hover:text-foreground/80">
              Sign up
            </Link>
          </span>
        }
      >
        <form onSubmit={handleLogin}>
          <InputField label="Email" type="email" placeholder="you@example.com" value={email} onChange={setEmail} />
          <InputField label="Password" placeholder="••••••••" value={password} onChange={setPassword} showToggle />
          <AppButton type="submit" className="mt-2 w-full" size="lg">
            Sign In
          </AppButton>
        </form>
      </AuthCard>
    </div>
  );
};

export default Login;
