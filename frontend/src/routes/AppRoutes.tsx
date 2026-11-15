import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';

// Layouts
import PublicLayout from '../layouts/PublicLayout';
import AppLayout from '../layouts/AppLayout';
import ProtectedRoute from '../components/common/ProtectedRoute';

// Public Pages
import LandingPage from '../pages/LandingPage';
import LoginPage from '../pages/LoginPage';
import RegisterPage from '../pages/RegisterPage';
import NotFoundPage from '../pages/NotFoundPage';

// Teacher Pages
import TeacherDashboardPage from '../pages/teacher/TeacherDashboardPage';
import TeacherCoursesPage from '../pages/teacher/TeacherCoursesPage';
import TeacherDocumentsPage from '../pages/teacher/TeacherDocumentsPage';
import TeacherStudentsPage from '../pages/teacher/TeacherStudentsPage';
import TeacherHypergraphPage from '../pages/teacher/TeacherHypergraphPage';
import TeacherAnalyticsPage from '../pages/teacher/TeacherAnalyticsPage';
import TeacherSettingsPage from '../pages/teacher/TeacherSettingsPage';

// Student Pages
import StudentDashboardPage from '../pages/student/StudentDashboardPage';
import StudentCoursesPage from '../pages/student/StudentCoursesPage';
import StudentTutorPage from '../pages/student/StudentTutorPage';
import StudentHistoryPage from '../pages/student/StudentHistoryPage';
import StudentProgressPage from '../pages/student/StudentProgressPage';
import StudentSettingsPage from '../pages/student/StudentSettingsPage';

export const AppRoutes: React.FC = () => {
  return (
    <Routes>
      {/* Public Pages wrapped in PublicLayout */}
      <Route element={<PublicLayout />}>
        <Route path="/" element={<LandingPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
      </Route>

      {/* Teacher Workspace Routes protected with ProtectedRoute (teacher role) */}
      <Route element={<ProtectedRoute allowedRoles={['teacher']} />}>
        <Route path="/teacher" element={<AppLayout initialRole="teacher" />}>
          <Route index element={<Navigate to="/teacher/dashboard" replace />} />
          <Route path="dashboard" element={<TeacherDashboardPage />} />
          <Route path="courses" element={<TeacherCoursesPage />} />
          <Route path="documents" element={<TeacherDocumentsPage />} />
          <Route path="students" element={<TeacherStudentsPage />} />
          <Route path="hypergraph" element={<TeacherHypergraphPage />} />
          <Route path="analytics" element={<TeacherAnalyticsPage />} />
          <Route path="settings" element={<TeacherSettingsPage />} />
        </Route>
      </Route>

      {/* Student Workspace Routes protected with ProtectedRoute (student role) */}
      <Route element={<ProtectedRoute allowedRoles={['student']} />}>
        <Route path="/student" element={<AppLayout initialRole="student" />}>
          <Route index element={<Navigate to="/student/dashboard" replace />} />
          <Route path="dashboard" element={<StudentDashboardPage />} />
          <Route path="courses" element={<StudentCoursesPage />} />
          <Route path="tutor" element={<StudentTutorPage />} />
          <Route path="history" element={<StudentHistoryPage />} />
          <Route path="progress" element={<StudentProgressPage />} />
          <Route path="settings" element={<StudentSettingsPage />} />
        </Route>
      </Route>

      {/* 404 Catch-All Page */}
      <Route element={<PublicLayout />}>
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  );
};

export default AppRoutes;
