import React from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import TelegramAuth from './TelegramAuth';

const TelegramAuthWrapper = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  // Проверяем, находимся ли мы в Telegram Web App
  const isTelegramWebApp = window.Telegram?.WebApp;
  
  // Проверяем, есть ли параметры, указывающие на вызов из бота
  const hasBotParams = searchParams.get('tg_user_id') || searchParams.get('source') === 'bot';

  React.useEffect(() => {
    console.log('🔍 TelegramAuthWrapper проверка:');
    console.log('- В Telegram Web App:', isTelegramWebApp);
    console.log('- Параметры бота:', hasBotParams);
    console.log('- Все параметры:', Object.fromEntries(searchParams.entries()));
    
    // Если не в Telegram Web App И нет параметров бота - перенаправляем
    if (!isTelegramWebApp && !hasBotParams) {
      console.log('❌ Не из бота - перенаправляем на главную');
      navigate('/');
    }
  }, [isTelegramWebApp, hasBotParams, navigate, searchParams]);

  // Показываем загрузку во время проверки
  if (!isTelegramWebApp && !hasBotParams) {
    return (
      <div style={{ 
        padding: '40px', 
        textAlign: 'center',
        fontFamily: 'Arial, sans-serif' 
      }}>
        <p>Перенаправление...</p>
      </div>
    );
  }

  // Рендерим компонент авторизации
  return <TelegramAuth />;
};

export default TelegramAuthWrapper;