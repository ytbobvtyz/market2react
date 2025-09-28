import React, { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';

const TelegramAuth = () => {
  const [searchParams] = useSearchParams();
  const [telegramUser, setTelegramUser] = useState(null);
  const [status, setStatus] = useState('loading');
  const [isTelegramWebApp, setIsTelegramWebApp] = useState(false);

  // Получаем корректные URL из переменных окружения
  const API_URL = import.meta.env.VITE_API_URL || 'https://wblist.ru';
  const FRONTEND_URL = import.meta.env.VITE_FRONTEND_URL || 'https://wblist.ru';

  useEffect(() => {
    const initTelegramAuth = () => {
      if (window.Telegram?.WebApp) {
        setIsTelegramWebApp(true);
        const tg = window.Telegram.WebApp;
        tg.expand();
        tg.ready();
        
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
      
      console.log('🔐 Отправляем данные в бота:', data);
      
      try {
        window.Telegram.WebApp.sendData(JSON.stringify(data));
        setTimeout(() => {
          window.Telegram.WebApp.close();
        }, 500);
      } catch (error) {
        console.error('Ошибка отправки данных в бота:', error);
        document.body.innerHTML = `
          <div style="padding: 40px; text-align: center;">
            <h2>✅ Аккаунт привязан!</h2>
            <p>Возвращайтесь в бота для продолжения.</p>
            <button onclick="window.close()" style="padding: 10px 20px; background: #007bff; color: white; border: none; border-radius: 5px;">
              Закрыть
            </button>
          </div>
        `;
      }
    }
  };

  const startGoogleOAuth = () => {
    // Создаем корректный OAuth URL
    let oauthUrl = `${API_URL}/oauth/google?source=telegram`;
    
    // Добавляем Telegram данные если есть
    if (telegramUser) {
      oauthUrl += `&tg_id=${telegramUser.id}&tg_username=${telegramUser.username}`;
    }
    
    console.log('🔗 Переход по OAuth URL:', oauthUrl);
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
        
        <div style={{ marginTop: '20px' }}>
          <a 
            href="https://t.me/wishbenefitbot" 
            target="_blank" 
            rel="noopener noreferrer"
            style={{
              display: 'inline-block',
              padding: '10px 20px',
              backgroundColor: '#0088cc',
              color: 'white',
              textDecoration: 'none',
              borderRadius: '5px',
              marginRight: '10px'
            }}
          >
            📲 Открыть бота
          </a>
          
          <button 
            onClick={() => window.location.href = FRONTEND_URL}
            style={{
              padding: '10px 20px',
              backgroundColor: '#6c757d',
              color: 'white',
              border: 'none',
              borderRadius: '5px',
              cursor: 'pointer'
            }}
          >
            Вернуться на главную
          </button>
        </div>
      </div>
    );
  }

  if (status === 'loading') {
    return (
      <div style={{ 
        padding: '40px', 
        textAlign: 'center',
        fontFamily: 'Arial, sans-serif' 
      }}>
        <h2>⏳ Загрузка...</h2>
        <p>Инициализация Telegram Web App</p>
      </div>
    );
  }

  return (
    <div style={{ 
      padding: '20px', 
      fontFamily: 'Arial, sans-serif',
      maxWidth: '500px',
      margin: '0 auto'
    }}>
      <h2 style={{ textAlign: 'center', marginBottom: '30px' }}>
        🔐 Привязка аккаунта
      </h2>
      
      {telegramUser && (
        <div style={{ 
          marginBottom: '30px',
          padding: '15px',
          backgroundColor: '#f8f9fa',
          borderRadius: '8px',
          textAlign: 'center'
        }}>
          <p style={{ margin: '0 0 10px 0', fontSize: '18px' }}>
            Привет, <strong>{telegramUser.first_name}</strong>! 👋
          </p>
          <p style={{ margin: 0, color: '#666' }}>
            Для доступа к функциям бота привяжите ваш аккаунт
          </p>
        </div>
      )}
      
      <div style={{ textAlign: 'center' }}>
        <button 
          onClick={startGoogleOAuth}
          style={{
            padding: '15px 30px',
            backgroundColor: '#4285f4',
            color: 'white',
            border: 'none',
            borderRadius: '8px',
            cursor: 'pointer',
            fontSize: '16px',
            fontWeight: 'bold',
            width: '100%',
            maxWidth: '300px',
            marginBottom: '15px'
          }}
        >
          📧 Войти через Google
        </button>
        
        <p style={{ fontSize: '14px', color: '#666', marginTop: '20px' }}>
          После авторизации вы автоматически вернетесь в бота
        </p>
      </div>
    </div>
  );
};

export default TelegramAuth;