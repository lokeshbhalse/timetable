// frontend/src/context/AuthContext.tsx
import React, { createContext, useContext, useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

interface User {
  id: string;
  username: string;
  email: string;
  full_name: string;
  role: 'admin' | 'teacher' | 'student';
}

interface SignupData {
  username: string;
  email: string;
  password: string;
  full_name: string;
  role: 'admin' | 'teacher' | 'student';
}

interface AuthContextType {
  user: User | null;
  login: (username: string, password: string, role: string) => Promise<boolean>;
  signup: (data: SignupData) => Promise<boolean>;
  logout: () => void;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    // Check localStorage for existing session
    const storedUser = localStorage.getItem('user');
    if (storedUser) {
      setUser(JSON.parse(storedUser));
    }
  }, []);

  const login = async (username: string, password: string, role: string): Promise<boolean> => {
    // Demo login - In production, call your backend API
    // For demo purposes, hardcoded credentials
    if (username === 'admin' && password === 'admin123') {
      const user = {
        id: '1',
        username: 'admin',
        email: 'admin@sgsits.edu',
        full_name: 'Administrator',
        role: 'admin' as const
      };
      setUser(user);
      localStorage.setItem('user', JSON.stringify(user));
      return true;
    } else if (username === 'teacher1' && password === '123456') {
      const user = {
        id: '2',
        username: 'teacher1',
        email: 'teacher1@sgsits.edu',
        full_name: 'Prof. Abhijeet',
        role: 'teacher' as const
      };
      setUser(user);
      localStorage.setItem('user', JSON.stringify(user));
      return true;
    } else if (username === 'student1' && password === '123456') {
      const user = {
        id: '3',
        username: 'student1',
        email: 'student1@sgsits.edu',
        full_name: 'John Doe',
        role: 'student' as const
      };
      setUser(user);
      localStorage.setItem('user', JSON.stringify(user));
      return true;
    }
    return false;
  };

  const signup = async (data: SignupData): Promise<boolean> => {
    // Demo signup - In production, call your backend API
    const user = {
      id: Date.now().toString(),
      username: data.username,
      email: data.email,
      full_name: data.full_name,
      role: data.role
    };
    setUser(user);
    localStorage.setItem('user', JSON.stringify(user));
    return true;
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem('user');
    navigate('/');
  };

  return (
    <AuthContext.Provider value={{
      user,
      login,
      signup,
      logout,
      isAuthenticated: !!user
    }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};