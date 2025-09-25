import React, { useEffect, useContext } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { AuthContext } from '../contexts/auth-context';
import { api, setAuthToken } from '../api/apiService';

const OAuthSuccess = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { login } = useContext(AuthContext);

  useEffect(() => {
    const handleOAuthCallback = async () => {
      const token = searchParams.get('token');
      const error = searchParams.get('error');
      const message = searchParams.get('message');

      if (error) {
        console.error('OAuth error:', message);
        alert(`Ошибка OAuth: ${message || 'Неизвестная ошибка'}`);
        navigate('/');
        return;
      }

      if (token) {
        try {
          console.log('🔑 Processing OAuth token...');
          
          // Сохраняем токен
          localStorage.setItem('access_token', token);
          setAuthToken(token);
          
          // Получаем данные пользователя
          const response = await api.get('/auth/me');
          console.log('✅ User data received:', response.data);
          
          login(response.data);
          
          // Перенаправляем на главную
          navigate('/');
          
        } catch (error) {
          console.error('OAuth processing error:', error);
          alert('Ошибка обработки OAuth токена');
          navigate('/');
        }
      } else {
        console.error('No token received');
        navigate('/');
      }
    };

    handleOAuthCallback();
  }, [searchParams, navigate, login]);

  return (
    <div style={{ padding: '50px', textAlign: 'center' }}>
      <h2>🔐 Обработка входа...</h2>
      <p>Пожалуйста, подождите.</p>
    </div>
  );
};

export default OAuthSuccess;