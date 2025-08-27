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
  console.log('Context login:', { userData, token }); // Добавьте логирование
  setUser(userData);
  setToken(token); // Добавьте состояние токена в контекст
};

  const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
    setUser(null);
    setToken(null);
    window.location.href = '/';
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