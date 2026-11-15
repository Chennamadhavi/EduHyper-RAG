import React from 'react';
import { Link } from 'react-router-dom';
import { Home, ArrowLeft } from 'lucide-react';
import Button from '../components/common/Button';

export const NotFoundPage: React.FC = () => {
  return (
    <div className="min-h-[70vh] flex flex-col items-center justify-center px-4 py-16 text-center">
      <div className="w-16 h-16 rounded-2xl bg-blue-50 text-blue-600 flex items-center justify-center font-black text-2xl mb-4 border border-blue-200">
        404
      </div>
      <h1 className="text-2xl sm:text-3xl font-bold text-slate-900 tracking-tight mb-2">
        Page Not Found
      </h1>
      <p className="text-sm text-slate-500 max-w-md mb-8">
        The requested path does not exist or has moved. Return to the EduHyper-RAG homepage or select a portal.
      </p>
      <div className="flex flex-wrap items-center justify-center gap-3">
        <Link to="/">
          <Button variant="primary" leftIcon={<Home className="w-4 h-4" />}>
            Back to Home
          </Button>
        </Link>
        <Link to="/teacher/dashboard">
          <Button variant="outline">
            Teacher Portal
          </Button>
        </Link>
        <Link to="/student/dashboard">
          <Button variant="secondary">
            Student Portal
          </Button>
        </Link>
      </div>
    </div>
  );
};

export default NotFoundPage;
