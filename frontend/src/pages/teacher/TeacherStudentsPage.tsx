import React, { useState, useEffect } from 'react';
import { Users, UserPlus, Calendar, AlertCircle, BookOpen, CheckCircle2 } from 'lucide-react';
import PageHeader from '../../components/common/PageHeader';
import Card from '../../components/common/Card';
import Button from '../../components/common/Button';
import Badge from '../../components/common/Badge';
import Modal from '../../components/common/Modal';
import Input from '../../components/common/Input';
import LoadingState from '../../components/common/LoadingState';
import EmptyState from '../../components/common/EmptyState';
import courseService from '../../services/courseService';
import { Course, EnrolledStudent } from '../../types/course';

export const TeacherStudentsPage: React.FC = () => {
  const [courses, setCourses] = useState<Course[]>([]);
  const [selectedCourseId, setSelectedCourseId] = useState<number | null>(null);
  const [students, setStudents] = useState<EnrolledStudent[]>([]);
  const [loadingCourses, setLoadingCourses] = useState<boolean>(true);
  const [loadingStudents, setLoadingStudents] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Modal State
  const [isModalOpen, setIsModalOpen] = useState<boolean>(false);
  const [studentIdentifier, setStudentIdentifier] = useState<string>('');
  const [modalSubmitting, setModalSubmitting] = useState<boolean>(false);
  const [modalError, setModalError] = useState<string | null>(null);
  const [modalSuccess, setModalSuccess] = useState<string | null>(null);

  // Load teacher's courses
  useEffect(() => {
    const fetchCourses = async () => {
      setLoadingCourses(true);
      setError(null);
      try {
        const data = await courseService.listCourses();
        setCourses(data);
        if (data.length > 0) {
          setSelectedCourseId(data[0].id);
        }
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to load courses.');
      } finally {
        setLoadingCourses(false);
      }
    };
    fetchCourses();
  }, []);

  // Load roster whenever selectedCourseId changes
  useEffect(() => {
    if (!selectedCourseId) return;

    const fetchRoster = async () => {
      setLoadingStudents(true);
      try {
        const roster = await courseService.listCourseStudents(selectedCourseId);
        setStudents(roster);
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to load student roster.');
      } finally {
        setLoadingStudents(false);
      }
    };

    fetchRoster();
  }, [selectedCourseId]);

  const handleEnrollStudent = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedCourseId || !studentIdentifier.trim()) {
      setModalError('Please enter a student username or email.');
      return;
    }

    setModalSubmitting(true);
    setModalError(null);
    setModalSuccess(null);

    try {
      const student = await courseService.enrollStudentByTeacher(selectedCourseId, studentIdentifier.trim());
      setModalSuccess(`Successfully enrolled ${student.username} (${student.email}) into the course!`);
      setStudentIdentifier('');
      // Refresh roster
      const updatedRoster = await courseService.listCourseStudents(selectedCourseId);
      setStudents(updatedRoster);
    } catch (err: any) {
      setModalError(err.response?.data?.detail || 'Failed to enroll student. Check username/email.');
    } finally {
      setModalSubmitting(false);
    }
  };

  const selectedCourse = courses.find((c) => c.id === selectedCourseId);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Student Management"
        description="Monitor student course enrollments, access rosters, and manage student permissions."
        breadcrumbs={[{ label: 'Teacher', path: '/teacher/dashboard' }, { label: 'Students' }]}
        badge={<Badge variant="default">Roster & Access</Badge>}
        actions={
          <Button
            size="sm"
            leftIcon={<UserPlus className="w-4 h-4" />}
            onClick={() => {
              setIsModalOpen(true);
              setModalError(null);
              setModalSuccess(null);
            }}
            disabled={!selectedCourseId}
          >
            Enroll Student
          </Button>
        }
      />

      {error && (
        <div className="p-4 rounded-xl bg-red-50 border border-red-200 text-sm text-red-800 flex items-center gap-2">
          <AlertCircle className="w-5 h-5 text-red-600 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {loadingCourses ? (
        <LoadingState message="Loading courses and rosters..." size="lg" />
      ) : courses.length === 0 ? (
        <EmptyState
          icon={<BookOpen className="w-8 h-8 text-blue-600" />}
          title="No Courses Available"
          description="Create a course first before enrolling students."
        />
      ) : (
        <div className="space-y-6">
          {/* Course Selector Filter */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-4 rounded-xl bg-white border border-slate-200/80 shadow-xs">
            <div className="flex items-center gap-3">
              <label className="text-xs font-bold uppercase tracking-wider text-slate-600">
                Course:
              </label>
              <select
                value={selectedCourseId || ''}
                onChange={(e) => setSelectedCourseId(Number(e.target.value))}
                className="bg-slate-50 border border-slate-300 rounded-lg px-3 py-1.5 text-sm font-medium text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {courses.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.course_code} — {c.title}
                  </option>
                ))}
              </select>
            </div>

            <div className="text-xs text-slate-500">
              Total Enrolled Students: <span className="font-bold text-slate-800">{students.length}</span>
            </div>
          </div>

          {/* Student Roster Table */}
          {loadingStudents ? (
            <LoadingState message="Loading student roster..." size="md" />
          ) : students.length === 0 ? (
            <EmptyState
              icon={<Users className="w-8 h-8 text-emerald-600" />}
              title="No Students Enrolled in this Course"
              description={`No students are currently enrolled in ${selectedCourse?.course_code || 'this course'}. Use the button above to enroll a student.`}
              action={
                <Button
                  variant="primary"
                  size="sm"
                  leftIcon={<UserPlus className="w-4 h-4" />}
                  onClick={() => setIsModalOpen(true)}
                >
                  Enroll First Student
                </Button>
              }
            />
          ) : (
            <Card className="overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead className="bg-slate-50 border-b border-slate-200 text-xs font-semibold uppercase tracking-wider text-slate-500">
                    <tr>
                      <th className="px-6 py-3.5">Student Username</th>
                      <th className="px-6 py-3.5">Email</th>
                      <th className="px-6 py-3.5">Role</th>
                      <th className="px-6 py-3.5">Enrolled Date</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 bg-white">
                    {students.map((student) => (
                      <tr key={student.id} className="hover:bg-slate-50/80 transition-colors">
                        <td className="px-6 py-4 font-semibold text-slate-900 flex items-center gap-2.5">
                          <div className="w-7 h-7 rounded-full bg-purple-100 text-purple-700 font-bold text-xs flex items-center justify-center uppercase">
                            {student.username.charAt(0)}
                          </div>
                          <span>{student.username}</span>
                        </td>
                        <td className="px-6 py-4 text-slate-600">{student.email}</td>
                        <td className="px-6 py-4">
                          <Badge variant="purple" size="sm">
                            Student
                          </Badge>
                        </td>
                        <td className="px-6 py-4 text-xs text-slate-500">
                          {student.enrolled_at ? student.enrolled_at.split(' ')[0] : 'N/A'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Card>
          )}
        </div>
      )}

      {/* Enroll Student Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title={`Enroll Student into ${selectedCourse?.course_code || 'Course'}`}
      >
        <form onSubmit={handleEnrollStudent} className="space-y-4">
          {modalError && (
            <div className="p-3 rounded-lg bg-red-50 border border-red-200 text-xs text-red-800 flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-red-600 shrink-0" />
              <span>{modalError}</span>
            </div>
          )}

          {modalSuccess && (
            <div className="p-3 rounded-lg bg-emerald-50 border border-emerald-200 text-xs text-emerald-800 flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
              <span>{modalSuccess}</span>
            </div>
          )}

          <Input
            label="Student Username or Email"
            placeholder="e.g. student or student@eduhyperrag.edu"
            value={studentIdentifier}
            onChange={(e) => setStudentIdentifier(e.target.value)}
            disabled={modalSubmitting}
            required
            helperText="Enter the registered username or email of the student"
          />

          <div className="pt-4 border-t border-slate-100 flex items-center justify-end gap-2.5">
            <Button
              type="button"
              variant="secondary"
              size="sm"
              onClick={() => setIsModalOpen(false)}
              disabled={modalSubmitting}
            >
              Close
            </Button>
            <Button
              type="submit"
              variant="primary"
              size="sm"
              isLoading={modalSubmitting}
            >
              Enroll Student
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};

export default TeacherStudentsPage;
