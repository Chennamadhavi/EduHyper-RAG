import React, { useEffect, useState } from 'react';
import {
  Bot,
  Send,
  ShieldCheck,
  Sparkles,
  BookOpen,
  FileText,
  AlertCircle,
  ChevronDown,
  ChevronUp,
  Layers,
  HelpCircle,
  ExternalLink,
  RotateCcw,
  CheckCircle2,
  AlertTriangle,
  XCircle,
} from 'lucide-react';
import { Link } from 'react-router-dom';
import PageHeader from '../../components/common/PageHeader';
import Card, { CardContent } from '../../components/common/Card';
import Button from '../../components/common/Button';
import Badge from '../../components/common/Badge';
import LoadingState from '../../components/common/LoadingState';
import courseService from '../../services/courseService';
import documentService from '../../services/documentService';
import tutorService from '../../services/tutorService';
import { Course } from '../../types/course';
import { DocumentItem } from '../../types/document';
import { ChunkDetail, TutorQueryResponse } from '../../types/tutor';

interface ChatMessage {
  id: string;
  sender: 'user' | 'tutor';
  text: string;
  timestamp: string;
  tutorResponse?: TutorQueryResponse;
}

export const StudentTutorPage: React.FC = () => {
  // State for selections
  const [courses, setCourses] = useState<Course[]>([]);
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [selectedCourseId, setSelectedCourseId] = useState<number | null>(null);
  const [selectedDocId, setSelectedDocId] = useState<string>('');
  const [sampleQuestions, setSampleQuestions] = useState<string[]>([]);

  // State for interaction
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [query, setQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isInitializing, setIsInitializing] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Expanded chunk accordion states
  const [expandedChunks, setExpandedChunks] = useState<Record<string, boolean>>({});

  useEffect(() => {
    loadInitialData();
  }, []);

  useEffect(() => {
    if (selectedCourseId) {
      loadDocuments(selectedCourseId);
    } else {
      setDocuments([]);
      setSelectedDocId('');
    }
  }, [selectedCourseId]);

  const loadInitialData = async () => {
    setIsInitializing(true);
    try {
      const [fetchedCourses, fetchedSamples] = await Promise.all([
        courseService.listCourses(),
        tutorService.getSampleQuestions().catch(() => []),
      ]);
      setCourses(fetchedCourses);
      setSampleQuestions(fetchedSamples);

      if (fetchedCourses.length > 0) {
        setSelectedCourseId(fetchedCourses[0].id);
      }
    } catch (err: any) {
      setError('Failed to load courses. Please make sure you are enrolled in at least one course.');
    } finally {
      setIsInitializing(false);
    }
  };

  const loadDocuments = async (courseId: number) => {
    try {
      const docs = await documentService.listDocuments(courseId);
      const readyDocs = docs.filter((d) => d.status === 'READY');
      setDocuments(readyDocs);
      if (readyDocs.length > 0) {
        setSelectedDocId(readyDocs[0].doc_id);
      } else {
        setSelectedDocId('');
      }
    } catch {
      setDocuments([]);
      setSelectedDocId('');
    }
  };

  const handleAsk = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    const trimmed = query.trim();
    if (!trimmed || !selectedDocId || !selectedCourseId || isLoading) return;

    setError(null);
    const userMsgId = `user-${Date.now()}`;
    const newMessages: ChatMessage[] = [
      ...messages,
      {
        id: userMsgId,
        sender: 'user',
        text: trimmed,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      },
    ];
    setMessages(newMessages);
    setQuery('');
    setIsLoading(true);

    try {
      const response = await tutorService.askTutor({
        query: trimmed,
        doc_id: selectedDocId,
        course_id: selectedCourseId,
        max_iterations: 2,
        min_support_score: 0.7,
      });

      const tutorMsgId = `tutor-${Date.now()}`;
      setMessages([
        ...newMessages,
        {
          id: tutorMsgId,
          sender: 'tutor',
          text: response.answer,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          tutorResponse: response,
        },
      ]);
    } catch (err: any) {
      const errMsg = err?.response?.data?.detail || 'An error occurred while consulting the AI Tutor.';
      setError(errMsg);
    } finally {
      setIsLoading(false);
    }
  };

  const toggleChunkExpand = (messageId: string, chunkId: string) => {
    const key = `${messageId}-${chunkId}`;
    setExpandedChunks((prev) => ({
      ...prev,
      [key]: !prev[key],
    }));
  };

  const renderVerificationBadge = (decision: string) => {
    switch (decision?.toUpperCase()) {
      case 'VERIFIED':
        return (
          <Badge variant="success" size="sm" className="font-semibold">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
            VERIFIED
          </Badge>
        );
      case 'PARTIALLY_SUPPORTED':
        return (
          <Badge variant="warning" size="sm" className="font-semibold">
            <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
            PARTIALLY SUPPORTED
          </Badge>
        );
      case 'UNSUPPORTED':
        return (
          <Badge variant="danger" size="sm" className="font-semibold">
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

  if (isInitializing) {
    return (
      <div className="space-y-6 max-w-5xl">
        <PageHeader
          title="AI Tutor Workspace"
          description="Ask complex educational questions and receive grounded, hallucination-verified answers."
          breadcrumbs={[{ label: 'Student', path: '/student/dashboard' }, { label: 'AI Tutor' }]}
        />
        <LoadingState message="Loading your enrolled courses and verified knowledge base..." />
      </div>
    );
  }

  if (courses.length === 0) {
    return (
      <div className="space-y-6 max-w-4xl">
        <PageHeader
          title="AI Tutor Workspace"
          description="Ask complex educational questions and receive grounded, hallucination-verified answers."
          breadcrumbs={[{ label: 'Student', path: '/student/dashboard' }, { label: 'AI Tutor' }]}
        />
        <Card className="text-center p-8 border-slate-200">
          <BookOpen className="w-12 h-12 text-blue-500 mx-auto mb-3 opacity-80" />
          <h3 className="text-lg font-bold text-slate-800 mb-1">No Courses Found</h3>
          <p className="text-sm text-slate-600 max-w-md mx-auto mb-6">
            You need to be enrolled in at least one course with uploaded documents before starting a tutoring session.
          </p>
          <Link to="/student/courses">
            <Button variant="primary" rightIcon={<ExternalLink className="w-4 h-4" />}>
              Explore Course Catalog
            </Button>
          </Link>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-5xl">
      <PageHeader
        title="AI Tutor Workspace"
        description="Ask complex educational questions and receive grounded, hallucination-verified answers."
        breadcrumbs={[{ label: 'Student', path: '/student/dashboard' }, { label: 'AI Tutor' }]}
        badge={<Badge variant="primary">Agentic Verification</Badge>}
      />

      {/* Control Panel: Course & Document Selection */}
      <Card className="border border-slate-200 bg-white">
        <div className="p-4 grid grid-cols-1 md:grid-cols-2 gap-4 items-center">
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1 flex items-center gap-1.5">
              <BookOpen className="w-3.5 h-3.5 text-blue-600" />
              Target Course
            </label>
            <select
              value={selectedCourseId || ''}
              onChange={(e) => setSelectedCourseId(Number(e.target.value))}
              className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-sm text-slate-800 font-medium focus:ring-2 focus:ring-blue-500 focus:outline-none"
            >
              {courses.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.course_code}: {c.title}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1 flex items-center gap-1.5">
              <FileText className="w-3.5 h-3.5 text-blue-600" />
              Grounded Document Source
            </label>
            <select
              value={selectedDocId}
              onChange={(e) => setSelectedDocId(e.target.value)}
              disabled={documents.length === 0}
              className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-sm text-slate-800 font-medium focus:ring-2 focus:ring-blue-500 focus:outline-none disabled:bg-slate-100 disabled:text-slate-400"
            >
              {documents.length === 0 ? (
                <option value="">No ready documents for this course</option>
              ) : (
                documents.map((d) => (
                  <option key={d.doc_id} value={d.doc_id}>
                    {d.filename} ({d.num_chunks} chunks, {d.num_hyperedges} hyperedges)
                  </option>
                ))
              )}
            </select>
          </div>
        </div>
      </Card>

      {/* Sample Questions Shelf */}
      {sampleQuestions.length > 0 && (
        <div className="p-3 bg-blue-50/50 border border-blue-100 rounded-xl space-y-2">
          <div className="flex items-center gap-1.5 text-xs font-semibold text-blue-900">
            <Sparkles className="w-3.5 h-3.5 text-blue-600" />
            Curated Sample Questions:
          </div>
          <div className="flex flex-wrap gap-1.5">
            {sampleQuestions.map((sq, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => setQuery(sq)}
                className="text-left text-xs bg-white hover:bg-blue-50 border border-blue-200 text-slate-700 hover:text-blue-800 px-2.5 py-1.5 rounded-lg transition-colors shadow-xs"
              >
                {sq}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Chat Workspace */}
      <Card className="border border-slate-200">
        <div className="p-4 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg bg-blue-600 text-white flex items-center justify-center">
              <Bot className="w-4 h-4" />
            </div>
            <div>
              <div className="text-xs font-bold text-slate-800">EduHyper-RAG Multi-Agent Tutor</div>
              <div className="text-[10px] text-slate-500">
                Phase 4–8 Verified Answers • Zero Unverified Claims
              </div>
            </div>
          </div>
          {messages.length > 0 && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => setMessages([])}
              leftIcon={<RotateCcw className="w-3.5 h-3.5" />}
            >
              Clear Session
            </Button>
          )}
        </div>

        <CardContent className="p-6 space-y-6 min-h-[380px] flex flex-col justify-between">
          {/* Messages Container */}
          <div className="space-y-6 overflow-y-auto">
            {messages.length === 0 && (
              <div className="p-4 rounded-xl bg-blue-50/60 border border-blue-200 text-sm text-blue-900 max-w-xl">
                <p className="font-semibold mb-1 flex items-center gap-1.5">
                  <Sparkles className="w-4 h-4 text-blue-600" /> Welcome to your AI Tutor!
                </p>
                <p className="text-xs text-blue-700 leading-relaxed mb-2">
                  Select a document from your course above, pick a sample prompt or ask any question. The tutor uses
                  high-order hypergraph relationships and agentic verification to prove every answer factually.
                </p>
                <p className="text-[11px] text-blue-600 font-medium">
                  • Phase 4: Hybrid Semantic & Hypergraph Retrieval
                  <br />• Phase 5: LangGraph Verification Iterations
                  <br />• Phase 6: Grounded Educational Answer Synthesis
                  <br />• Phase 7: Line-by-Line Claim Verification & Hallucination Checking
                  <br />• Phase 8: Explanatory Evidence Citations
                </p>
              </div>
            )}

            {messages.map((msg) => (
              <div key={msg.id} className="space-y-3">
                {/* User Message */}
                {msg.sender === 'user' ? (
                  <div className="flex justify-end">
                    <div className="bg-blue-600 text-white rounded-2xl rounded-tr-xs px-4 py-3 max-w-xl text-sm shadow-xs">
                      <p className="font-normal leading-relaxed">{msg.text}</p>
                      <span className="block text-[10px] text-blue-200 text-right mt-1.5">
                        {msg.timestamp}
                      </span>
                    </div>
                  </div>
                ) : (
                  /* Tutor Message with Full Verification & Explainability Card */
                  <div className="flex justify-start">
                    <div className="bg-slate-50 border border-slate-200 rounded-2xl rounded-tl-xs p-5 max-w-3xl space-y-4 shadow-xs">
                      {/* Header with Verification Status */}
                      <div className="flex flex-wrap items-center justify-between gap-2 pb-3 border-b border-slate-200/80">
                        <div className="flex items-center gap-2">
                          <Bot className="w-4 h-4 text-blue-600" />
                          <span className="text-xs font-bold text-slate-800">Verified Answer</span>
                          {msg.tutorResponse && renderVerificationBadge(msg.tutorResponse.verification_decision)}
                        </div>

                        {msg.tutorResponse && (
                          <div className="flex items-center gap-2 text-xs">
                            <span className="text-slate-500 text-[11px]">Grounded:</span>
                            <div className="w-20 bg-slate-200 rounded-full h-2 overflow-hidden">
                              <div
                                className="bg-emerald-500 h-2 rounded-full"
                                style={{ width: `${Math.round(msg.tutorResponse.support_score * 100)}%` }}
                              />
                            </div>
                            <span className="font-semibold text-slate-700 text-[11px]">
                              {Math.round(msg.tutorResponse.support_score * 100)}%
                            </span>
                            <Badge variant="purple" size="sm">
                              {msg.tutorResponse.confidence_level} Confidence
                            </Badge>
                          </div>
                        )}
                      </div>

                      {/* Answer Body */}
                      <div className="text-sm text-slate-800 leading-relaxed whitespace-pre-line font-normal">
                        {msg.text}
                      </div>

                      {/* Verification Reasoning */}
                      {msg.tutorResponse?.verification_reasoning && (
                        <div className="p-3 bg-white rounded-lg border border-slate-200 text-xs text-slate-600">
                          <div className="font-semibold text-slate-700 mb-1 flex items-center gap-1">
                            <ShieldCheck className="w-3.5 h-3.5 text-blue-600" />
                            Verification Audit Trail:
                          </div>
                          <p>{msg.tutorResponse.verification_reasoning}</p>
                        </div>
                      )}

                      {/* Retrieved Concepts & Hyperedges Tags */}
                      {msg.tutorResponse?.retrieved_concepts && msg.tutorResponse.retrieved_concepts.length > 0 && (
                        <div className="pt-2 border-t border-slate-200/60">
                          <div className="text-[11px] font-semibold text-slate-500 mb-1.5 flex items-center gap-1">
                            <Layers className="w-3 h-3 text-purple-600" />
                            Supporting Hypergraph Concepts:
                          </div>
                          <div className="flex flex-wrap gap-1.5">
                            {msg.tutorResponse.retrieved_concepts.map((concept, cIdx) => (
                              <span
                                key={cIdx}
                                className="text-[11px] bg-purple-50 text-purple-700 border border-purple-200 px-2 py-0.5 rounded-md font-medium"
                              >
                                #{concept}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Evidence Citations / Chunks Accordion */}
                      {msg.tutorResponse?.retrieved_chunk_details && msg.tutorResponse.retrieved_chunk_details.length > 0 && (
                        <div className="pt-2 border-t border-slate-200/60">
                          <div className="text-[11px] font-semibold text-slate-500 mb-2 flex items-center gap-1">
                            <FileText className="w-3 h-3 text-blue-600" />
                            Supporting Textbook Citations ({msg.tutorResponse.retrieved_chunk_details.length}):
                          </div>
                          <div className="space-y-2">
                            {msg.tutorResponse.retrieved_chunk_details.map((chunk: ChunkDetail, chIdx: number) => {
                              const isExp = expandedChunks[`${msg.id}-${chunk.chunk_id || chIdx}`];
                              return (
                                <div
                                  key={chIdx}
                                  className="bg-white border border-slate-200 rounded-lg p-2.5 text-xs transition-colors"
                                >
                                  <div
                                    className="flex items-center justify-between cursor-pointer select-none"
                                    onClick={() => toggleChunkExpand(msg.id, chunk.chunk_id || String(chIdx))}
                                  >
                                    <div className="flex items-center gap-2">
                                      <span className="font-semibold text-blue-700">
                                        Source [{chunk.chunk_id || chIdx + 1}]
                                      </span>
                                      {chunk.page && (
                                        <span className="text-slate-400 text-[10px]">p. {chunk.page}</span>
                                      )}
                                      <Badge variant="default" size="sm">
                                        Sim: {chunk.score.toFixed(3)}
                                      </Badge>
                                    </div>
                                    <button
                                      type="button"
                                      className="text-slate-400 hover:text-slate-600"
                                    >
                                      {isExp ? (
                                        <ChevronUp className="w-4 h-4" />
                                      ) : (
                                        <ChevronDown className="w-4 h-4" />
                                      )}
                                    </button>
                                  </div>
                                  {isExp && (
                                    <p className="mt-2 text-slate-700 text-[11px] leading-relaxed border-t border-slate-100 pt-2 font-mono bg-slate-50 p-2 rounded">
                                      {chunk.content}
                                    </p>
                                  )}
                                </div>
                              );
                            })}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            ))}

            {/* In-Flight Pipeline Loading State */}
            {isLoading && (
              <div className="flex justify-start">
                <div className="bg-slate-50 border border-slate-200 rounded-2xl rounded-tl-xs p-5 max-w-md space-y-3">
                  <div className="flex items-center gap-2">
                    <div className="w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
                    <span className="text-xs font-bold text-slate-800">
                      Executing Multi-Phase Pipeline...
                    </span>
                  </div>
                  <div className="space-y-1 text-[11px] text-slate-600">
                    <p>• Phase 4: Hybrid semantic & hypergraph retrieval</p>
                    <p>• Phase 5: Multi-hop LangGraph state verification</p>
                    <p>• Phase 6: Grounded answer generation</p>
                    <p>• Phase 7: Line-by-line claim hallucination checking</p>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Error Message */}
          {error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-xs text-red-700 flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-red-500 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Input Form */}
          <form onSubmit={handleAsk} className="pt-4 border-t border-slate-100">
            <div className="flex items-center gap-2">
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder={
                  documents.length > 0
                    ? 'Ask an educational question about this document...'
                    : 'Select a course document to enable tutoring...'
                }
                disabled={documents.length === 0 || isLoading}
                className="flex-1 bg-slate-50 border border-slate-200 rounded-lg px-4 py-2.5 text-sm text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-slate-100 disabled:text-slate-400"
              />
              <Button
                type="submit"
                variant="primary"
                disabled={!query.trim() || documents.length === 0 || isLoading}
                isLoading={isLoading}
                rightIcon={!isLoading ? <Send className="w-4 h-4" /> : undefined}
              >
                Ask Tutor
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
};

export default StudentTutorPage;
