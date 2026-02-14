import { useState } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import InputField from "@/components/InputField";
import AppButton from "@/components/AppButton";
import { Camera, Mail, User, Shield, Clock } from "lucide-react";

const Profile = () => {
  const [name, setName] = useState("John Doe");
  const [email, setEmail] = useState("john@example.com");
  const [role, setRole] = useState("Administrator");

  return (
    <DashboardLayout title="Profile">
      <div className="animate-fade-in mx-auto max-w-2xl space-y-8">
        {/* Avatar section */}
        <div className="flex items-center gap-6 border border-border bg-card p-6">
          <div className="relative group">
            <div className="flex h-20 w-20 items-center justify-center border border-border bg-secondary text-2xl font-bold text-foreground">
              JD
            </div>
            <button className="absolute inset-0 flex items-center justify-center bg-background/60 opacity-0 transition-opacity duration-200 group-hover:opacity-100">
              <Camera size={18} className="text-foreground" />
            </button>
          </div>
          <div>
            <h2 className="text-lg font-semibold text-foreground">{name}</h2>
            <p className="text-xs text-muted-foreground">{email}</p>
            <div className="mt-2 flex items-center gap-1">
              <Shield size={10} className="text-muted-foreground" />
              <span className="text-[10px] uppercase tracking-widest text-muted-foreground">{role}</span>
            </div>
          </div>
        </div>

        {/* Personal info */}
        <div className="border border-border bg-card p-6">
          <h3 className="mb-5 text-xs font-medium uppercase tracking-widest text-muted-foreground">Personal Information</h3>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <InputField label="Full Name" placeholder="John Doe" value={name} onChange={setName} />
            <InputField label="Email" type="email" placeholder="john@example.com" value={email} onChange={setEmail} />
            <InputField label="Role" placeholder="Administrator" value={role} onChange={setRole} />
            <InputField label="Department" placeholder="Computer Science" value="" onChange={() => {}} />
          </div>
          <div className="mt-5 flex justify-end">
            <AppButton size="md">Save Changes</AppButton>
          </div>
        </div>

        {/* Security */}
        <div className="border border-border bg-card p-6">
          <h3 className="mb-5 text-xs font-medium uppercase tracking-widest text-muted-foreground">Security</h3>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <InputField label="Current Password" value="" onChange={() => {}} showToggle />
            <InputField label="New Password" value="" onChange={() => {}} showToggle />
          </div>
          <div className="mt-5 flex justify-end">
            <AppButton variant="outline" size="md">Update Password</AppButton>
          </div>
        </div>

        {/* Activity */}
        <div className="border border-border bg-card p-6">
          <h3 className="mb-4 text-xs font-medium uppercase tracking-widest text-muted-foreground">Recent Activity</h3>
          <div className="space-y-3">
            {[
              { action: "Edited Section A timetable", time: "2 hours ago" },
              { action: "Generated new timetable", time: "Yesterday" },
              { action: "Added subject 'AI/ML'", time: "3 days ago" },
              { action: "Account created", time: "1 week ago" },
            ].map((item, i) => (
              <div key={i} className="flex items-center justify-between py-2 border-b border-border last:border-0">
                <div className="flex items-center gap-3">
                  <Clock size={12} className="text-muted-foreground/50" />
                  <span className="text-xs text-muted-foreground">{item.action}</span>
                </div>
                <span className="text-[10px] text-muted-foreground/50">{item.time}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Danger zone */}
        <div className="border border-border bg-card p-6">
          <h3 className="mb-3 text-xs font-medium uppercase tracking-widest text-destructive-foreground">Danger Zone</h3>
          <p className="mb-4 text-xs text-muted-foreground">Once you delete your account, there is no going back.</p>
          <AppButton variant="outline" size="sm">Delete Account</AppButton>
        </div>
      </div>
    </DashboardLayout>
  );
};

export default Profile;
