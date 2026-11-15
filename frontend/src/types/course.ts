export interface Course {
  id: number;
  course_code: string;
  title: string;
  description?: string;
  teacher_id: number;
  teacher_name?: string;
  document_count?: number;
  student_count?: number;
  created_at?: string;
  is_enrolled?: boolean;
}

export interface CourseCreatePayload {
  course_code: string;
  title: string;
  description?: string;
}

export interface EnrolledStudent {
  id: number;
  username: string;
  email: string;
  enrolled_at?: string;
}

