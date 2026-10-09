export type Role = "student" | "faculty" | "admin";
export type Risk = "safe" | "warning" | "critical";

export interface Me {
  id: number;
  email: string;
  role: Role;
  name: string;
  profile_id: number;
}


export interface StudentInfo {
  id: number;
  roll_no: string;
  name: string;
  email: string;
  department: string;
  batch_year: number;
  current_semester: number;
  section: string;
  mentor: string | null;
}

export interface AttendanceSummary {
  attended: number;
  total: number;
  percentage: number | null;
  risk: Risk;
  classes_needed: number;
  can_skip: number;
}

export interface AttendanceReport {
  semester: number;
  overall: AttendanceSummary;
  courses: (AttendanceSummary & { course_id: number; code: string; name: string })[];
  courses_at_risk: number;
  recent_absences: { date: string; period: number; code: string }[];
}

export interface ExamMark {
  exam_id: number;
  type: string;
  max_marks: number;
  weightage: number;
  exam_date: string | null;
  marks: number | null;
  percentage: number | null;
}

export interface SemesterMarks {
  semester: number;
  courses: {
    course_id: number;
    code: string;
    name: string;
    grade: string | null;
    total_marks: number | null;
    exams: ExamMark[];
  }[];
}

export interface Results {
  cgpa: number | null;
  credits_earned: number;
  active_backlogs: number;
  semesters: {
    semester: number;
    sgpa: number | null;
    credits: number;
    credits_earned: number;
    cgpa_upto: number | null;
    courses: { code: string; name: string; credits: number; grade: string; grade_points: number; total_marks: number }[];
  }[];
  years: { year: number; semesters: number[]; gpa: number | null }[];
}

export interface AssignmentItem {
  id: number;
  title: string;
  description: string | null;
  course_code: string;
  course_name: string;
  due_date: string;
  max_marks: number;
  marks: number | null;
  submitted_at: string | null;
  status: "pending" | "overdue" | "submitted" | "late" | "graded";
}

export interface Assignments {
  items: AssignmentItem[];
  pending: number;
  overdue: number;
}

export interface CertificationItem {
  id: number;
  title: string;
  issuer: string;
  issue_date: string;
  credential_url: string | null;
  verified: boolean;
  verified_by: string | null;
}

export interface Activities {
  clubs: { club: string; category: string; role: string; joined_on: string }[];
  activities: { id: number; title: string; type: string; level: string; achievement: string | null; date: string; club: string | null }[];
}

export interface Question {
  id: string;
  text: string;
  type: "rating" | "text";
}

export interface FeedbackFormItem {
  id: number;
  title: string;
  course_code: string | null;
  faculty: string | null;
  open_from: string;
  due_date: string;
  questions: Question[];
  overdue?: boolean;
  submitted_at?: string;
}

export interface FeedbackForms {
  pending: FeedbackFormItem[];
  completed: FeedbackFormItem[];
}

export interface PlacementCheck {
  name: string;
  required: number;
  actual: number | null;
  passed: boolean;
  gap: number | null;
}

export interface Placement {
  eligible: boolean;
  criteria_defined: boolean;
  checks: PlacementCheck[];
}

export interface Remark {
  id: number;
  category: string;
  remark: string;
  visibility: "student" | "faculty_only";
  faculty: string;
  created_at: string;
}

export interface HelpThread {
  id: number;
  student_id: number;
  student_name: string | null;
  subject: string;
  message: string;
  course_code: string | null;
  status: "open" | "in_progress" | "resolved";
  assigned_to: string | null;
  assigned_faculty_id: number | null;
  created_at: string;
  replies: { id: number; author: string; author_is_student: boolean; message: string; created_at: string }[];
}

export interface StudentDashboard {
  student: StudentInfo;
  cgpa: number | null;
  last_sgpa: number | null;
  last_sgpa_semester: number | null;
  active_backlogs: number;
  credits_earned: number;
  attendance: AttendanceSummary;
  courses_at_risk: number;
  pending_feedback: number;
  pending_assignments: number;
  placement_eligible: boolean;
  sgpa_trend: { semester: number; sgpa: number | null; cgpa: number | null }[];
  attendance_by_course: { code: string; percentage: number | null; risk: Risk }[];
  upcoming_assignments: AssignmentItem[];
  recent_remarks: Remark[];
}

export interface StudentOverview {
  id: number;
  roll_no: string;
  name: string;
  section: string;
  current_semester: number;
  mentor_faculty_id: number | null;
  cgpa: number | null;
  last_sgpa: number | null;
  attendance_pct: number | null;
  attendance_risk: Risk;
  courses_at_risk: number;
  active_backlogs: number;
  placement_eligible: boolean;
}

export interface AtRiskStudent extends StudentOverview {
  reasons: string[];
  severity: "high" | "medium";
}

export interface FacultyDashboard {
  faculty: { id: number; name: string; designation: string; department: string };
  total_students: number;
  my_mentees: number;
  average_cgpa: number | null;
  attendance_critical: number;
  attendance_warning: number;
  with_backlogs: number;
  placement_eligible: number;
  open_help_requests: number;
  cgpa_distribution: { range: string; students: number }[];
  at_risk: AtRiskStudent[];
}

