import React, { useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { Lock, ArrowRight, AlertCircle, Key, UserCheck } from 'lucide-react';
import Card, { CardContent, CardHeader, CardTitle, CardDescription } from '../components/common/Card';
import Button from '../components/common/Button';
import Input from '../components/common/Input';
import { useAuth } from '../hooks/useAuth';

export const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const redirectPath = searchParams.get('redirect');

  const { login } = useAuth();
  const [identifier, setIdentifier] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!identifier.trim() || !password) {
      setError('Please provide both username/email and password.');
      return;
    }

    setIsSubmitting(true);
    try {
      const user = await login({ username: identifier.trim(), password });
      
      // Determine redirection target
      if (redirectPath) {
        navigate(redirectPath, { replace: true });
      } else if (user.role === 'teacher') {
        navigate('/teacher/dashboard', { replace: true });
      } else {
        navigate('/student/dashboard', { replace: true });
      }
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Authentication failed. Please verify your credentials.';
      setError(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  // Quick fill helper for existing accounts
  const handleQuickFill = (u: string, p: string) => {
    setIdentifier(u);
    setPassword(p);
    setError(null);
  };

  return (
    <div className="max-w-md mx-auto px-4 py-16 sm:py-24">
      <Card className="shadow-md">
        <CardHeader className="text-center pb-2">
          <div className="w-12 h-12 rounded-full bg-blue-50 text-blue-600 flex items-center justify-center mx-auto mb-3">
            <Lock className="w-6 h-6" />
          </div>
          <CardTitle className="text-xl">Sign In to EduHyper-RAG</CardTitle>
          <CardDescription>
            Access your verified course materials and personalized AI tutoring
          </CardDescription>
        </CardHeader>

        <CardContent className="space-y-4 pt-4">
          {error && (
            <div className="p-3 rounded-lg bg-red-50 border border-red-200 text-xs text-red-800 flex items-start gap-2">
              <AlertCircle className="w-4 h-4 text-red-600 mt-0.5 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <Input
              label="Username or Email"
              type="text"
              placeholder="e.g. teacher or teacher@eduhyperrag.edu"
              value={identifier}
              onChange={(e) => setIdentifier(e.target.value)}
              disabled={isSubmitting}
              required
            />
            <Input
              label="Password"
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={isSubmitting}
              required
            />

            <Button
              type="submit"
              variant="primary"
              className="w-full"
              isLoading={isSubmitting}
              rightIcon={<ArrowRight className="w-4 h-4" />}
            >
              Sign In
            </Button>
          </form>

          {/* Quick-Fill Existing Accounts */}
          <div className="pt-4 border-t border-slate-200/80 space-y-2">
            <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider text-center flex items-center justify-center gap-1.5">
              <Key className="w-3.5 h-3.5 text-slate-400" />
              Quick-Fill Verified System Accounts
            </div>
            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={() => handleQuickFill('teacher', 'password123')}
                className="flex items-center justify-center gap-1.5 px-2.5 py-1.5 rounded-lg border border-slate-200 bg-slate-50 text-slate-700 hover:bg-slate-100 text-xs transition-colors"
              >
                <UserCheck className="w-3.5 h-3.5 text-blue-600" />
                <span>Teacher Demo</span>
              </button>
              <button
                type="button"
                onClick={() => handleQuickFill('student', 'password123')}
                className="flex items-center justify-center gap-1.5 px-2.5 py-1.5 rounded-lg border border-slate-200 bg-slate-50 text-slate-700 hover:bg-slate-100 text-xs transition-colors"
              >
                <UserCheck className="w-3.5 h-3.5 text-purple-600" />
                <span>Student Demo</span>
              </button>
            </div>
          </div>

          <div className="text-center pt-2">
            <span className="text-xs text-slate-500">
              Don't have an account?{' '}
              <Link to="/register" className="text-blue-600 font-medium hover:underline">
                Sign Up
              </Link>
            </span>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default LoginPage;
