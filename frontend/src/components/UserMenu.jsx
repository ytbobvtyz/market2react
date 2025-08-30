import { useContext, useState } from 'react';
import { AuthContext } from '../contexts/auth-context';
import { AuthModal } from './AuthModal'; // Добавляем импорт модалки
import './UserMenu.css';

export function UserMenu() {
  const { isAuthenticated, user, logout, login } = useContext(AuthContext);
  const [authModalOpen, setAuthModalOpen] = useState(false);
  const [isLoginMode, setIsLoginMode] = useState(true);

  const handleAuthSuccess = ({ user: userData, token }) => {
  login(userData, token); // Используем метод из контекста
  setAuthModalOpen(false);
};

  const showAuthModal = (loginMode = true) => {
    setIsLoginMode(loginMode);
    setAuthModalOpen(true);
  };

  return (
    <div className="user-menu">
      {isAuthenticated ? (
        <>
          <span className="user-greeting">Привет, {user?.username || 'друг'}!</span>

          <button onClick={logout} className="logout-btn">
             Выйти
          </button>
        </>
      ) : (
        <>
          <button 
            onClick={() => showAuthModal(true)} 
            className="auth-link"
          >
            <i className="icon-login"></i> Войти
          </button>
          <button 
            onClick={() => showAuthModal(false)} 
            className="auth-link register-link"
          >
            <i className="icon-register"></i> Регистрация
          </button>
        </>
      )}

      {/* Модальное окно аутентификации */}
      {authModalOpen && (
        <AuthModal
          isLoginMode={isLoginMode}
          onClose={() => setAuthModalOpen(false)}
          onLogin={handleAuthSuccess}
          switchMode={() => setIsLoginMode(!isLoginMode)}
        />
      )}
    </div>
  );
}