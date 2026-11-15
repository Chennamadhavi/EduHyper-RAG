import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  BookOpen,
  FileText,
  Users,
  CheckCircle2,
  Bot,
  AlertCircle,
  Plus,
  Compass,
} from 'lucide-react';
import PageHeader from '../../components/common/PageHeader';
import Card, { CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from '../../components/common/Card';
import Button from '../../components/common/Button';
import Badge from '../../components/common/Badge';
import LoadingState from '../../components/common/LoadingState';
import EmptyState from '../../components/common/EmptyState';
import courseService from '../../services/courseService';
import { Course } from '../../types/course';

export const StudentCoursesPage: React.FC = () => {
  const [enrolledCourses, setEnrolledCourses] = useState<Course[]>([]);
  const [allCourses, setAllCourses] = useState<Course[]>([]);
  const [activeTab, setActiveTab] = useState<'enrolled' | 'browse'>('enrolled');
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [enrollingId, setEnrollingId] = useState<number | null>(null);

  const fetchCourses = async () => {
    setLoading(true);
    setError(null);
    try {
      const [enrolled, catalog] = await Promise.all([
        courseService.listCourses(false),
        courseService.listCourses(true),
      ]);
      setEnrolledCourses(enrolled);
      setAllCourses(catalog);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load courses.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCourses();
  }, []);

  const handleEnroll = async (courseId: number) => {
    setEnrollingId(courseId);
    try {
      await courseService.enrollCourse(courseId);
      await fetchCourses();
      setActiveTab('enrolled');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Enrollment failed.');
    } finally {
      setEnrollingId(null);
    }
  };

  const displayedCourses = activeTab === 'enrolled' ? enrolledCourses : allCourses;

  return (
    <div className="space-y-6">
      <PageHeader
        title="My Courses"
        description="Courses you are currently enrolled in with attached knowledge bases and AI tutoring."
        breadcrumbs={[{ label: 'Student', path: '/student/dashboard' }, { label: 'Courses' }]}
        badge={<Badge variant="primary">Curriculum Access</Badge>}
      />

      {/* Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-200">
        <button
          onClick={() => setActiveTab('enrolled')}
          className={`flex items-center gap-2 px-4 py-2.5 text-sm font-semibold border-b-2 transition-colors ${
            activeTab === 'enrolled'
              ? 'border-blue-600 text-blue-600'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <BookOpen className="w-4 h-4" />
          <span>My Enrolled Courses ({enrolledCourses.length})</span>
        </button>

        <button
          onClick={() => setActiveTab('browse')}
          className={`flex items-center gap-2 px-4 py-2.5 text-sm font-semibold border-b-2 transition-colors ${
            activeTab === 'browse'
              ? 'border-blue-600 text-blue-600'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <Compass className="w-4 h-4" />
          <span>Explore All Courses ({allCourses.length})</span>
        </button>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-red-50 border border-red-200 text-sm text-red-800 flex items-center gap-2">
          <AlertCircle className="w-5 h-5 text-red-600 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {loading ? (
        <LoadingState message="Loading courses and syllabi..." size="lg" />
      ) : displayedCourses.length === 0 ? (
        <EmptyState
          icon={<BookOpen className="w-8 h-8 text-blue-600" />}
          title={
            activeTab === 'enrolled'
              ? 'You are not enrolled in any courses yet'
              : 'No courses available in the catalog'
          }
          description="Browse the course catalog to enroll in educational subjects and begin grounded AI tutoring."
          action={
            activeTab === 'enrolled' ? (
              <Button
                variant="primary"
                size="sm"
                leftIcon={<Compass className="w-4 h-4" />}
                onClick={() => setActiveTab('browse')}
              >
                Explore Course Catalog
              </Button>
            ) : undefined
          }
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {displayedCourses.map((course) => {
            const isEnrolled = enrolledCourses.some((e) => e.id === course.id);

            return (
              <Card key={course.id} hover className="flex flex-col justify-between">
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <Badge variant="purple" size="sm">
                      {course.course_code}
                    </Badge>
                    {isEnrolled ? (
                      <Badge variant="success" size="sm">
                        <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                        Enrolled
                      </Badge>
                    ) : (
                      <Badge variant="default" size="sm">
                        Available
                      </Badge>
                    )}
                  </div>
                  <CardTitle className="mt-2.5 text-base sm:text-lg">{course.title}</CardTitle>
                  <CardDescription className="line-clamp-2">
                    {course.description || 'No description available.'}
                  </CardDescription>
                </CardHeader>

                <CardContent className="py-2">
                  <div className="flex items-center justify-between pt-2 border-t border-slate-100 text-xs text-slate-600">
                    <div className="flex items-center gap-1.5">
                      <FileText className="w-4 h-4 text-purple-600" />
                      <span>{course.document_count || 0} Documents</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <Users className="w-4 h-4 text-slate-400" />
                      <span>Instructor: {course.teacher_name || 'Faculty'}</span>
                    </div>
                  </div>
                </CardContent>

                <CardFooter className="pt-3">
                  {isEnrolled ? (
                    <Link to="/student/tutor" className="w-full">
                      <Button
                        variant="primary"
                        size="sm"
                        className="w-full justify-center"
                        leftIcon={<Bot className="w-4 h-4" />}
                      >
                        Ask AI Tutor
                      </Button>
                    </Link>
                  ) : (
                    <Button
                      variant="outline"
                      size="sm"
                      className="w-full justify-center"
                      isLoading={enrollingId === course.id}
                      onClick={() => handleEnroll(course.id)}
                      leftIcon={<Plus className="w-4 h-4" />}
                    >
                      Enroll in Course
                    </Button>
                  )}
                </CardFooter>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default StudentCoursesPage;
