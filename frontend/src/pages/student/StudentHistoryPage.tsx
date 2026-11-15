import React, { useEffect, useState } from 'react';
import {
  History,
  Search,
  BookOpen,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  ShieldCheck,
  ChevronDown,
  ChevronUp,
  MessageSquare,
  ArrowRight,
} from 'lucide-react';
import { Link } from 'react-router-dom';
import PageHeader from '../../components/common/PageHeader';
import Card, { CardContent } from '../../components/common/Card';
import Button from '../../components/common/Button';
import Badge from '../../components/common/Badge';
import LoadingState from '../../components/common/LoadingState';
import EmptyState from '../../components/common/EmptyState';
import tutorService from '../../services/tutorService';
import { QAHistoryItem } from '../../types/tutor';

export const StudentHistoryPage: React.FC = () => {
  const [history, setHistory] = useState<QAHistoryItem[]>([]);
  const [filteredHistory, setFilteredHistory] = useState<QAHistoryItem[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedItems, setExpandedItems] = useState<Record<number, boolean>>({});

  useEffect(() => {
    loadHistory();
  }, []);

  useEffect(() => {
    if (!searchTerm.trim()) {
      setFilteredHistory(history);
    } else {
      const q = searchTerm.toLowerCase();
      setFilteredHistory(
        history.filter(
          (item) =>
            item.user_query.toLowerCase().includes(q) ||
            item.generated_answer.toLowerCase().includes(q) ||
            item.course_code?.toLowerCase().includes(q) ||
            item.filename?.toLowerCase().includes(q)
        )
      );
    }
  }, [searchTerm, history]);

  const loadHistory = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await tutorService.getHistory();
      setHistory(data);
      setFilteredHistory(data);
    } catch (err: any) {
      setError('Failed to load question history. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const toggleExpand = (id: number) => {
    setExpandedItems((prev) => ({
      ...prev,
      [id]: !prev[id],
    }));
  };

  const renderVerificationBadge = (decision?: string) => {
    switch (decision?.toUpperCase()) {
      case 'VERIFIED':
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
      case 'UNSUPPORTED':
        return (
          <Badge variant="danger" size="sm">
            <XCircle className="w-3.5 h-3.5 text-red-600" />
            UNSUPPORTED
          </Badge>
        );
      default:
        return (
          <Badge variant="purple" size="sm">
            <ShieldCheck className="w-3.5 h-3.5 text-purple-600" />
            {decision || 'CHECKED'}
          </Badge>
        );
    }
  };

  return (
    <div className="space-y-6 max-w-5xl">
      <PageHeader
        title="Question History & Audit Trail"
        description="Review past interactions, grounded educational answers, and citation audit records."
        breadcrumbs={[{ label: 'Student', path: '/student/dashboard' }, { label: 'History' }]}
        badge={<Badge variant="default">{history.length} Questions</Badge>}
      />

      {/* Search and Filters */}
      <Card className="border border-slate-200 bg-white">
        <div className="p-4 flex flex-col sm:flex-row gap-3 items-center justify-between">
          <div className="relative w-full sm:w-96">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Filter by question, answer keywords, or course..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full bg-slate-50 border border-slate-200 rounded-lg pl-9 pr-3 py-2 text-sm text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <Link to="/student/tutor">
            <Button variant="primary" size="sm" rightIcon={<ArrowRight className="w-4 h-4" />}>
              Open AI Tutor
            </Button>
          </Link>
        </div>
      </Card>

      {/* Content Area */}
      {isLoading ? (
        <LoadingState message="Loading your question answering audit trail..." />
      ) : error ? (
        <Card className="p-6 text-center text-red-600 border-red-200 bg-red-50/50">
          <p className="text-sm font-medium">{error}</p>
          <Button variant="outline" size="sm" className="mt-3" onClick={loadHistory}>
            Retry
          </Button>
        </Card>
      ) : filteredHistory.length === 0 ? (
        <EmptyState
          icon={<History className="w-8 h-8 text-blue-500" />}
          title={searchTerm ? 'No matching questions found' : 'No Question History Yet'}
          description={
            searchTerm
              ? `No questions matched "${searchTerm}". Try a different search keyword.`
              : 'You have not asked any questions to the AI Tutor yet. Ask questions in the AI Tutor workspace to build your verified learning record.'
          }
          action={
            <Link to="/student/tutor">
              <Button variant="primary" size="sm" rightIcon={<MessageSquare className="w-4 h-4" />}>
                Ask a Question
              </Button>
            </Link>
          }
        />
      ) : (
        <div className="space-y-4">
          {filteredHistory.map((item) => {
            const isExp = expandedItems[item.id];
            const supportPercent = Math.round((item.support_score || 0) * 100);

            return (
              <Card key={item.id} className="border border-slate-200 hover:border-slate-300 transition-all">
                <CardContent className="p-5 space-y-4">
                  {/* Top Bar: Meta tags and verification */}
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      {item.course_code && (
                        <Badge variant="primary" size="sm">
                          <BookOpen className="w-3 h-3 text-blue-600" />
                          {item.course_code}
                        </Badge>
                      )}
                      {renderVerificationBadge(item.verification_decision)}
                      <Badge variant="purple" size="sm">
                        {item.confidence_level || 'Medium'} Confidence
                      </Badge>
                    </div>

                    <div className="flex items-center gap-3 text-xs text-slate-500">
                      <span>Grounded: <strong className="text-slate-800">{supportPercent}%</strong></span>
                      {item.created_at && (
                        <span>{new Date(item.created_at).toLocaleDateString()}</span>
                      )}
                    </div>
                  </div>

                  {/* Question */}
                  <div>
                    <h3 className="text-sm font-semibold text-slate-900 flex items-start gap-2">
                      <MessageSquare className="w-4 h-4 text-blue-600 shrink-0 mt-0.5" />
                      {item.user_query}
                    </h3>
                  </div>

                  {/* Answer Preview / Full */}
                  <div className="bg-slate-50 border border-slate-200/80 rounded-xl p-4 text-xs text-slate-700 leading-relaxed">
                    <div className={isExp ? 'whitespace-pre-line' : 'line-clamp-3'}>
                      {item.generated_answer}
                    </div>

                    {item.generated_answer.length > 200 && (
                      <button
                        type="button"
                        onClick={() => toggleExpand(item.id)}
                        className="mt-2 text-xs font-semibold text-blue-600 hover:text-blue-800 flex items-center gap-1 cursor-pointer select-none"
                      >
                        {isExp ? (
                          <>
                            <ChevronUp className="w-3.5 h-3.5" /> Show Less
                          </>
                        ) : (
                          <>
                            <ChevronDown className="w-3.5 h-3.5" /> Read Full Answer
                          </>
                        )}
                      </button>
                    )}
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default StudentHistoryPage;
