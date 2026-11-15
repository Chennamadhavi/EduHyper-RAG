export interface User {
  id: number;
  username: string;
  email: string;
  role: 'teacher' | 'student';
  created_at?: string;
}

export interface LoginPayload {
  username: string;
  password: string;
}

export interface RegisterPayload {
  username: string;
  email: string;
  password: string;
  role: 'teacher' | 'student';
  full_name?: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}
