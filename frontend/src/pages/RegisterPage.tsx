import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { UserPlus, ArrowRight, AlertCircle, GraduationCap, Users } from 'lucide-react';
import Card, { CardContent, CardHeader, CardTitle, CardDescription } from '../components/common/Card';
import Button from '../components/common/Button';
import Input from '../components/common/Input';
import { useAuth } from '../hooks/useAuth';

export const RegisterPage: React.FC = () => {
  const navigate = useNavigate();
  const { register } = useAuth();

  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState<'student' | 'teacher'>('student');
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (username.trim().length < 3) {
      setError('Username must be at least 3 characters long.');
      return;
    }

    if (password.length < 6) {
      setError('Password must be at least 6 characters long.');
      return;
    }

    setIsSubmitting(true);
    try {
      const newUser = await register({
        username: username.trim(),
        email: email.trim(),
        password,
        role,
      });

      if (newUser.role === 'teacher') {
        navigate('/teacher/dashboard', { replace: true });
      } else {
        navigate('/student/dashboard', { replace: true });
      }
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Registration failed. Please review your input.';
      setError(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="max-w-md mx-auto px-4 py-16 sm:py-24">
      <Card className="shadow-md">
        <CardHeader className="text-center pb-2">
          <div className="w-12 h-12 rounded-full bg-blue-50 text-blue-600 flex items-center justify-center mx-auto mb-3">
            <UserPlus className="w-6 h-6" />
          </div>
          <CardTitle className="text-xl">Create EduHyper-RAG Account</CardTitle>
          <CardDescription>
            Join as a course instructor or student learner
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
            {/* Role Selection */}
            <div className="space-y-1.5">
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-700">
                Account Role
              </label>
              <div className="grid grid-cols-2 gap-2">
                <button
                  type="button"
                  onClick={() => setRole('student')}
                  className={`flex items-center justify-center gap-2 p-2.5 rounded-lg border text-xs font-semibold transition-all ${
                    role === 'student'
                      ? 'border-purple-600 bg-purple-50 text-purple-700 ring-2 ring-purple-600/20'
                      : 'border-slate-200 bg-white text-slate-600 hover:bg-slate-50'
                  }`}
                >
                  <GraduationCap className="w-4 h-4" />
                  <span>Student</span>
                </button>
                <button
                  type="button"
                  onClick={() => setRole('teacher')}
                  className={`flex items-center justify-center gap-2 p-2.5 rounded-lg border text-xs font-semibold transition-all ${
                    role === 'teacher'
                      ? 'border-blue-600 bg-blue-50 text-blue-700 ring-2 ring-blue-600/20'
                      : 'border-slate-200 bg-white text-slate-600 hover:bg-slate-50'
                  }`}
                >
                  <Users className="w-4 h-4" />
                  <span>Instructor</span>
                </button>
              </div>
            </div>

            <Input
              label="Username"
              type="text"
              placeholder="e.g. alex_mercer"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              disabled={isSubmitting}
              required
            />
            <Input
              label="Email Address"
              type="email"
              placeholder="e.g. alex@university.edu"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              disabled={isSubmitting}
              required
            />
            <Input
              label="Password"
              type="password"
              placeholder="Minimum 6 characters"
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
              Register & Sign In
            </Button>
          </form>

          <div className="text-center pt-2">
            <span className="text-xs text-slate-500">
              Already have an account?{' '}
              <Link to="/login" className="text-blue-600 font-medium hover:underline">
                Sign In
              </Link>
            </span>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default RegisterPage;
