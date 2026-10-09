import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api, errorMessage, useApi } from "../../api/client";
import type {
  FullStudentAnalytics,
  InterventionItem,
  StudentProfileFull,
} from "../../api/types";
import { HelpThreadCard } from "../../components/HelpThread";
import {
  Badge,
  Card,
  Empty,
  PageHeader,
  QueryState,
  RiskBadge,
  StatCard,
  Tabs,
  fmt,
} from "../../components/ui";
import { ActivitiesView } from "../student/Activities";
import { AssignmentsView } from "../student/Assignments";
import { AttendanceView } from "../student/Attendance";
import { CertificationsView } from "../student/Certifications";
import { FeedbackStatusView } from "../student/Feedback";
import { ResultsView } from "../student/Grades";
import { MarksView } from "../student/Marks";
import { PlacementView } from "../student/Placement";
import { RemarksView } from "../student/Remarks";
import { WriteRemark } from "./WriteRemark";
import { SuccessScoreCard } from "../../components/SuccessScoreCard";
import { PlacementReadinessCard } from "../../components/PlacementReadinessCard";
import { RiskAnalysisCard } from "../../components/RiskAnalysisCard";
import { InterventionsManager } from "../../components/InterventionsManager";
import {
  Award,
  CheckCircle2,
  AlertCircle,
  Save,
} from "lucide-react";

const TABS = [
  { id: "overview", label: "Overview" },
  { id: "analytics", label: "Analytics & Interventions" },
  { id: "skills", label: "Skills Assessment" },
  { id: "attendance", label: "Attendance" },
  { id: "marks", label: "Marks" },
  { id: "results", label: "SGPA & CGPA" },
  { id: "assignments", label: "Assignments" },
  { id: "certifications", label: "Certifications" },
  { id: "activities", label: "Activities" },
  { id: "feedback", label: "Feedback forms" },
  { id: "remarks", label: "Remarks" },
  { id: "help", label: "Help requests" },
] as const;

type Tab = (typeof TABS)[number]["id"];

