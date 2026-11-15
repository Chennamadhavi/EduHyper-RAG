import apiClient from './api';
import { Course, CourseCreatePayload, EnrolledStudent } from '../types/course';

export const courseService = {
  /**
   * Fetches courses list.
   * If all is true, returns all catalog courses.
   * Otherwise returns courses filtered to user role (taught courses for teacher, enrolled for student).
   */
  async listCourses(all: boolean = false): Promise<Course[]> {
    const response = await apiClient.get<Course[]>('/api/courses', {
      params: all ? { all: true } : {},
    });
    return response.data;
  },

  /**
   * Fetches details for a specific course.
   */
  async getCourse(courseId: number): Promise<Course> {
    const response = await apiClient.get<Course>(`/api/courses/${courseId}`);
    return response.data;
  },

  /**
   * Creates a new course record (Instructor only).
   */
  async createCourse(payload: CourseCreatePayload): Promise<Course> {
    const response = await apiClient.post<Course>('/api/courses', payload);
    return response.data;
  },

  /**
   * Enrolls the current authenticated student into a course.
   */
  async enrollCourse(courseId: number): Promise<{ success: boolean; message: string; course_id: number }> {
    const response = await apiClient.post<{ success: boolean; message: string; course_id: number }>(
      `/api/courses/${courseId}/enroll`
    );
    return response.data;
  },

  /**
   * Fetches enrolled students roster for an instructor's course.
   */
  async listCourseStudents(courseId: number): Promise<EnrolledStudent[]> {
    const response = await apiClient.get<EnrolledStudent[]>(`/api/courses/${courseId}/students`);
    return response.data;
  },

  /**
   * Enrolls a student into a course by teacher using username or email.
   */
  async enrollStudentByTeacher(courseId: number, usernameOrEmail: string): Promise<EnrolledStudent> {
    const response = await apiClient.post<EnrolledStudent>(`/api/courses/${courseId}/students`, {
      username_or_email: usernameOrEmail,
    });
    return response.data;
  },
};

export default courseService;
