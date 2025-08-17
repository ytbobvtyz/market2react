import { useState } from 'react';
import axios from 'axios';
import './AuthModal.css';

export function AuthModal({ isLoginMode, onClose, onLogin, switchMode }) {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    username: ''
  });
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    try {
      let response;
      
      if (isLoginMode) {
        // Для логина используем FormData как ожидает OAuth2
        const formData = new FormData();
        formData.append('username', formData.email); // backend ожидает username, но мы используем email
        formData.append('password', formData.password);
        
        response = await axios.post(
          'http://localhost:8000/auth/login',
          formData,
          {
            headers: {
              'Content-Type': 'multipart/form-data'
            }
          }
        );
      } else {
        // Для регистрации обычный JSON
        response = await axios.post(
          'http://localhost:8000/auth/register',
          {
            email: formData.email,
            password: formData.password,
            username: formData.username
          }
        );
      }

      // Обрабатываем успешный ответ
      if (isLoginMode) {
        onLogin({
          user: response.data.user,
          token: response.data.access_token // исправлено с data.token
        });
      } else {
        // После регистрации автоматически логиним пользователя
        const loginResponse = await axios.post(
          'http://localhost:8000/auth/login',
          new URLSearchParams({
            username: formData.email,
            password: formData.password
          }),
          {
            headers: {
              'Content-Type': 'application/x-www-form-urlencoded'
            }
          }
        );
        
        onLogin({
          user: loginResponse.data.user,
          token: loginResponse.data.access_token
        });
      }
      
      onClose();
    } catch (err) {
      console.error('Auth error:', err);
      setError(
        err.response?.data?.detail || 
        err.message || 
        'Произошла ошибка. Проверьте введенные данные'
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="modal-overlay">
      <div className="modal">
        <button className="close-btn" onClick={onClose}>×</button>
        <h2>{isLoginMode ? 'Вход' : 'Регистрация'}</h2>
        
        {error && <div className="error">{error}</div>}

        <form onSubmit={handleSubmit}>
          {!isLoginMode && (
            <input
              type="text"
              name="username"
              placeholder="Имя пользователя"
              value={formData.username}
              onChange={handleChange}
              required
              minLength={3}
            />
          )}
          
          <input
            type="email"
            name="email"
            placeholder="Email"
            value={formData.email}
            onChange={handleChange}
            required
          />
          
          <input
            type="password"
            name="password"
            placeholder="Пароль"
            value={formData.password}
            onChange={handleChange}
            required
            minLength={8}
          />
          
          <button 
            type="submit" 
            disabled={isLoading}
            className={isLoading ? 'loading' : ''}
          >
            {isLoading ? (
              'Загрузка...'
            ) : isLoginMode ? (
              'Войти'
            ) : (
              'Зарегистрироваться'
            )}
          </button>
        </form>

        <button 
          className="switch-mode-btn"
          onClick={switchMode} // Исправлено с onClose
        >
          {isLoginMode ? 'Нет аккаунта? Зарегистрироваться' : 'Уже есть аккаунт? Войти'}
        </button>
      </div>
    </div>
  );
}