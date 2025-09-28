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

  // Улучшенная проверка на нахождение в Telegram Web App
  const checkTelegramContext = () => {
    const tg = window.Telegram?.WebApp;
    
    // Проверяем несколько признаков Telegram Web App
    const hasWebApp = !!tg;
    const hasInitData = !!tg?.initData;
    const hasInitDataUnsafe = !!tg?.initDataUnsafe?.user;
    const hasVersion = !!tg?.version;
    
    // Проверяем параметры URL, которые Telegram передает при открытии
    const urlParams = new URLSearchParams(window.location.search);
    const hasTelegramParams = urlParams.has('tgWebAppData') || 
                             urlParams.has('tgWebAppPlatform') ||
                             urlParams.has('tgWebAppVersion');
    
    // Проверяем user agent (дополнительный признак)
    const userAgent = navigator.userAgent.toLowerCase();
    const hasTelegramUserAgent = userAgent.includes('telegram') || 
                                userAgent.includes('webview');
    
    console.log('🔍 Проверка Telegram контекста:', {
      hasWebApp,
      hasInitData,
      hasInitDataUnsafe,
      hasVersion,
      hasTelegramParams,
      hasTelegramUserAgent,
      urlParams: Object.fromEntries(urlParams.entries()),
      userAgent: navigator.userAgent
    });

    // Считаем, что мы в Telegram, если есть основные признаки
    return (hasWebApp && (hasInitData || hasInitDataUnsafe || hasVersion)) || 
           hasTelegramParams ||
           (hasWebApp && hasTelegramUserAgent);
  };

  useEffect(() => {
    const initTelegramAuth = () => {
      const inTelegram = checkTelegramContext();
      setIsTelegramWebApp(inTelegram);

      if (inTelegram && window.Telegram?.WebApp) {
        console.log('✅ Обнаружен Telegram Web App');
        const tg = window.Telegram.WebApp;
        
        // Инициализация Telegram Web App
        try {
          tg.expand();
          tg.ready();
          console.log('✅ Telegram Web App инициализирован');
        } catch (error) {
          console.error('❌ Ошибка инициализации Telegram Web App:', error);
        }
        
        // Получаем данные пользователя
        const user = tg.initDataUnsafe?.user;
        console.log('👤 Данные пользователя Telegram:', user);
        setTelegramUser(user);
        
        // Проверяем, есть ли JWT токен (после OAuth)
        const token = searchParams.get('token');
        console.log('🔑 Токен из URL:', token);
        
        if (token && user) {
          console.log('🔄 Обработка успешной OAuth авторизации');
          handleOAuthSuccess(token, user);
        } else {
          console.log('✅ Статус: готов к авторизации');
          setStatus('ready');
        }
      } else {
        console.log('❌ Не в Telegram Web App');
        setIsTelegramWebApp(false);
        setStatus('not_in_telegram');
      }
    };

    // Добавляем небольшую задержку для уверенной инициализации
    setTimeout(initTelegramAuth, 100);
  }, [searchParams]);

  const handleOAuthSuccess = (token, tgUser) => {
    console.log('🔄 Начало обработки OAuth успеха');
    
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
      
      console.log('📤 Отправляем данные в бота:', data);
      
      try {
        window.Telegram.WebApp.sendData(JSON.stringify(data));
        console.log('✅ Данные успешно отправлены в бота');
        
        setTimeout(() => {
          console.log('🔄 Закрытие Web App');
          window.Telegram.WebApp.close();
        }, 1000);
      } catch (error) {
        console.error('❌ Ошибка отправки данных в бота:', error);
        // Fallback для случаев, когда отправка не сработала
        setStatus('success');
      }
    } else {
      console.error('❌ Telegram Web App не доступен для отправки данных');
      setStatus('success');
    }
  };

  const startGoogleOAuth = () => {
    console.log('🚀 Запуск Google OAuth');
    
    // Создаем корректный OAuth URL
    let oauthUrl = `${API_URL}/oauth/google?source=telegram`;
    
    // Добавляем Telegram данные если есть
    if (telegramUser) {
      oauthUrl += `&tg_id=${telegramUser.id}&tg_username=${telegramUser.username}`;
    }
    
    // Добавляем redirect_uri для возврата в Web App
    const currentUrl = encodeURIComponent(`${FRONTEND_URL}/telegram-auth`);
    oauthUrl += `&redirect_uri=${currentUrl}`;
    
    console.log('🔗 Переход по OAuth URL:', oauthUrl);
    window.location.href = oauthUrl;
  };

  // Показываем успешное сообщение после OAuth
  if (status === 'success') {
    return (
      <div style={{ 
        padding: '40px', 
        textAlign: 'center',
        fontFamily: 'Arial, sans-serif' 
      }}>
        <h2 style={{ color: '#22c55e', marginBottom: '20px' }}>✅ Аккаунт привязан!</h2>
        <p style={{ marginBottom: '30px', fontSize: '16px' }}>
          Возвращайтесь в бота для продолжения работы.
        </p>
        <button 
          onClick={() => window.close()}
          style={{
            padding: '12px 24px',
            backgroundColor: '#0088cc',
            color: 'white',
            border: 'none',
            borderRadius: '8px',
            cursor: 'pointer',
            fontSize: '16px'
          }}
        >
          Закрыть окно
        </button>
      </div>
    );
  }

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
      margin: '0 auto',
      minHeight: '100vh',
      backgroundColor: '#f8f9fa'
    }}>
      <h2 style={{ 
        textAlign: 'center', 
        marginBottom: '30px',
        color: '#1f2937'
      }}>
        🔐 Привязка аккаунта
      </h2>
      
      {telegramUser && (
        <div style={{ 
          marginBottom: '30px',
          padding: '20px',
          backgroundColor: 'white',
          borderRadius: '12px',
          textAlign: 'center',
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
        }}>
          <p style={{ margin: '0 0 10px 0', fontSize: '18px', fontWeight: 'bold' }}>
            Привет, <strong>{telegramUser.first_name}</strong>! 👋
          </p>
          <p style={{ margin: 0, color: '#666', fontSize: '14px' }}>
            Для доступа к функциям бота привяжите ваш аккаунт
          </p>
        </div>
      )}
      
      <div style={{ 
        textAlign: 'center',
        padding: '20px',
        backgroundColor: 'white',
        borderRadius: '12px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
      }}>
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
            marginBottom: '15px',
            transition: 'background-color 0.2s'
          }}
          onMouseOver={(e) => e.target.style.backgroundColor = '#3367d6'}
          onMouseOut={(e) => e.target.style.backgroundColor = '#4285f4'}
        >
          📧 Войти через Google
        </button>
        
        <p style={{ 
          fontSize: '14px', 
          color: '#666', 
          marginTop: '20px',
          lineHeight: '1.5'
        }}>
          После авторизации вы автоматически вернетесь в бота и сможете использовать все функции отслеживания цен.
        </p>
      </div>
    </div>
  );
};

export default TelegramAuth;