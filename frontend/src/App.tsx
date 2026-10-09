import { Navigate, Route, Routes } from "react-router-dom";
import { ProtectedRoute } from "./auth/ProtectedRoute";
import { Layout, type NavItem } from "./components/Layout";
import FacultyDashboard from "./pages/faculty/Dashboard";
import HelpInbox from "./pages/faculty/HelpInbox";
import StudentDetail from "./pages/faculty/StudentDetail";
import StudentList from "./pages/faculty/StudentList";
import Login from "./pages/Login";
import Activities from "./pages/student/Activities";
import Assignments from "./pages/student/Assignments";
import Attendance from "./pages/student/Attendance";
import Certifications from "./pages/student/Certifications";
import StudentDashboard from "./pages/student/Dashboard";
import Feedback from "./pages/student/Feedback";
import Grades from "./pages/student/Grades";
import HelpRequests from "./pages/student/HelpRequests";
import Marks from "./pages/student/Marks";
import Placement from "./pages/student/Placement";
import Remarks from "./pages/student/Remarks";

// Administrator Pages
import AdminDashboard from "./pages/admin/Dashboard";
import AdminSegmentation from "./pages/admin/Segmentation";
import AdminSettings from "./pages/admin/Settings";
import AdminModels from "./pages/admin/Models";
import AdminUsers from "./pages/admin/Users";

const studentNav: NavItem[] = [
  { to: "/student", label: "Dashboard", end: true },
  { to: "/student/attendance", label: "Attendance" },
  { to: "/student/marks", label: "Exam marks" },
  { to: "/student/grades", label: "SGPA & CGPA" },
  { to: "/student/assignments", label: "Assignments" },
  { to: "/student/feedback", label: "Feedback forms" },
  { to: "/student/certifications", label: "Certifications" },
  { to: "/student/activities", label: "Clubs & activities" },
  { to: "/student/placement", label: "Placement eligibility" },
  { to: "/student/remarks", label: "Faculty remarks" },
  { to: "/student/help", label: "Ask for help" },
];

const facultyNav: NavItem[] = [
  { to: "/faculty", label: "Dashboard", end: true },
  { to: "/faculty/students", label: "Students" },
  { to: "/faculty/help", label: "Help requests" },
];

const adminNav: NavItem[] = [
  { to: "/admin", label: "Executive Dashboard", end: true },
  { to: "/admin/segmentation", label: "Student Segmentation" },
  { to: "/admin/settings", label: "Weight Engine & Formulas" },
  { to: "/admin/models", label: "Predictive Models & Governance" },
  { to: "/admin/users", label: "User Management" },
];

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />

      {/* Student Portal */}
      <Route
        path="/student"
        element={
          <ProtectedRoute role="student">
            <Layout nav={studentNav} portal="Student Portal" />
          </ProtectedRoute>
        }
      >
        <Route index element={<StudentDashboard />} />
        <Route path="attendance" element={<Attendance />} />
        <Route path="marks" element={<Marks />} />
        <Route path="grades" element={<Grades />} />
        <Route path="assignments" element={<Assignments />} />
        <Route path="feedback" element={<Feedback />} />
        <Route path="certifications" element={<Certifications />} />
        <Route path="activities" element={<Activities />} />
        <Route path="placement" element={<Placement />} />
        <Route path="remarks" element={<Remarks />} />
        <Route path="help" element={<HelpRequests />} />
      </Route>

      {/* Faculty Portal */}
      <Route
        path="/faculty"
        element={
          <ProtectedRoute role="faculty">
            <Layout nav={facultyNav} portal="Faculty Portal" />
          </ProtectedRoute>
        }
      >
        <Route index element={<FacultyDashboard />} />
        <Route path="students" element={<StudentList />} />
        <Route path="students/:id" element={<StudentDetail />} />
        <Route path="help" element={<HelpInbox />} />
      </Route>

      {/* Administrator Portal */}
      <Route
        path="/admin"
        element={
          <ProtectedRoute role="admin">
            <Layout nav={adminNav} portal="Administrator Portal" />
          </ProtectedRoute>
        }
      >
        <Route index element={<AdminDashboard />} />
        <Route path="segmentation" element={<AdminSegmentation />} />
        <Route path="settings" element={<AdminSettings />} />
        <Route path="models" element={<AdminModels />} />
        <Route path="users" element={<AdminUsers />} />
      </Route>

      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  );
}
