import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Index from "./pages/Index";
import Login from "./pages/Login";
import Signup from "./pages/Signup";
import Dashboard from "./pages/Dashboard";
import Timetable from "./pages/Timetable";
import Generate from "./pages/Generate";
import Profile from "./pages/Profile";
import TeacherTimetable from "./pages/TeacherTimetable";
import RoomTimetable from "./pages/RoomSchedule";
import GenerateTimetableUsingExcel from "./pages/GenerateTimeTableUsingExcel";
import ValidateExsistingTimeTable from "./pages/ValidateExsistingTimeTable";
import NotFound from "./pages/NotFound";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Index />} />
          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<Signup />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/student-timetable" element={<Timetable />} />
          <Route path="/teacher-timetable" element={<TeacherTimetable />} />
          <Route path="/room's-schedule" element={<RoomTimetable />} />
          <Route path="/generate" element={<Generate />} />
          <Route path="/generate-with-excel" element={<GenerateTimetableUsingExcel />} />
          <Route path="/validate-timetable" element={<ValidateExsistingTimeTable />} />
          <Route path="/profile" element={<Profile />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
