import React, { createContext, useContext, useState, useEffect } from 'react';
import authService from '../services/authService';
import { User, LoginPayload, RegisterPayload } from '../types/auth';

export interface AuthContextType {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (payload: LoginPayload) => Promise<User>;
  register: (payload: RegisterPayload) => Promise<User>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(authService.getCachedUser());
  const [token, setToken] = useState<string | null>(authService.getToken());
  const [isLoading, setIsLoading] = useState<boolean>(true);

  // Initialize session and verify token against backend on mount
  useEffect(() => {
    const initializeAuth = async () => {
      const storedToken = authService.getToken();
      if (!storedToken) {
        setIsLoading(false);
        return;
      }

      // Configure axios with stored token
      authService.setSession(storedToken, authService.getCachedUser());

      try {
        const currentUser = await authService.getMe();
        setUser(currentUser);
      } catch (error) {
        // Token is invalid or expired
        authService.logout();
        setUser(null);
        setToken(null);
      } finally {
        setIsLoading(false);
      }
    };

    initializeAuth();
  }, []);

  const login = async (payload: LoginPayload): Promise<User> => {
    setIsLoading(true);
    try {
      const authData = await authService.login(payload);
      setUser(authData.user);
      setToken(authData.access_token);
      return authData.user;
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (payload: RegisterPayload): Promise<User> => {
    setIsLoading(true);
    try {
      const authData = await authService.register(payload);
      setUser(authData.user);
      setToken(authData.access_token);
      return authData.user;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    authService.logout();
    setUser(null);
    setToken(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: !!user && !!token,
        isLoading,
        login,
        register,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export default AuthContext;
