import React from 'react';
import { useNavigate } from 'react-router-dom';

const TelegramAuthWrapper = () => {
  const navigate = useNavigate();

  // Проверяем, находимся ли мы в Telegram Web App
  const isTelegramWebApp = typeof window !== 'undefined' && window.Telegram?.WebApp;

  React.useEffect(() => {
    if (!isTelegramWebApp) {
      // Если не в Telegram, перенаправляем на главную
      navigate('/');
      return;
    }
  }, [isTelegramWebApp, navigate]);

  if (!isTelegramWebApp) {
    return (
      <div style={{ padding: '40px', textAlign: 'center' }}>
        <p>Перенаправление...</p>
      </div>
    );
  }

  // Динамически загружаем компонент только когда он нужен
  const TelegramAuth = React.lazy(() => import('./TelegramAuth'));

  return (
    <React.Suspense fallback={<div>Загрузка Telegram Auth...</div>}>
      <TelegramAuth />
    </React.Suspense>
  );
};

export default TelegramAuthWrapper;