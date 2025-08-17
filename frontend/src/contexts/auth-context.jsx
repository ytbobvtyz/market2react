import { createContext, useState, useEffect } from 'react';

export const AuthContext = createContext();

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('authToken') || null);

  // Вычисляемое состояние аутентификации
  const isAuthenticated = !!user;

  // При монтировании проверяем токен и загружаем пользователя
  useEffect(() => {
    if (token && !user) {
      // Здесь можно добавить запрос для проверки токена и загрузки данных пользователя
      // Например:
      // try {
      //   const userData = await verifyToken(token);
      //   setUser(userData);
      // } catch {
      //   localStorage.removeItem('authToken');
      //   setToken(null);
      // }
    }
  }, [token, user]);

const login = (userData, token) => {
  setUser(userData);
  setIsAuthenticated(true);
  setToken(token); // Добавьте состояние токена в контекст
};

  const logout = () => {
    setUser(null);
    setToken(null);
    localStorage.removeItem('authToken');
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated,
        login,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}