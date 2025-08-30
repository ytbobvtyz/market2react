import { useState } from 'react';
import { setAuthToken } from '../api/apiService';
import axios from 'axios';
import './AuthModal.css';

export function AuthModal({ isLoginMode, onClose, onLogin, switchMode }) {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    username: '',
    verificationCode: ''
  });
  const [errors, setErrors] = useState({});
  const [isLoading, setIsLoading] = useState(false);
  const [verificationSent, setVerificationSent] = useState(false);
  const [verificationLoading, setVerificationLoading] = useState(false);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData({
      ...formData,
      [name]: value
    });
    
    // Очищаем ошибку для этого поля при изменении
    if (errors[name]) {
      setErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[name];
        return newErrors;
      });
    }
  };

  const handleSendVerification = async () => {
    if (!formData.email) {
      setErrors({ email: 'Введите email' });
      return;
    }

    setVerificationLoading(true);
    setErrors({});

    try {
      await axios.post('http://localhost:8000/auth/send-verification-code', {
        email: formData.email
      });

      setVerificationSent(true);
      alert('Код подтверждения отправлен на ваш email!');

    } catch (error) {
      console.error('Verification error:', error);
      setErrors({ 
        email: error.response?.data?.detail || 'Ошибка отправки кода' 
      });
    } finally {
      setVerificationLoading(false);
    }
  };

  const handleLogin = async () => {
    try {
      const params = new URLSearchParams();
      params.append('username', formData.email);
      params.append('password', formData.password);

      const response = await axios.post(
        'http://localhost:8000/auth/login',
        params.toString(),
        {
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
          }
        }
      );

      setAuthToken(response.data.access_token);
      onLogin({
        user: response.data.user,
        token: response.data.access_token
      });
      onClose();

    } catch (error) {
      console.error('Login error:', error);
      if (error.response?.status === 401) {
        setErrors({ general: 'Неверный email или пароль' });
      } else {
        setErrors({ 
          general: error.response?.data?.detail || 'Ошибка входа' 
        });
      }
    }
  };

  const handleRegister = async () => {
    try {
      // Сначала регистрируем
      const response = await axios.post(
        'http://localhost:8000/auth/register-with-verification',
        {
          username: formData.username,
          email: formData.email,
          password: formData.password,
          verification_code: formData.verificationCode
        }, 
        {
          headers: {
            'Content-Type': 'application/json'
          }
        }
      );

      // Затем автоматически логинимся
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
      onClose();

    } catch (error) {
      console.error('Register error:', error);
      if (error.response?.status === 400) {
        setErrors({ 
          general: error.response.data.detail || 'Ошибка регистрации' 
        });
      } else {
        setErrors({ 
          general: 'Ошибка регистрации. Проверьте введенные данные.' 
        });
      }
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setErrors({});

    try {
      if (isLoginMode) {
        await handleLogin();
      } else {
        await handleRegister();
      }
    } catch (error) {
      console.error('Auth error:', error);
      setErrors({ 
        general: 'Произошла ошибка. Попробуйте еще раз.' 
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="modal-overlay">
      <div className="modal">
        <button className="close-btn" onClick={onClose}>×</button>
        <h2>{isLoginMode ? 'Вход' : 'Регистрация'}</h2>
        
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
              disabled={verificationSent && !isLoginMode}
              className={errors.email ? 'error-input' : ''}
            />
            {errors.email && (
              <span className="error-text">{errors.email}</span>
            )}
            
            {!isLoginMode && !verificationSent && (
              <button
                type="button"
                onClick={handleSendVerification}
                disabled={verificationLoading}
                className="verify-btn"
              >
                {verificationLoading ? 'Отправка...' : 'Отправить код'}
              </button>
            )}
          </div>

          {!isLoginMode && verificationSent && (
            <div className="input-group">
              <input
                type="text"
                name="verificationCode"
                placeholder="Код подтверждения из email"
                value={formData.verificationCode}
                onChange={handleChange}
                required
                maxLength={6}
                className={errors.verificationCode ? 'error-input' : ''}
              />
              <div className="code-hint">
                Код отправлен на {formData.email}
              </div>
            </div>
          )}
          
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
            disabled={isLoading || (!isLoginMode && !verificationSent)}
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