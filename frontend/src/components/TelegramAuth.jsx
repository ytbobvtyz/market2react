import React, { useEffect } from 'react';

const TelegramAuth = ({ onAuth, botUsername = "WishbenefitBot" }) => {
  useEffect(() => {
    // Загружаем Telegram Widget script
    const script = document.createElement('script');
    script.src = "https://telegram.org/js/telegram-widget.js?22";
    script.async = true;
    script.setAttribute('data-telegram-login', botUsername);
    script.setAttribute('data-size', 'large');
    script.setAttribute('data-request-access', 'write');
    script.setAttribute('data-onauth', 'onTelegramAuth(user)');
    
    document.body.appendChild(script);
    
    // Глобальная функция для обработки авторизации
    window.onTelegramAuth = (userData) => {
      onAuth(userData);
    };
    
    return () => {
      document.body.removeChild(script);
      delete window.onTelegramAuth;
    };
  }, [botUsername, onAuth]);

  return (
    <div 
      id="telegram-auth" 
      className="telegram-auth-btn"
      style={{ cursor: 'pointer' }}
    >
      {/* Кнопка будет вставлена Telegram Widget */}
    </div>
  );
};

export default TelegramAuth;