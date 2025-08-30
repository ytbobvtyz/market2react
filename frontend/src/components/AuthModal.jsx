import { useState } from 'react';
import { setAuthToken } from '../api/apiService';
import axios from 'axios';
import './AuthModal.css';

export function AuthModal({ isLoginMode, onClose, onLogin, switchMode }) {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    username: ''
  });
  const [errors, setErrors] = useState({}); // Меняем на объект для множественных ошибок
  const [isLoading, setIsLoading] = useState(false);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData({
      ...formData,
      [name]: value
    });
    
    // Очищаем ошибку для этого поля при изменении
    if (errors[name] || errors.general) {
      setErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[name];
        delete newErrors.general;
        return newErrors;
      });
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setErrors({}); // Очищаем все ошибки

    try {
      let response;
      
      if (isLoginMode) {
        // Логин
        const params = new URLSearchParams();
        params.append('username', formData.email);
        params.append('password', formData.password);

        response = await axios.post(
          'http://localhost:8000/auth/login',
          params.toString(),
          {
            headers: {
              'Content-Type': 'application/x-www-form-urlencoded'
            }
          }
        );
      } else {
        // Регистрация
        response = await axios.post(
          'http://localhost:8000/auth/register',
          {
            email: formData.email,
            password: formData.password,
            username: formData.username
          }, 
          {
            headers: {
              'Content-Type': 'application/json'
            }
          }
        );
      }

      // Обрабатываем успешный ответ
      if (isLoginMode) {
        setAuthToken(response.data.access_token);
        onLogin({
          user: response.data.user,
          token: response.data.access_token
        });
      } else {
        // После регистрации автоматически логинимся
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
        
        setAuthToken(loginResponse.data.access_token);
        onLogin({
          user: loginResponse.data.user,
          token: loginResponse.data.access_token
        });
      }
      
      onClose();
      
    } catch (err) {
      console.error('Auth error:', err);
      
      // Обработка разных типов ошибок
      if (err.response?.status === 422) {
        // Ошибки валидации от Pydantic
        const errorDetail = err.response.data.detail;
        
        if (typeof errorDetail === 'string') {
          // Одна ошибка (например, для пароля)
          setErrors({ password: errorDetail });
        } else if (Array.isArray(errorDetail)) {
          // Несколько ошибок валидации
          const validationErrors = {};
          errorDetail.forEach(error => {
            const field = error.loc[error.loc.length - 1]; // Берем последний элемент loc
            validationErrors[field] = error.msg;
          });
          setErrors(validationErrors);
        }
        
      } else if (err.response?.status === 400) {
        // Пользователь уже существует или другие бизнес-ошибки
        setErrors({ general: err.response.data.detail });
        
      } else if (err.response?.status === 401) {
        // Неверные учетные данные
        setErrors({ general: 'Неверный email или пароль' });
        
      } else if (err.code === 'NETWORK_ERROR') {
        // Проблемы с сетью
        setErrors({ general: 'Ошибка сети. Проверьте подключение' });
        
      } else {
        // Любая другая ошибка
        setErrors({ 
          general: err.response?.data?.detail || 
                  err.message || 
                  'Произошла ошибка. Проверьте введенные данные' 
        });
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="modal-overlay">
      <div className="modal">
        <button className="close-btn" onClick={onClose}>×</button>
        <h2>{isLoginMode ? 'Вход' : 'Регистрация'}</h2>
        
        {/* Общая ошибка */}
        {errors.general && (
          <div className="error general-error">
            {errors.general}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          {!isLoginMode && (
            <div className="input-group">
              <input
                type="text"
                name="username"
                placeholder="Имя пользователя"
                value={formData.username}
                onChange={handleChange}
                required
                minLength={3}
                className={errors.username ? 'error-input' : ''}
              />
              {errors.username && (
                <span className="error-text">{errors.username}</span>
              )}
            </div>
          )}
          
          <div className="input-group">
            <input
              type="email"
              name="email"
              placeholder="Email"
              value={formData.email}
              onChange={handleChange}
              required
              className={errors.email ? 'error-input' : ''}
            />
            {errors.email && (
              <span className="error-text">{errors.email}</span>
            )}
          </div>
          
          <div className="input-group">
            <input
              type="password"
              name="password"
              placeholder="Пароль"
              value={formData.password}
              onChange={handleChange}
              required
              minLength={8}
              className={errors.password ? 'error-input' : ''}
            />
            {errors.password && (
              <span className="error-text">{errors.password}</span>
            )}
            
            {/* Подсказки для пароля при регистрации */}
            {!isLoginMode && (
              <div className="password-hints">
                <p>Пароль должен содержать:</p>
                <ul>
                  <li>• Минимум 8 символов</li>
                  <li>• Заглавную и строчную буквы</li>
                  <li>• Цифру</li>
                  <li>• Специальный символ</li>
                </ul>
              </div>
            )}
          </div>
          
          <button 
            type="submit" 
            disabled={isLoading}
            className={`submit-btn ${isLoading ? 'loading' : ''}`}
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
          onClick={switchMode}
          type="button"
        >
          {isLoginMode ? 'Нет аккаунта? Зарегистрироваться' : 'Уже есть аккаунт? Войти'}
        </button>
      </div>
    </div>
  );
}