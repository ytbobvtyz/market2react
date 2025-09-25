import React, { useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';

const OAuthCallback = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  useEffect(() => {
    const handleCallback = async () => {
      const code = searchParams.get('code');
      const error = searchParams.get('error');

      if (error) {
        console.error('OAuth error:', error);
        navigate('/?oauth_error=1');
        return;
      }

      if (code) {
        try {
          // Отправляем код на бэкенд для обмена на токен
          const response = await fetch('http://localhost:8000/oauth/google/callback', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({ code })
          });

          if (response.ok) {
            const data = await response.json();
            localStorage.setItem('access_token', data.access_token);
            navigate('/'); // Успешный вход
          } else {
            throw new Error('Failed to exchange code for token');
          }
        } catch (error) {
          console.error('Callback error:', error);
          navigate('/?oauth_error=1');
        }
      }
    };

    handleCallback();
  }, [searchParams, navigate]);

  return (
    <div style={{ padding: '20px', textAlign: 'center' }}>
      <h2>Обработка входа...</h2>
      <p>Пожалуйста, подождите.</p>
    </div>
  );
};

export default OAuthCallback;