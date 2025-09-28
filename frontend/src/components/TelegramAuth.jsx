import React, { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';

const TelegramAuth = () => {
  const [searchParams] = useSearchParams();
  const [telegramUser, setTelegramUser] = useState(null);
  const [status, setStatus] = useState('loading');
  const [isTelegramWebApp, setIsTelegramWebApp] = useState(false);

  useEffect(() => {
    const initTelegramAuth = () => {
      // Проверяем, что мы внутри Telegram Web App
      if (window.Telegram?.WebApp) {
        setIsTelegramWebApp(true);
        const tg = window.Telegram.WebApp;
        tg.expand();
        
        const user = tg.initDataUnsafe?.user;
        setTelegramUser(user);
        
        // Проверяем, есть ли JWT токен (после OAuth)
        const token = searchParams.get('token');
        if (token && user) {
          handleOAuthSuccess(token, user);
        } else {
          setStatus('ready');
        }
      } else {
        setIsTelegramWebApp(false);
        setStatus('not_in_telegram');
      }
    };

    initTelegramAuth();
  }, [searchParams]);

  const handleOAuthSuccess = (token, tgUser) => {
    if (window.Telegram?.WebApp) {
      const data = {
        type: 'oauth_success',
        jwt_token: token,
        telegram_user: {
          id: tgUser.id,
          username: tgUser.username,
          first_name: tgUser.first_name
        }
      };
      
      window.Telegram.WebApp.sendData(JSON.stringify(data));
      window.Telegram.WebApp.close();
    }
  };

  const startGoogleOAuth = () => {
    if (!telegramUser) return;
    
    const tgParams = `&source=telegram&tg_id=${telegramUser.id}&tg_username=${telegramUser.username}`;
    const oauthUrl = `${import.meta.env.VITE_API_URL || 'http://wblist.ru'}/oauth/google?${tgParams}`;
    window.location.href = oauthUrl;
  };

  // Если не в Telegram Web App, показываем сообщение
  if (!isTelegramWebApp) {
    return (
      <div style={{ 
        padding: '40px', 
        textAlign: 'center',
        fontFamily: 'Arial, sans-serif' 
      }}>
        <h2>📱 Telegram Auth</h2>
        <p>Эта страница доступна только внутри Telegram приложения.</p>
        <p>Откройте бота в Telegram для продолжения.</p>
        <button 
          onClick={() => window.location.href = '/'}
          style={{
            padding: '10px 20px',
            backgroundColor: '#007bff',
            color: 'white',
            border: 'none',
            borderRadius: '5px',
            cursor: 'pointer',
            marginTop: '20px'
          }}
        >
          Вернуться на главную
        </button>
      </div>
    );
  }

  if (status === 'loading') {
    return <div style={{ padding: '20px' }}>Загрузка Telegram Web App...</div>;
  }

  if (status === 'error') {
    return <div style={{ padding: '20px' }}>Ошибка загрузки Telegram Web App</div>;
  }

  return (
    <div style={{ padding: '20px', fontFamily: 'Arial, sans-serif' }}>
      <h2>🔐 Привязка Telegram аккаунта</h2>
      
      {telegramUser && (
        <div style={{ marginBottom: '20px' }}>
          <p>Привет, <strong>{telegramUser.first_name}</strong>!</p>
          <p>Для доступа к функциям бота привяжите ваш аккаунт:</p>
        </div>
      )}
      
      <div>
        <button 
          onClick={startGoogleOAuth}
          style={{
            padding: '10px 20px',
            backgroundColor: '#4285f4',
            color: 'white',
            border: 'none',
            borderRadius: '5px',
            cursor: 'pointer',
            fontSize: '16px'
          }}
        >
          Войти через Google
        </button>
      </div>
    </div>
  );
};

export default TelegramAuth;