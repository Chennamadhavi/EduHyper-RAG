import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { BookOpen, Plus, FileText, Users, Calendar, ArrowRight, AlertCircle } from 'lucide-react';
import PageHeader from '../../components/common/PageHeader';
import Card, { CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from '../../components/common/Card';
import Button from '../../components/common/Button';
import Badge from '../../components/common/Badge';
import Modal from '../../components/common/Modal';
import Input from '../../components/common/Input';
import LoadingState from '../../components/common/LoadingState';
import EmptyState from '../../components/common/EmptyState';
import courseService from '../../services/courseService';
import { Course } from '../../types/course';

export const TeacherCoursesPage: React.FC = () => {
  const [courses, setCourses] = useState<Course[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Modal State
  const [isModalOpen, setIsModalOpen] = useState<boolean>(false);
  const [courseCode, setCourseCode] = useState<string>('');
  const [title, setTitle] = useState<string>('');
  const [description, setDescription] = useState<string>('');
  const [modalError, setModalError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState<boolean>(false);

  const fetchCourses = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await courseService.listCourses();
      setCourses(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load courses.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCourses();
  }, []);

  const handleCreateCourse = async (e: React.FormEvent) => {
    e.preventDefault();
    setModalError(null);

    if (!courseCode.trim() || !title.trim()) {
      setModalError('Course code and title are required.');
      return;
    }

    setSubmitting(true);
    try {
      await courseService.createCourse({
        course_code: courseCode.trim(),
        title: title.trim(),
        description: description.trim(),
      });
      setIsModalOpen(false);
      setCourseCode('');
      setTitle('');
      setDescription('');
      await fetchCourses();
    } catch (err: any) {
      setModalError(err.response?.data?.detail || 'Failed to create course.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="My Courses"
        description="Manage assigned curriculum courses, textbook attachments, and student enrollments."
        breadcrumbs={[{ label: 'Teacher', path: '/teacher/dashboard' }, { label: 'Courses' }]}
        badge={<Badge variant="primary">Course Administration</Badge>}
        actions={
          <Button
            size="sm"
            leftIcon={<Plus className="w-4 h-4" />}
            onClick={() => setIsModalOpen(true)}
          >
            Create New Course
          </Button>
        }
      />

      {error && (
        <div className="p-4 rounded-xl bg-red-50 border border-red-200 text-sm text-red-800 flex items-center gap-2">
          <AlertCircle className="w-5 h-5 text-red-600 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {loading ? (
        <LoadingState message="Loading courses from database..." size="lg" />
      ) : courses.length === 0 ? (
        <EmptyState
          icon={<BookOpen className="w-8 h-8 text-blue-600" />}
          title="No Courses Created Yet"
          description="Create your first educational course to start uploading syllabus documents and constructing hypergraphs."
          action={
            <Button
              variant="primary"
              size="sm"
              leftIcon={<Plus className="w-4 h-4" />}
              onClick={() => setIsModalOpen(true)}
            >
              Create Course
            </Button>
          }
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {courses.map((course) => (
            <Card key={course.id} hover className="flex flex-col justify-between">
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <Badge variant="purple" size="sm">
                    {course.course_code}
                  </Badge>
                  <span className="text-[11px] text-slate-400 flex items-center gap-1">
                    <Calendar className="w-3.5 h-3.5" />
                    {course.created_at ? course.created_at.split(' ')[0] : 'Active'}
                  </span>
                </div>
                <CardTitle className="mt-2.5 text-base sm:text-lg">{course.title}</CardTitle>
                <CardDescription className="line-clamp-2">
                  {course.description || 'No course description provided.'}
                </CardDescription>
              </CardHeader>

              <CardContent className="py-2">
                <div className="grid grid-cols-2 gap-2 pt-2 border-t border-slate-100">
                  <div className="flex items-center gap-2 text-xs text-slate-600">
                    <FileText className="w-4 h-4 text-purple-600" />
                    <span>
                      <strong>{course.document_count || 0}</strong> Documents
                    </span>
                  </div>
                  <div className="flex items-center gap-2 text-xs text-slate-600">
                    <Users className="w-4 h-4 text-emerald-600" />
                    <span>
                      <strong>{course.student_count || 0}</strong> Students
                    </span>
                  </div>
                </div>
              </CardContent>

              <CardFooter className="pt-3">
                <Link to="/teacher/documents" className="w-full">
                  <Button
                    variant="outline"
                    size="sm"
                    className="w-full justify-between"
                    rightIcon={<ArrowRight className="w-3.5 h-3.5" />}
                  >
                    Manage Documents
                  </Button>
                </Link>
              </CardFooter>
            </Card>
          ))}
        </div>
      )}

      {/* Create Course Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title="Create New Course"
      >
        <form onSubmit={handleCreateCourse} className="space-y-4">
          {modalError && (
            <div className="p-3 rounded-lg bg-red-50 border border-red-200 text-xs text-red-800 flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-red-600 shrink-0" />
              <span>{modalError}</span>
            </div>
          )}

          <Input
            label="Course Code"
            placeholder="e.g. BIO101, CHEM202, CS301"
            value={courseCode}
            onChange={(e) => setCourseCode(e.target.value)}
            disabled={submitting}
            required
            helperText="Short uppercase code identifier"
          />

          <Input
            label="Course Title"
            placeholder="e.g. Molecular & Cellular Biology"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            disabled={submitting}
            required
          />

          <div className="space-y-1.5">
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-700">
              Description / Syllabus Overview
            </label>
            <textarea
              rows={3}
              placeholder="Brief summary of curriculum topics and learning goals..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              disabled={submitting}
              className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20"
            />
          </div>

          <div className="pt-4 border-t border-slate-100 flex items-center justify-end gap-2.5">
            <Button
              type="button"
              variant="secondary"
              size="sm"
              onClick={() => setIsModalOpen(false)}
              disabled={submitting}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              size="sm"
              isLoading={submitting}
            >
              Create Course
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};

export default TeacherCoursesPage;
