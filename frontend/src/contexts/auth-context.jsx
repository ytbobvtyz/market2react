import { createContext, useState } from 'react';
import { AuthModal } from '../components/AuthModal';

export const AuthContext = createContext();

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [authModal, setAuthModal] = useState({
    isOpen: false,
    isLoginMode: true, // true = вход, false = регистрация
  });

  const showAuthModal = (isLoginMode) => {
    setAuthModal({ isOpen: true, isLoginMode });
  };

  const hideAuthModal = () => {
    setAuthModal({ isOpen: false, isLoginMode: true });
  };

  const login = (userData) => {
    setUser(userData);
    setIsAuthenticated(true);
    hideAuthModal();
  };

  const logout = () => {
    setUser(null);
    setIsAuthenticated(false);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated,
        login,
        logout,
        showAuthModal,
        hideAuthModal,
      }}
    >
      {children}
      {authModal.isOpen && (
        <AuthModal
          isLoginMode={authModal.isLoginMode}
          onClose={hideAuthModal}
          onLogin={login}
        />
      )}
    </AuthContext.Provider>
  );
}