import { useContext, useState } from 'react';
import { AuthContext } from '../contexts/auth-context';
import { AuthModal } from './AuthModal'; // Добавляем импорт модалки
import './UserMenu.css';

export function UserMenu() {
  const { isAuthenticated, user, logout } = useContext(AuthContext);
  const [authModalOpen, setAuthModalOpen] = useState(false);
  const [isLoginMode, setIsLoginMode] = useState(true);

  const handleAuthSuccess = (authData) => {
    // Обработка успешной аутентификации
    console.log('Auth success:', authData);
    setAuthModalOpen(false);
  };

  const showAuthModal = (loginMode) => {
    setIsLoginMode(loginMode);
    setAuthModalOpen(true);
  };

  return (
    <div className="user-menu">
      {isAuthenticated ? (
        <>
          <span className="user-greeting">Привет, {user?.username || 'друг'}!</span>
          <a href="/requests" className="menu-link">
            <i className="icon-requests"></i> Мои запросы
          </a>
          <button onClick={logout} className="logout-btn">
            <i className="icon-logout"></i> Выйти
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
        />
      )}
    </div>
  );
}