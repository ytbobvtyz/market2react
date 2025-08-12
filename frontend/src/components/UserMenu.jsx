import { useContext } from 'react';
import { AuthContext } from '../contexts/auth-context';
import './UserMenu.css'; // Импорт стилей

export function UserMenu() {
  const { isAuthenticated, user, logout } = useContext(AuthContext);

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
          <a href="/login" className="auth-link">
            <i className="icon-login"></i> Войти
          </a>
          <a href="/register" className="auth-link register-link">
            <i className="icon-register"></i> Регистрация
          </a>
        </>
      )}
    </div>
  );
}