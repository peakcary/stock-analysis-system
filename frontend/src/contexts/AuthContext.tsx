import React, { createContext, useContext, useState, useEffect, type ReactNode } from 'react';
import { message } from 'antd';
import { authManager, apiClient, type User } from '../../../shared/auth';


interface AuthContextType {
  isAuthenticated: boolean;
  user: User | null;
  login: (username: string, password: string) => Promise<boolean>;
  logout: () => void;
  loading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);


  // 登录函数
  const login = async (username: string, password: string): Promise<boolean> => {
    try {
      const result = await authManager.login(username, password);
      if (result.success && result.user) {
        setUser(result.user);
        setIsAuthenticated(true);
        message.success('登录成功');
        return true;
      }
      return false;
    } catch (error: any) {
      console.error('登录失败:', error);
      message.error(error || '登录失败');
      return false;
    }
  };

  // 退出登录
  const logout = () => {
    authManager.logout();
    setUser(null);
    setIsAuthenticated(false);
    message.success('已退出登录');
  };

  // 初始化认证状态
  useEffect(() => {
    const initAuth = async () => {
      if (authManager.isAuthenticated()) {
        const isValid = await authManager.checkAuth();
        if (isValid) {
          const currentUser = authManager.getUser();
          setUser(currentUser);
          setIsAuthenticated(true);
        } else {
          logout();
        }
      }
      setLoading(false);
    };

    initAuth();
  }, []);

  const value: AuthContextType = {
    isAuthenticated,
    user,
    login,
    logout,
    loading
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};