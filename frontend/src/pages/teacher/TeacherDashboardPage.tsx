import React, { useEffect, useState } from 'react';
import {
  BookOpen,
  FileText,
  Users,
  Network,
  BarChart3,
  Plus,
  ArrowRight,
  ShieldCheck,
  AlertTriangle,
  HelpCircle,
  Sparkles,
} from 'lucide-react';
import { Link } from 'react-router-dom';
import PageHeader from '../../components/common/PageHeader';
import Card, { CardContent, CardHeader, CardTitle, CardDescription } from '../../components/common/Card';
import Button from '../../components/common/Button';
import Badge from '../../components/common/Badge';
import analyticsService from '../../services/analyticsService';
import { TeacherAnalyticsResponse } from '../../types/analytics';

export const TeacherDashboardPage: React.FC = () => {
  const [stats, setStats] = useState<TeacherAnalyticsResponse | null>(null);

  useEffect(() => {
    analyticsService.getTeacherAnalytics().then(setStats).catch(() => null);
  }, []);

  return (
    <div className="space-y-6 max-w-7xl">
      <PageHeader
        title="Teacher Dashboard"
        description="Curriculum management, document processing, and student knowledge analytics overview."
        breadcrumbs={[{ label: 'Teacher' }, { label: 'Dashboard' }]}
        badge={<Badge variant="primary">Instructor View</Badge>}
        actions={
          <Link to="/teacher/documents">
            <Button size="sm" leftIcon={<Plus className="w-4 h-4" />}>
              Upload Document
            </Button>
          </Link>
        }
      />

      {/* Live Operational Metrics Ribbon */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="border border-slate-200">
          <CardContent className="p-4">
            <div className="text-xs font-medium text-slate-500 flex items-center gap-1">
              <BookOpen className="w-3.5 h-3.5 text-blue-600" />
              Active Courses
            </div>
            <div className="text-2xl font-bold text-slate-900 mt-1">
              {stats ? stats.total_courses : '—'}
            </div>
            <div className="text-[11px] text-slate-500 mt-0.5">Under management</div>
          </CardContent>
        </Card>

        <Card className="border border-slate-200">
          <CardContent className="p-4">
            <div className="text-xs font-medium text-slate-500 flex items-center gap-1">
              <FileText className="w-3.5 h-3.5 text-purple-600" />
              Indexed Documents
            </div>
            <div className="text-2xl font-bold text-purple-700 mt-1">
              {stats ? stats.total_documents : '—'}
            </div>
            <div className="text-[11px] text-slate-500 mt-0.5">Knowledge base sources</div>
          </CardContent>
        </Card>

        <Card className="border border-slate-200">
          <CardContent className="p-4">
            <div className="text-xs font-medium text-slate-500 flex items-center gap-1">
              <HelpCircle className="w-3.5 h-3.5 text-indigo-600" />
              Student Queries
            </div>
            <div className="text-2xl font-bold text-indigo-700 mt-1">
              {stats ? stats.total_queries : '—'}
            </div>
            <div className="text-[11px] text-slate-500 mt-0.5">Interactions logged</div>
          </CardContent>
        </Card>

        <Card className="border border-slate-200">
          <CardContent className="p-4">
            <div className="text-xs font-medium text-slate-500 flex items-center gap-1">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
              Mean Grounding Score
            </div>
            <div className="text-2xl font-bold text-emerald-700 mt-1">
              {stats ? `${Math.round(stats.avg_support_score * 100)}%` : '—'}
            </div>
            <div className="text-[11px] text-slate-500 mt-0.5">Factual evidence accuracy</div>
          </CardContent>
        </Card>
      </div>

      {/* Module Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <Card hover>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="w-9 h-9 rounded-lg bg-blue-100 text-blue-600 flex items-center justify-center">
                <BookOpen className="w-5 h-5" />
              </div>
              <Badge variant="outline" size="sm">Management</Badge>
            </div>
            <CardTitle className="mt-3">Course Management</CardTitle>
            <CardDescription>
              Create courses, assign syllabi, and set student access scopes.
            </CardDescription>
          </CardHeader>
          <CardContent className="pt-0">
            <Link to="/teacher/courses">
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
                <FileText className="w-5 h-5" />
              </div>
              <Badge variant="outline" size="sm">Phase 1–3</Badge>
            </div>
            <CardTitle className="mt-3">Document Processing</CardTitle>
            <CardDescription>
              Upload course PDFs for dynamic chunking and hyperedge extraction.
            </CardDescription>
          </CardHeader>
          <CardContent className="pt-0">
            <Link to="/teacher/documents">
              <Button variant="ghost" size="sm" className="w-full justify-between" rightIcon={<ArrowRight className="w-4 h-4" />}>
                Manage Documents
              </Button>
            </Link>
          </CardContent>
        </Card>

        <Card hover>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="w-9 h-9 rounded-lg bg-indigo-100 text-indigo-600 flex items-center justify-center">
                <Network className="w-5 h-5" />
              </div>
              <Badge variant="purple" size="sm">HyperNetX</Badge>
            </div>
            <CardTitle className="mt-3">Hypergraph Explorer</CardTitle>
            <CardDescription>
              Visualize high-order concept hyperedges, entity centrality, and clusters.
            </CardDescription>
          </CardHeader>
          <CardContent className="pt-0">
            <Link to="/teacher/hypergraph">
              <Button variant="ghost" size="sm" className="w-full justify-between" rightIcon={<ArrowRight className="w-4 h-4" />}>
                Explore Graphs
              </Button>
            </Link>
          </CardContent>
        </Card>

        <Card hover>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="w-9 h-9 rounded-lg bg-emerald-100 text-emerald-600 flex items-center justify-center">
                <Users className="w-5 h-5" />
              </div>
              <Badge variant="outline" size="sm">Roster</Badge>
            </div>
            <CardTitle className="mt-3">Student Management</CardTitle>
            <CardDescription>
              Monitor enrolled students, study activity, and knowledge mastery.
            </CardDescription>
          </CardHeader>
          <CardContent className="pt-0">
            <Link to="/teacher/students">
              <Button variant="ghost" size="sm" className="w-full justify-between" rightIcon={<ArrowRight className="w-4 h-4" />}>
                View Students
              </Button>
            </Link>
          </CardContent>
        </Card>

        <Card hover>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="w-9 h-9 rounded-lg bg-amber-100 text-amber-600 flex items-center justify-center">
                <BarChart3 className="w-5 h-5" />
              </div>
              <Badge variant="warning" size="sm">Telemetry</Badge>
            </div>
            <CardTitle className="mt-3">Learning Analytics</CardTitle>
            <CardDescription>
              Track common student queries, concept bottlenecks, and hallucination audits.
            </CardDescription>
          </CardHeader>
          <CardContent className="pt-0">
            <Link to="/teacher/analytics">
              <Button variant="ghost" size="sm" className="w-full justify-between" rightIcon={<ArrowRight className="w-4 h-4" />}>
                View Analytics
              </Button>
            </Link>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default TeacherDashboardPage;
