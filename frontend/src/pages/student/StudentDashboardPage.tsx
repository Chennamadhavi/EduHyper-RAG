import React, { useEffect, useState } from 'react';
import {
  BookOpen,
  Bot,
  History,
  TrendingUp,
  Sparkles,
  ArrowRight,
  ShieldCheck,
  HelpCircle,
} from 'lucide-react';
import { Link } from 'react-router-dom';
import PageHeader from '../../components/common/PageHeader';
import Card, { CardContent, CardHeader, CardTitle, CardDescription } from '../../components/common/Card';
import Button from '../../components/common/Button';
import Badge from '../../components/common/Badge';
import analyticsService from '../../services/analyticsService';
import { StudentProgressResponse } from '../../types/analytics';

export const StudentDashboardPage: React.FC = () => {
  const [progress, setProgress] = useState<StudentProgressResponse | null>(null);

  useEffect(() => {
    analyticsService.getStudentProgress().then(setProgress).catch(() => null);
  }, []);

  return (
    <div className="space-y-6 max-w-7xl">
      <PageHeader
        title="Student Dashboard"
        description="Personalized AI tutoring workspace, enrolled curriculum courses, and learning analytics."
        breadcrumbs={[{ label: 'Student' }, { label: 'Dashboard' }]}
        badge={<Badge variant="purple">Learner Portal</Badge>}
        actions={
          <Link to="/student/tutor">
            <Button size="sm" leftIcon={<Sparkles className="w-4 h-4" />}>
              Ask AI Tutor
            </Button>
          </Link>
        }
      />

      {/* Live Operational Metrics Ribbon */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="border border-slate-200">
          <CardContent className="p-4">
            <div className="text-xs font-medium text-slate-500 flex items-center gap-1">
              <HelpCircle className="w-3.5 h-3.5 text-blue-600" />
              Questions Asked
            </div>
            <div className="text-2xl font-bold text-slate-900 mt-1">
              {progress ? progress.total_queries : '—'}
            </div>
            <div className="text-[11px] text-slate-500 mt-0.5">Tutor sessions logged</div>
          </CardContent>
        </Card>

        <Card className="border border-slate-200">
          <CardContent className="p-4">
            <div className="text-xs font-medium text-slate-500 flex items-center gap-1">
              <BookOpen className="w-3.5 h-3.5 text-purple-600" />
              Enrolled Courses
            </div>
            <div className="text-2xl font-bold text-purple-700 mt-1">
              {progress ? progress.enrolled_courses_count : '—'}
            </div>
            <div className="text-[11px] text-slate-500 mt-0.5">Active curricula</div>
          </CardContent>
        </Card>

        <Card className="border border-slate-200">
          <CardContent className="p-4">
            <div className="text-xs font-medium text-slate-500 flex items-center gap-1">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
              Avg Grounding
            </div>
            <div className="text-2xl font-bold text-emerald-700 mt-1">
              {progress ? `${Math.round(progress.avg_support_score * 100)}%` : '—'}
            </div>
            <div className="text-[11px] text-slate-500 mt-0.5">Factual support accuracy</div>
          </CardContent>
        </Card>

        <Card className="border border-slate-200">
          <CardContent className="p-4">
            <div className="text-xs font-medium text-slate-500 flex items-center gap-1">
              <TrendingUp className="w-3.5 h-3.5 text-amber-600" />
              Verified Answers
            </div>
            <div className="text-2xl font-bold text-amber-700 mt-1">
              {progress ? `${progress.verified_rate_pct.toFixed(0)}%` : '—'}
            </div>
            <div className="text-[11px] text-slate-500 mt-0.5">Zero hallucination rate</div>
          </CardContent>
        </Card>
      </div>

      {/* Student Module Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <Card hover>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="w-9 h-9 rounded-lg bg-blue-100 text-blue-600 flex items-center justify-center">
                <Bot className="w-5 h-5" />
              </div>
              <Badge variant="primary" size="sm">Core Feature</Badge>
            </div>
            <CardTitle className="mt-3">AI Tutor Workspace</CardTitle>
            <CardDescription>
              Ask questions grounded strictly in course materials with verifiable citations.
            </CardDescription>
          </CardHeader>
          <CardContent className="pt-0">
            <Link to="/student/tutor">
              <Button variant="ghost" size="sm" className="w-full justify-between" rightIcon={<ArrowRight className="w-4 h-4" />}>
                Open Tutor
              </Button>
            </Link>
          </CardContent>
        </Card>

        <Card hover>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="w-9 h-9 rounded-lg bg-indigo-100 text-indigo-600 flex items-center justify-center">
                <BookOpen className="w-5 h-5" />
              </div>
              <Badge variant="outline" size="sm">Curriculum</Badge>
            </div>
            <CardTitle className="mt-3">My Enrolled Courses</CardTitle>
            <CardDescription>
              Access syllabus topics, assigned documents, and course materials.
            </CardDescription>
          </CardHeader>
          <CardContent className="pt-0">
            <Link to="/student/courses">
              <Button variant="ghost" size="sm" className="w-full justify-between" rightIcon={<ArrowRight className="w-4 h-4" />}>
                View Courses
              </Button>
            </Link>
          </CardContent>
        </Card>

        <Card hover>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="w-9 h-9 rounded-lg bg-purple-100 text-purple-600 flex items-center justify-center">
                <History className="w-5 h-5" />
              </div>
              <Badge variant="outline" size="sm">Past QA</Badge>
            </div>
            <CardTitle className="mt-3">Question History</CardTitle>
            <CardDescription>
              Review past explanations, verified claims, and hypergraph references.
            </CardDescription>
          </CardHeader>
          <CardContent className="pt-0">
            <Link to="/student/history">
              <Button variant="ghost" size="sm" className="w-full justify-between" rightIcon={<ArrowRight className="w-4 h-4" />}>
                View History
              </Button>
            </Link>
          </CardContent>
        </Card>

        <Card hover>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="w-9 h-9 rounded-lg bg-emerald-100 text-emerald-600 flex items-center justify-center">
                <TrendingUp className="w-5 h-5" />
              </div>
              <Badge variant="success" size="sm">Mastery</Badge>
            </div>
            <CardTitle className="mt-3">Learning Progress</CardTitle>
            <CardDescription>
              Track your concept grounding rates, course mastery, and question topics.
            </CardDescription>
          </CardHeader>
          <CardContent className="pt-0">
            <Link to="/student/progress">
              <Button variant="ghost" size="sm" className="w-full justify-between" rightIcon={<ArrowRight className="w-4 h-4" />}>
                View Progress
              </Button>
            </Link>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default StudentDashboardPage;