function SkillsAssessmentForm({
  studentId,
  onSaved,
}: {
  studentId: number;
  onSaved: () => void;
}) {
  const [tech, setTech] = useState("75");
  const [comm, setComm] = useState("80");
  const [team, setTeam] = useState("85");
  const [lead, setLead] = useState("70");
  const [prob, setProb] = useState("75");
  const [apt, setApt] = useState("70");
  const [mock, setMock] = useState("75");
  const [source, setSource] = useState("Faculty Evaluation");
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setMsg(null);
    setErr(null);
    try {
      await api.post("/analytics/skills", {
        student_id: studentId,
        technical_score: parseFloat(tech),
        communication_score: parseFloat(comm),
        teamwork_score: parseFloat(team),
        leadership_score: parseFloat(lead),
        problem_solving_score: parseFloat(prob),
        aptitude_score: parseFloat(apt),
        mock_interview_score: parseFloat(mock),
        assessment_source: source.trim() || "Faculty Assessment",
      });
      setMsg("Skills assessment recorded and placement readiness recalculated successfully!");
      onSaved();
    } catch (e) {
      setErr(errorMessage(e));
    } finally {
      setSaving(false);
    }
  };

  return (
    <Card
      title="Record / Update Skills Assessment"
      action={<span className="text-xs text-slate-400">Scores from 0 to 100</span>}
    >
      {msg && (
        <div className="mb-4 flex items-center gap-2 rounded-xl border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-800">
          <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-600" />
          <span>{msg}</span>
        </div>
      )}
      {err && (
        <div className="mb-4 flex items-center gap-2 rounded-xl border border-rose-200 bg-rose-50 p-3 text-sm text-rose-800">
          <AlertCircle className="h-4 w-4 shrink-0 text-rose-600" />
          <span>{err}</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700">Technical (0-100)</label>
            <input
              type="number"
              min="0"
              max="100"
              required
              className="input mt-1"
              value={tech}
              onChange={(e) => setTech(e.target.value)}
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-700">Communication (0-100)</label>
            <input
              type="number"
              min="0"
              max="100"
              required
              className="input mt-1"
              value={comm}
              onChange={(e) => setComm(e.target.value)}
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-700">Teamwork (0-100)</label>
            <input
              type="number"
              min="0"
              max="100"
              required
              className="input mt-1"
              value={team}
              onChange={(e) => setTeam(e.target.value)}
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-700">Leadership (0-100)</label>
            <input
              type="number"
              min="0"
              max="100"
              required
              className="input mt-1"
              value={lead}
              onChange={(e) => setLead(e.target.value)}
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-700">Problem Solving (0-100)</label>
            <input
              type="number"
              min="0"
              max="100"
              required
              className="input mt-1"
              value={prob}
              onChange={(e) => setProb(e.target.value)}
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-700">Aptitude (0-100)</label>
            <input
              type="number"
              min="0"
              max="100"
              required
              className="input mt-1"
              value={apt}
              onChange={(e) => setApt(e.target.value)}
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-700">Mock Interview (0-100)</label>
            <input
              type="number"
              min="0"
              max="100"
              required
              className="input mt-1"
              value={mock}
              onChange={(e) => setMock(e.target.value)}
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-700">Assessment Context</label>
            <input
              type="text"
              className="input mt-1"
              placeholder="e.g. Mid-term review"
              value={source}
              onChange={(e) => setSource(e.target.value)}
            />
          </div>
        </div>

        <button
          type="submit"
          disabled={saving}
          className="btn-primary inline-flex items-center gap-2"
        >
          <Save className="h-4 w-4" />
          {saving ? "Saving Assessment..." : "Save Assessment"}
        </button>
      </form>
    </Card>
  );
}

function Detail({ d, url }: { d: StudentProfileFull; url: string }) {
  const qc = useQueryClient();
  const [tab, setTab] = useState<Tab>("overview");
  const refresh = () => qc.invalidateQueries({ queryKey: [url] });
  const verify = useMutation({
    mutationFn: (id: number) => api.post(`/faculty/certifications/${id}/verify`),
    onSuccess: refresh,
  });
  const s = d.student;

  const analyticsQ = useApi<FullStudentAnalytics>(`/analytics/student/${s.id}/full-analytics`);
  const interventionsQ = useApi<InterventionItem[]>(`/interventions?student_id=${s.id}`);

  const handleRefreshAnalytics = () => {
    qc.invalidateQueries({ queryKey: [`/analytics/student/${s.id}/full-analytics`] });
    qc.invalidateQueries({ queryKey: [`/interventions?student_id=${s.id}`] });
  };

  return (
    <>
      <PageHeader
        title={s.name}
        subtitle={`${s.roll_no} · ${s.email} · Semester ${s.current_semester}, Section ${s.section}${
          s.mentor ? ` · Mentor: ${s.mentor}` : ""
        }`}
        action={
          <Link to="/faculty/students" className="btn-secondary">
            ← All students
          </Link>
        }
      />
      <Tabs tabs={[...TABS]} value={tab} onChange={setTab} />

      {tab === "overview" && (
        <div className="space-y-5">
          <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
            <StatCard
              label="CGPA"
              value={fmt(d.results.cgpa)}
              tone={d.results.cgpa !== null && d.results.cgpa < 6 ? "bad" : "default"}
            />
            <StatCard
              label="Attendance"
              value={`${d.attendance.overall.percentage ?? "—"}%`}
              hint={<RiskBadge risk={d.attendance.overall.risk} />}
            />
            <StatCard
              label="Backlogs"
              value={d.results.active_backlogs}
              tone={d.results.active_backlogs ? "bad" : "good"}
            />
            <StatCard label="Pending feedback" value={d.feedback_forms.pending.length} />
          </div>
          <div className="grid gap-5 lg:grid-cols-2">
            <div>
              <h2 className="mb-3 text-sm font-semibold text-slate-900">Placement eligibility</h2>
              <PlacementView data={d.placement} />
            </div>
            <div className="space-y-5">
              <WriteRemark studentId={s.id} studentName={s.name.split(" ")[0]} onSaved={refresh} />
              <Card title="Academic background">
                <dl className="grid grid-cols-3 gap-3 text-sm">
                  <div>
                    <dt className="text-xs text-slate-500">10th</dt>
                    <dd className="font-medium">{d.profile.tenth_pct ?? "—"}%</dd>
                  </div>
                  <div>
                    <dt className="text-xs text-slate-500">12th</dt>
                    <dd className="font-medium">{d.profile.twelfth_pct ?? "—"}%</dd>
                  </div>
                  <div>
                    <dt className="text-xs text-slate-500">Phone</dt>
                    <dd className="font-medium">{d.profile.phone ?? "—"}</dd>
                  </div>
                </dl>
              </Card>
            </div>
          </div>
        </div>
      )}

      {tab === "analytics" && (
        <div className="space-y-6">
          {analyticsQ.isLoading ? (
            <div className="p-8 text-center text-sm text-slate-500">Loading analytics...</div>
          ) : analyticsQ.data ? (
            <>
              {/* Segment Banner */}
              <div className="flex items-center justify-between rounded-2xl border border-indigo-200 bg-indigo-50/60 p-4">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-600 text-white font-bold">
                    <Award className="h-5 w-5" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-bold text-slate-900">
                        Assigned Cohort: Segment {analyticsQ.data.segment.segment_code} -{" "}
                        {analyticsQ.data.segment.segment_name}
                      </span>
                    </div>
                    <p className="text-xs text-slate-600 mt-0.5">
                      Rationale: {analyticsQ.data.segment.assignment_reason}
                    </p>
                  </div>
                </div>
                <Badge color="blue">Active Segment</Badge>
              </div>

              {/* Success Score & Placement Readiness */}
              <div className="grid gap-6 lg:grid-cols-2">
                <SuccessScoreCard data={analyticsQ.data.success_score} />
                <PlacementReadinessCard data={analyticsQ.data.placement_readiness} />
              </div>

              {/* Academic Risk */}
              <RiskAnalysisCard data={analyticsQ.data.academic_risk} />

              {/* Interventions Management */}
              <InterventionsManager
                interventions={interventionsQ.data || []}
                isFaculty={true}
                studentId={s.id}
                onRefresh={handleRefreshAnalytics}
              />
            </>
          ) : (
            <Empty>Unable to load analytics for this student.</Empty>
          )}
        </div>
      )}

      {tab === "skills" && (
        <div className="space-y-6">
          <SkillsAssessmentForm studentId={s.id} onSaved={handleRefreshAnalytics} />
          {analyticsQ.data && (
            <PlacementReadinessCard data={analyticsQ.data.placement_readiness} />
          )}
        </div>
      )}

      {tab === "attendance" && <AttendanceView data={d.attendance} />}
      {tab === "marks" && <MarksView data={d.marks} />}
      {tab === "results" && <ResultsView data={d.results} />}
      {tab === "assignments" && <AssignmentsView data={d.assignments} />}
      {tab === "certifications" && (
        <CertificationsView
          items={d.certifications}
          renderAction={(c) =>
            !c.verified && (
              <button
                className="btn-secondary px-2 py-1 text-xs"
                disabled={verify.isPending}
                onClick={() => verify.mutate(c.id)}
              >
                Mark verified
              </button>
            )
          }
        />
      )}
      {tab === "activities" && <ActivitiesView data={d.activities} />}
      {tab === "feedback" && <FeedbackStatusView data={d.feedback_forms} />}
      {tab === "remarks" && (
        <div className="space-y-5">
          <WriteRemark studentId={s.id} studentName={s.name.split(" ")[0]} onSaved={refresh} />
          <RemarksView items={d.remarks} />
        </div>
      )}
      {tab === "help" &&
        (d.help_requests.length === 0 ? (
          <Empty>This student has not raised any help requests.</Empty>
        ) : (
          <ul className="space-y-3">
            {d.help_requests.map((t) => (
              <HelpThreadCard
                key={t.id}
                thread={t}
                replyUrl={`/faculty/help-requests/${t.id}/replies`}
                onChanged={refresh}
              />
            ))}
          </ul>
        ))}
    </>
  );
}

export default function StudentDetail() {
  const { id } = useParams();
  const url = `/faculty/students/${id}`;
  const q = useApi<StudentProfileFull>(url);
  return <QueryState query={q}>{(d) => <Detail d={d} url={url} />}</QueryState>;
}
