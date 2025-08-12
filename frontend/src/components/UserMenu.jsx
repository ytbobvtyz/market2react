import { useContext } from 'react';
import { AuthContext } from '../contexts/auth-context';
import './UserMenu.css';

export const UserMenu = () => {
  const { isAuthenticated, user, logout } = useContext(AuthContext);

  if (!isAuthenticated) {
    return (
      <div className="user-menu">
        <a href="/login" className="auth-link">Авторизация</a>
        <span> / </span>
        <a href="/register" className="auth-link">Регистрация</a>
      </div>
    );
  }

  return (
    <div className="user-menu">
      <span className="username">{user?.username || 'Пользователь'}</span>
      <a href="/requests" className="menu-link">Мои запросы</a>
      <button onClick={logout} className="logout-button">Выйти</button>
    </div>
  );
};