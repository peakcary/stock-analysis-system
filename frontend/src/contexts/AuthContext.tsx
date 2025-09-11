import React, { createContext, useContext, useState, useEffect, type ReactNode } from 'react';
import { message } from 'antd';
import { adminAuthManager, adminApiClient, type AdminUser, type AdminLoginResult } from '../../../shared/admin-auth';


interface AuthContextType {
  isAuthenticated: boolean;
  user: AdminUser | null;
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
  const [user, setUser] = useState<AdminUser | null>(null);
  const [loading, setLoading] = useState(true);


  // 管理员登录函数 - 使用新的错误处理
  const login = async (username: string, password: string): Promise<boolean> => {
    try {
      const result: AdminLoginResult = await adminAuthManager.login(username, password);
      
      if (result.success && result.user) {
        setUser(result.user);
        setIsAuthenticated(true);
        message.success('管理员登录成功');
        return true;
      } else if (result.error) {
        // 使用用户友好的错误信息
        const userFriendlyMessage = adminAuthManager.getErrorMessage(result.error);
        message.error(userFriendlyMessage);
        return false;
      } else {
        message.error('登录失败，请稍后重试');
        return false;
      }
    } catch (error: any) {
      console.error('管理员登录异常:', error);
      message.error('登录过程中发生异常，请稍后重试');
      return false;
    }
  };

  // 退出登录
  const logout = async () => {
    try {
      await adminAuthManager.logout();
      setUser(null);
      setIsAuthenticated(false);
      message.success('已退出登录');
    } catch (error) {
      console.error('登出失败:', error);
      // 即使登出请求失败，也要清除本地状态
      setUser(null);
      setIsAuthenticated(false);
    }
  };

  // 初始化管理员认证状态
  useEffect(() => {
    const initAuth = async () => {
      if (adminAuthManager.isAuthenticated()) {
        const isValid = await adminAuthManager.checkAuth();
        if (isValid) {
          const currentUser = adminAuthManager.getUser();
          setUser(currentUser);
          setIsAuthenticated(true);
        } else {
          await logout();
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