export interface StudentProfileFull {
  student: StudentInfo;
  profile: { tenth_pct: number | null; twelfth_pct: number | null; phone: string | null };
  results: Results;
  attendance: AttendanceReport;
  marks: SemesterMarks[];
  assignments: Assignments;
  certifications: CertificationItem[];
  activities: Activities;
  feedback_forms: FeedbackForms;
  placement: Placement;
  remarks: Remark[];
  help_requests: HelpThread[];
}

export interface SuccessScoreComponent {
  label: string;
  raw: string;
  normalized: number;
  weight: number;
  contribution: number;
  impact: "positive" | "warning" | "negative";
}

export interface StudentSuccessScoreData {
  overall_score: number;
  score_category: "Excellent" | "Good" | "Average" | "At Risk";
  breakdown: Record<string, SuccessScoreComponent>;
  history: { score: number; category: string; date: string }[];
  calculated_at?: string;
}

export interface PlacementReadinessData {
  overall_score: number;
  category: "Placement Ready" | "Developing" | "Needs Improvement";
  components: Record<string, { score: number; weight: number; contribution: number }>;
  strengths: string[];
  skill_gaps: string[];
  recommendations: string[];
  calculated_at?: string;
}

export interface AcademicRiskData {
  risk_probability: number;
  risk_category: "low" | "medium" | "high";
  model_version: string;
  contributing_factors: { factor: string; impact: number; direction: "positive" | "negative"; detail: string }[];
  suggested_interventions: string[];
  features?: Record<string, number>;
  prediction_timestamp?: string;
}

export interface PlacementRiskData {
  risk_probability: number;
  risk_category: "low" | "medium" | "high";
  readiness_score: number;
  model_version: string;
  key_factors: string[];
  recommendations: string[];
  prediction_timestamp?: string;
}

export interface StudentSegmentData {
  student_id: number;
  segment_code: "A" | "B" | "C" | "D";
  segment_name: string;
  description: string;
  color: string;
  assignment_reason: string;
  metrics: {
    cgpa: number;
    attendance_pct: number;
    success_score: number;
    readiness_score: number;
    coding_score: number;
    aptitude_score: number;
    backlogs: number;
  };
}

export interface InterventionItem {
  id: number;
  student_id: number;
  student_name?: string | null;
  student_roll?: string | null;
  faculty_id?: number | null;
  faculty_name?: string | null;
  category: "academic" | "placement" | "attendance" | "counseling";
  title: string;
  description: string;
  urgency: "low" | "medium" | "high" | "critical";
  status: "pending" | "in_progress" | "completed" | "dismissed";
  action_steps: string[];
  student_notes?: string | null;
  faculty_notes?: string | null;
  outcome?: string | null;
  target_date?: string | null;
  created_at?: string | null;
  completed_at?: string | null;
}

export interface NotificationItem {
  id: number;
  title: string;
  message: string;
  type: string;
  severity: "info" | "warning" | "critical" | "success";
  is_read: boolean;
  link_url?: string | null;
  created_at?: string | null;
}

export interface SmartInsightItem {
  id: string;
  type: "attendance" | "placement" | "intervention" | "academic";
  severity: "info" | "warning" | "critical" | "success";
  title: string;
  summary: string;
  impact: string;
  recommendation: string;
  action_link?: string;
  stat?: string;
}

export interface SkillProfile {
  technical: number;
  communication: number;
  teamwork: number;
  leadership: number;
  problem_solving: number;
  aptitude: number;
  mock_interview: number;
  source: string;
  assessment_date?: string;
}

export interface LMSActivityData {
  login_count: number;
  course_views: number;
  videos_watched: number;
  assignments_completed: number;
  time_spent_hours: number;
  last_active?: string | null;
}

export interface AdminDashboardData {
  kpis: {
    total_students: number;
    total_faculty: number;
    total_departments: number;
    average_cgpa: number | null;
    average_attendance: number | null;
    average_success_score: number | null;
    average_placement_readiness: number | null;
    placement_eligible_count: number;
    high_risk_students: number;
    total_interventions: number;
    completed_interventions: number;
    intervention_completion_rate: number;
  };
  success_score_distribution: { range: string; count: number }[];
  readiness_distribution: { category: string; count: number; color: string }[];
}

export interface SystemSettingsData {
  success_score_weights: Record<string, number>;
  placement_readiness_weights: Record<string, number>;
  thresholds: Record<string, number>;
}

export interface ModelMetadataItem {
  id: number;
  model_name: string;
  model_version: string;
  algorithm: string;
  metrics: Record<string, any>;
  feature_importances: Record<string, number>;
  trained_at?: string | null;
  is_active: boolean;
}

export type ModelMetadata = ModelMetadataItem;

export interface UserProfile {
  id: number;
  email: string;
  name: string;
  role: Role;
  is_active: boolean;
  extra?: string;
  created_at: string;
}

export interface SegmentationSummary {
  total_students: number;
  distribution: {
    code: string;
    name: string;
    count: number;
    percentage: number;
    color: string;
    description: string;
  }[];
  segments: Record<string, any[]>;
}

export interface FullStudentAnalytics {
  success_score: StudentSuccessScoreData;
  placement_readiness: PlacementReadinessData;
  academic_risk: AcademicRiskData;
  placement_risk: any;
  segment: {
    segment_code: string;
    segment_name: string;
    assignment_reason: string;
    metrics: any;
  };
  trends: any;
}

