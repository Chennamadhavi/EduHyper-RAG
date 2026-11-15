import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  Network,
  Upload,
  BookOpen,
  ShieldCheck,
  Cpu,
  FileSearch,
  CheckCircle2,
  ArrowRight,
  Sparkles,
  Layers,
  GraduationCap,
  Users,
  Activity,
} from 'lucide-react';
import Button from '../components/common/Button';
import Card, { CardContent } from '../components/common/Card';
import Badge from '../components/common/Badge';
import { getBackendHealth } from '../services/api';
import { HealthResponse } from '../types/api';

export const LandingPage: React.FC = () => {
  const [backendHealth, setBackendHealth] = useState<HealthResponse | null>(null);
  const [checkingHealth, setCheckingHealth] = useState(true);

  useEffect(() => {
    getBackendHealth()
      .then((data) => setBackendHealth(data))
      .catch(() => setBackendHealth(null))
      .finally(() => setCheckingHealth(false));
  }, []);

  const features = [
    {
      icon: Upload,
      title: 'Educational PDF Ingestion',
      description:
        'Teachers upload textbooks and lecture materials. The pipeline cleans text and extracts multi-tiered semantic chunks.',
      badge: 'Phase 1',
    },
    {
      icon: Network,
      title: 'Hypergraph-Driven Retrieval',
      description:
        'Unlike pairwise graphs, HyperNetX hyperedges capture complex interactions connecting three or more educational concepts simultaneously.',
      badge: 'Phase 3 & 4',
    },
    {
      icon: BookOpen,
      title: 'Evidence-Based Answers',
      description:
        'Answers are synthesized strictly from retrieved course chunks with verifiable entity hyperpaths and source context.',
      badge: 'Phase 6',
    },
    {
      icon: Cpu,
      title: 'Agentic Verification',
      description:
        'A LangGraph state graph agent iteratively validates evidence sufficiency and triggers targeted retrieval when context is incomplete.',
      badge: 'Phase 5',
    },
    {
      icon: ShieldCheck,
      title: 'Hallucination Detection',
      description:
        'Decomposes generated answers into atomic claims to detect and flag unsubstantiated statements before student delivery.',
      badge: 'Phase 7',
    },
    {
      icon: FileSearch,
      title: 'Source Explainability',
      description:
        'Provides interactive transparency showing retrieved hyperedges, similarity scores, and verification reasoning for every query.',
      badge: 'Phase 8',
    },
  ];

  const workflowSteps = [
    {
      step: '01',
      title: 'Document Processing',
      description: 'Course PDFs are ingested, normalized, and partitioned into dual semantic and structural chunks.',
    },
    {
      step: '02',
      title: 'Hypergraph Modeling',
      description: 'Named entities and higher-order relations (≥3 entities) form an educational knowledge hypergraph.',
    },
    {
      step: '03',
      title: 'Hybrid Retrieval & Verification',
      description: 'Semantic vector search combines with hypergraph traversal; LangGraph agents verify evidence completeness.',
    },
    {
      step: '04',
      title: 'Grounded Tutoring',
      description: 'Verified educational explanations are generated with line-by-line claim citations and zero hallucinations.',
    },
  ];

  return (
    <div className="space-y-20 pb-16">
      {/* Hero Section */}
      <section className="relative pt-12 pb-8 sm:pt-20 sm:pb-16 overflow-hidden">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center relative z-10">
          {/* Top Pill / Status Indicator */}
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-blue-50 border border-blue-200 text-xs font-medium text-blue-700 mb-6 shadow-xs">
            <Sparkles className="w-3.5 h-3.5 text-blue-600" />
            <span>Enhanced Hyper-RAG with Agentic Verification</span>
            <span className="w-1 h-1 rounded-full bg-blue-400" />
            <span className="text-slate-600">
              {checkingHealth
                ? 'Connecting backend...'
                : backendHealth
                ? 'FastAPI Backend Online'
                : 'Standalone Frontend Mode'}
            </span>
          </div>

          {/* Main Hero Title */}
          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold text-slate-900 tracking-tight max-w-4xl mx-auto leading-tight sm:leading-tight">
            Your Personalized <span className="text-blue-600">AI Tutor</span>
          </h1>

          {/* Subtitle */}
          <p className="mt-5 text-base sm:text-lg text-slate-600 max-w-2xl mx-auto leading-relaxed">
            EduHyper-RAG bridges high-order educational concepts using hypergraph-driven retrieval
            and multi-agent verification — delivering strictly grounded answers with verifiable
            evidence and reduced hallucinations.
          </p>

          {/* Action Buttons */}
          <div className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-3">
            <Link to="/register">
              <Button size="lg" rightIcon={<ArrowRight className="w-4 h-4" />}>
                Get Started
              </Button>
            </Link>
            <a href="#features">
              <Button variant="secondary" size="lg">
                Explore Features
              </Button>
            </a>
          </div>

          {/* Backend Status Card (Subtle & Non-blocking) */}
          {backendHealth && (
            <div className="mt-8 max-w-lg mx-auto p-3 rounded-lg bg-emerald-50/70 border border-emerald-200 text-xs text-emerald-800 flex items-center justify-center gap-2">
              <Activity className="w-4 h-4 text-emerald-600 shrink-0" />
              <span>
                Connected to <strong>{backendHealth.app_name}</strong> ({backendHealth.version}) in{' '}
                <span className="capitalize">{backendHealth.environment}</span> mode.
              </span>
            </div>
          )}

          {/* Visual Architecture Representation */}
          <div className="mt-14 max-w-4xl mx-auto">
            <div className="rounded-2xl border border-slate-200 bg-white p-6 sm:p-8 shadow-sm">
              <div className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-6">
                System Knowledge & Verification Flow
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
                <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 text-left">
                  <div className="w-8 h-8 rounded-lg bg-blue-100 text-blue-700 flex items-center justify-center font-bold text-xs mb-3">
                    01
                  </div>
                  <h4 className="text-sm font-semibold text-slate-800 mb-1">Dual Ingestion</h4>
                  <p className="text-xs text-slate-500">PDF text extraction, semantic & fixed chunking</p>
                </div>
                <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 text-left">
                  <div className="w-8 h-8 rounded-lg bg-purple-100 text-purple-700 flex items-center justify-center font-bold text-xs mb-3">
                    02
                  </div>
                  <h4 className="text-sm font-semibold text-slate-800 mb-1">HyperNetX Graph</h4>
                  <p className="text-xs text-slate-500">Multi-concept hyperedges capturing joint relations</p>
                </div>
                <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 text-left">
                  <div className="w-8 h-8 rounded-lg bg-indigo-100 text-indigo-700 flex items-center justify-center font-bold text-xs mb-3">
                    03
                  </div>
                  <h4 className="text-sm font-semibold text-slate-800 mb-1">LangGraph Agent</h4>
                  <p className="text-xs text-slate-500">Evidence verification & sufficiency evaluation</p>
                </div>
                <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 text-left">
                  <div className="w-8 h-8 rounded-lg bg-emerald-100 text-emerald-700 flex items-center justify-center font-bold text-xs mb-3">
                    04
                  </div>
                  <h4 className="text-sm font-semibold text-slate-800 mb-1">Grounded Output</h4>
                  <p className="text-xs text-slate-500">Verified claims with traceable citations</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Feature Section */}
      <section id="features" className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 scroll-mt-20">
        <div className="text-center max-w-3xl mx-auto mb-12">
          <Badge variant="primary" className="mb-3">
            Core Capabilities
          </Badge>
          <h2 className="text-2xl sm:text-3xl font-bold text-slate-900 tracking-tight">
            Engineered for Reliable Educational QA
          </h2>
          <p className="mt-3 text-sm sm:text-base text-slate-600">
            Standard RAG systems hallucinate when educational concepts require multi-step reasoning.
            EduHyper-RAG is purpose-built to address this limitation.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((feature, idx) => {
            const Icon = feature.icon;
            return (
              <Card key={idx} hover className="border border-slate-200/90 flex flex-col justify-between">
                <CardContent className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div className="w-10 h-10 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center">
                      <Icon className="w-5 h-5" />
                    </div>
                    <Badge variant="default" size="sm">
                      {feature.badge}
                    </Badge>
                  </div>
                  <div>
                    <h3 className="text-base font-semibold text-slate-900 mb-1.5">{feature.title}</h3>
                    <p className="text-sm text-slate-600 leading-relaxed">{feature.description}</p>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      </section>

      {/* How It Works Section */}
      <section id="how-it-works" className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 scroll-mt-20">
        <div className="rounded-3xl bg-slate-900 text-white p-8 sm:p-12 lg:p-16">
          <div className="text-center max-w-2xl mx-auto mb-12">
            <span className="text-xs uppercase font-semibold tracking-wider text-blue-400">
              System Workflow
            </span>
            <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-white mt-2">
              How EduHyper-RAG Works
            </h2>
            <p className="mt-3 text-sm text-slate-400">
              A comprehensive 4-stage processing and verification loop designed to prevent knowledge omissions.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {workflowSteps.map((step, idx) => (
              <div key={idx} className="relative">
                <div className="text-4xl font-black text-slate-800 mb-3 select-none">{step.step}</div>
                <h3 className="text-base font-semibold text-white mb-2">{step.title}</h3>
                <p className="text-sm text-slate-400 leading-relaxed">{step.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Role Navigation Portal Preview */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-2xl mx-auto mb-10">
          <h2 className="text-2xl font-bold text-slate-900 tracking-tight">Dedicated User Portals</h2>
          <p className="mt-2 text-sm text-slate-600">
            Explore the role-tailored dashboards and management views available in EduHyper-RAG.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-4xl mx-auto">
          {/* Teacher Card */}
          <Card hover className="p-6 text-left border-l-4 border-l-blue-600">
            <div className="flex items-center gap-3 mb-3">
              <div className="w-10 h-10 rounded-lg bg-blue-100 text-blue-700 flex items-center justify-center">
                <Users className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-base font-bold text-slate-900">Teacher Dashboard</h3>
                <p className="text-xs text-slate-500">Course & document curriculum administration</p>
              </div>
            </div>
            <p className="text-sm text-slate-600 mb-6">
              Upload textbook PDFs, inspect generated hypergraph representations, manage enrolled students, and review student query analytics.
            </p>
            <Link to="/teacher/dashboard">
              <Button variant="outline" size="sm" className="w-full">
                Enter Teacher Portal
              </Button>
            </Link>
          </Card>

          {/* Student Card */}
          <Card hover className="p-6 text-left border-l-4 border-l-purple-600">
            <div className="flex items-center gap-3 mb-3">
              <div className="w-10 h-10 rounded-lg bg-purple-100 text-purple-700 flex items-center justify-center">
                <GraduationCap className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-base font-bold text-slate-900">Student Dashboard</h3>
                <p className="text-xs text-slate-500">Adaptive AI tutoring & personalized QA</p>
              </div>
            </div>
            <p className="text-sm text-slate-600 mb-6">
              Ask curriculum-grounded questions, view step-by-step verified explanations, inspect hypergraph evidence, and track mastery progress.
            </p>
            <Link to="/student/dashboard">
              <Button variant="primary" size="sm" className="w-full">
                Enter Student Portal
              </Button>
            </Link>
          </Card>
        </div>
      </section>
    </div>
  );
};

export default LandingPage;
