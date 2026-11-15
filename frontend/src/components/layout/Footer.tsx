import React from 'react';
import { Network, ShieldCheck, Cpu, GitFork } from 'lucide-react';
import { Link } from 'react-router-dom';

export const Footer: React.FC = () => {
  return (
    <footer className="bg-slate-900 text-slate-400 py-12 border-t border-slate-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
          {/* Brand info */}
          <div className="md:col-span-2">
            <div className="flex items-center gap-2.5 mb-3">
              <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center text-white">
                <Network className="w-4 h-4" />
              </div>
              <span className="text-lg font-bold text-white tracking-tight">
                EduHyper<span className="text-blue-500">RAG</span>
              </span>
            </div>
            <p className="text-sm text-slate-400 max-w-md leading-relaxed mb-4">
              An Adaptive Hypergraph-Driven AI Tutor for Reducing Hallucinations in Educational Chatbots. Capturing high-order multi-entity relationships with agentic verification.
            </p>
            <div className="flex items-center gap-4 text-xs text-slate-500">
              <span className="flex items-center gap-1.5">
                <ShieldCheck className="w-4 h-4 text-emerald-500" /> Grounded Evidence
              </span>
              <span className="flex items-center gap-1.5">
                <Cpu className="w-4 h-4 text-blue-400" /> LangGraph Verification
              </span>
              <span className="flex items-center gap-1.5">
                <GitFork className="w-4 h-4 text-purple-400" /> HyperNetX Hypergraphs
              </span>
            </div>
          </div>

          {/* Quick links */}
          <div>
            <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-300 mb-3">
              Platform
            </h4>
            <ul className="space-y-2 text-sm">
              <li>
                <a href="#features" className="hover:text-white transition-colors">
                  Key Features
                </a>
              </li>
              <li>
                <a href="#how-it-works" className="hover:text-white transition-colors">
                  System Architecture
                </a>
              </li>
              <li>
                <Link to="/teacher/dashboard" className="hover:text-white transition-colors">
                  Teacher Portal
                </Link>
              </li>
              <li>
                <Link to="/student/dashboard" className="hover:text-white transition-colors">
                  Student Portal
                </Link>
              </li>
            </ul>
          </div>

          {/* Core Foundations */}
          <div>
            <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-300 mb-3">
              Foundations
            </h4>
            <ul className="space-y-2 text-sm">
              <li className="text-slate-400">Phase 1-9 Modular Pipeline</li>
              <li className="text-slate-400">HyperNetX High-Order Graphs</li>
              <li className="text-slate-400">ChromaDB Vector Retrieval</li>
              <li className="text-slate-400">FastAPI + React Foundation</li>
            </ul>
          </div>
        </div>

        <div className="pt-8 border-t border-slate-800 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-slate-500">
          <p>© {new Date().getFullYear()} EduHyper-RAG Research Project. All rights reserved.</p>
          <p>Enhanced Hyper-RAG with Agentic Verification</p>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
