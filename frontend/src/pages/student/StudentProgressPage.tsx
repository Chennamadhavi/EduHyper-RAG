import React, { useEffect, useState } from 'react';
import {
  TrendingUp,
  BookOpen,
  HelpCircle,
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  RefreshCw,
  MessageSquare,
  ArrowRight,
  Clock,
  Sparkles,
} from 'lucide-react';
import { Link } from 'react-router-dom';
import PageHeader from '../../components/common/PageHeader';
import Card, { CardContent } from '../../components/common/Card';
import Button from '../../components/common/Button';
import Badge from '../../components/common/Badge';
import LoadingState from '../../components/common/LoadingState';
import EmptyState from '../../components/common/EmptyState';
import analyticsService from '../../services/analyticsService';
import { StudentProgressResponse } from '../../types/analytics';

export const StudentProgressPage: React.FC = () => {
  const [progress, setProgress] = useState<StudentProgressResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadProgress();
  }, []);

  const loadProgress = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await analyticsService.getStudentProgress();
      setProgress(data);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to load student progress.');
    } finally {
      setIsLoading(false);
    }
  };

  const renderDecisionBadge = (decision?: string) => {
    switch (decision?.toUpperCase()) {
      case 'VERIFIED':
      case 'ACCEPT':
        return (
          <Badge variant="success" size="sm">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
            VERIFIED
          </Badge>
        );
      case 'PARTIALLY_SUPPORTED':
        return (
          <Badge variant="warning" size="sm">
            <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
            PARTIALLY SUPPORTED
          </Badge>
        );
      case 'REGENERATE':
      case 'REJECT_INSUFFICIENT':
      case 'UNSUPPORTED':
        return (
          <Badge variant="danger" size="sm">
            <XCircle className="w-3.5 h-3.5 text-red-600" />
            UNSUPPORTED
          </Badge>
        );
      default:
        return (
          <Badge variant="default" size="sm">
            {decision || 'PROCESSED'}
          </Badge>
        );
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-6 max-w-6xl">
        <PageHeader
          title="Learning Progress"
          description="Personal learning analytics, concept grounding rates, and curriculum mastery."
          breadcrumbs={[{ label: 'Student', path: '/student/dashboard' }, { label: 'Progress' }]}
        />
        <LoadingState message="Calculating your factual grounding rates and learning activity..." />
      </div>
    );
  }

  if (error || !progress) {
    return (
      <div className="space-y-6 max-w-6xl">
        <PageHeader
          title="Learning Progress"
          description="Personal learning analytics, concept grounding rates, and curriculum mastery."
          breadcrumbs={[{ label: 'Student', path: '/student/dashboard' }, { label: 'Progress' }]}
        />
        <Card className="p-6 text-center text-red-600 border-red-200 bg-red-50/50">
          <p className="text-sm font-medium">{error || 'Unable to load progress data.'}</p>
          <Button variant="outline" size="sm" className="mt-3" onClick={loadProgress}>
            Retry
          </Button>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-6xl">
      <PageHeader
        title="Learning Progress & Grounding Mastery"
        description="Monitor your factual question inquiries, evidence grounding scores, and curriculum study progress."
        breadcrumbs={[{ label: 'Student', path: '/student/dashboard' }, { label: 'Progress' }]}
        badge={<Badge variant="success">Personal Mastery</Badge>}
        actions={
          <Button
            variant="outline"
            size="sm"
            onClick={loadProgress}
            leftIcon={<RefreshCw className="w-4 h-4" />}
          >
            Refresh Progress
          </Button>
        }
      />

      {/* KPI Ribbon */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="border border-slate-200">
          <CardContent className="p-4">
            <div className="text-xs font-medium text-slate-500 flex items-center gap-1">
              <HelpCircle className="w-3.5 h-3.5 text-blue-600" />
              Questions Asked
            </div>
            <div className="text-2xl font-bold text-slate-900 mt-1">
              {progress.total_queries}
            </div>
            <div className="text-[11px] text-slate-500 mt-0.5">Total AI tutor inquiries</div>
          </CardContent>
        </Card>

        <Card className="border border-slate-200">
          <CardContent className="p-4">
            <div className="text-xs font-medium text-slate-500 flex items-center gap-1">
              <BookOpen className="w-3.5 h-3.5 text-purple-600" />
              Enrolled Courses
            </div>
            <div className="text-2xl font-bold text-purple-700 mt-1">
              {progress.enrolled_courses_count}
            </div>
            <div className="text-[11px] text-slate-500 mt-0.5">Active curricula</div>
          </CardContent>
        </Card>

        <Card className="border border-slate-200">
          <CardContent className="p-4">
            <div className="text-xs font-medium text-slate-500 flex items-center gap-1">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
              Avg Grounding Score
            </div>
            <div className="text-2xl font-bold text-emerald-700 mt-1">
              {Math.round(progress.avg_support_score * 100)}%
            </div>
            <div className="text-[11px] text-slate-500 mt-0.5">Factual evidence support</div>
          </CardContent>
        </Card>

        <Card className="border border-slate-200">
          <CardContent className="p-4">
            <div className="text-xs font-medium text-slate-500 flex items-center gap-1">
              <TrendingUp className="w-3.5 h-3.5 text-amber-600" />
              Verified Rate
            </div>
            <div className="text-2xl font-bold text-amber-700 mt-1">
              {progress.verified_rate_pct.toFixed(1)}%
            </div>
            <div className="text-[11px] text-slate-500 mt-0.5">Zero hallucination answers</div>
          </CardContent>
        </Card>
      </div>

      {progress.total_queries === 0 ? (
        <EmptyState
          icon={<MessageSquare className="w-8 h-8 text-blue-500" />}
          title="Start Your Learning Journey"
          description="You haven't asked any questions to the AI Tutor yet. Explore course materials and consult the tutor to track your grounded concept mastery here."
          action={
            <Link to="/student/tutor">
              <Button variant="primary" size="sm" rightIcon={<ArrowRight className="w-4 h-4" />}>
                Open AI Tutor Workspace
              </Button>
            </Link>
          }
        />
      ) : (
        <div className="space-y-6">
          {/* Distributions */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Decision breakdown */}
            <Card className="border border-slate-200">
              <div className="p-4 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
                <span className="text-xs font-bold text-slate-800">
                  Answer Verification Accuracy
                </span>
                <Badge variant="success" size="sm">
                  Agentic Check
                </Badge>
              </div>
              <CardContent className="p-5 space-y-3">
                {Object.entries(progress.decisions_breakdown).map(([decision, count]) => {
                  const pct = progress.total_queries > 0
                    ? Math.round((count / progress.total_queries) * 100)
                    : 0;
                  const isClean = ['VERIFIED', 'ACCEPT'].includes(decision.toUpperCase());

                  return (
                    <div key={decision} className="space-y-1">
                      <div className="flex items-center justify-between text-xs">
                        <span className="font-semibold text-slate-700">{decision}</span>
                        <span className="text-slate-500">
                          {count} ({pct}%)
                        </span>
                      </div>
                      <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
                        <div
                          className={`h-2 rounded-full ${
                            isClean ? 'bg-emerald-500' : 'bg-amber-500'
                          }`}
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </CardContent>
            </Card>

            {/* Confidence breakdown */}
            <Card className="border border-slate-200">
              <div className="p-4 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
                <span className="text-xs font-bold text-slate-800">
                  Answer Confidence Levels
                </span>
                <Badge variant="purple" size="sm">
                  Evidence Depth
                </Badge>
              </div>
              <CardContent className="p-5 space-y-3">
                {Object.entries(progress.confidence_breakdown).map(([level, count]) => {
                  const pct = progress.total_queries > 0
                    ? Math.round((count / progress.total_queries) * 100)
                    : 0;
                  const barColor =
                    level.toUpperCase() === 'HIGH'
                      ? 'bg-blue-600'
                      : level.toUpperCase() === 'MEDIUM'
                      ? 'bg-amber-500'
                      : 'bg-rose-500';

                  return (
                    <div key={level} className="space-y-1">
                      <div className="flex items-center justify-between text-xs">
                        <span className="font-semibold text-slate-700">{level} Confidence</span>
                        <span className="text-slate-500">
                          {count} ({pct}%)
                        </span>
                      </div>
                      <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
                        <div
                          className={`h-2 rounded-full ${barColor}`}
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </CardContent>
            </Card>
          </div>

          {/* Course-by-course study breakdown */}
          <Card className="border border-slate-200">
            <div className="p-4 border-b border-slate-200 flex items-center justify-between">
              <span className="text-xs font-bold text-slate-800">
                Study Progress by Enrolled Course
              </span>
              <Badge variant="primary" size="sm">
                Curriculum Mastery
              </Badge>
            </div>
            <div className="p-5 space-y-4">
              {progress.course_progress.map((cp) => {
                const supportPct = Math.round(cp.avg_support_score * 100);
                return (
                  <div
                    key={cp.course_id}
                    className="p-4 bg-slate-50 rounded-xl border border-slate-200/80 space-y-3"
                  >
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-mono font-bold text-blue-700 text-xs">
                            {cp.course_code}
                          </span>
                          <span className="text-sm font-semibold text-slate-800">{cp.title}</span>
                        </div>
                        <div className="text-xs text-slate-500 mt-0.5">
                          {cp.queries_count} questions explored with AI Tutor
                        </div>
                      </div>

                      <div className="flex items-center gap-3">
                        <div className="text-right">
                          <div className="text-xs font-bold text-slate-800">{supportPct}%</div>
                          <div className="text-[10px] text-slate-500">Grounding</div>
                        </div>
                        <Link to="/student/tutor">
                          <Button variant="outline" size="sm" rightIcon={<ArrowRight className="w-3.5 h-3.5" />}>
                            Study
                          </Button>
                        </Link>
                      </div>
                    </div>

                    <div className="w-full bg-slate-200 rounded-full h-2 overflow-hidden">
                      <div
                        className="bg-emerald-500 h-2 rounded-full"
                        style={{ width: `${supportPct}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </Card>

          {/* Recent Activity Timeline */}
          <Card className="border border-slate-200">
            <div className="p-4 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
              <div className="flex items-center gap-1.5 text-xs font-bold text-slate-800">
                <Clock className="w-4 h-4 text-blue-600" />
                Recent Question Activity
              </div>
              <Link to="/student/history" className="text-xs font-semibold text-blue-600 hover:text-blue-800">
                View All History &rarr;
              </Link>
            </div>
            <div className="divide-y divide-slate-100">
              {progress.recent_activity.map((act, idx) => (
                <div key={idx} className="p-4 hover:bg-slate-50/60 transition-colors flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
                  <div className="space-y-1 max-w-xl">
                    <div className="flex items-center gap-2">
                      {act.course_code && (
                        <Badge variant="primary" size="sm">
                          {act.course_code}
                        </Badge>
                      )}
                      {renderDecisionBadge(act.verification_decision)}
                      <span className="text-xs font-semibold text-slate-700">
                        {Math.round(act.support_score * 100)}% Grounded
                      </span>
                    </div>
                    <p className="text-xs font-medium text-slate-800">{act.user_query}</p>
                  </div>
                  <div className="text-xs text-slate-400 shrink-0">
                    {act.timestamp}
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </div>
      )}
    </div>
  );
};

export default StudentProgressPage;
