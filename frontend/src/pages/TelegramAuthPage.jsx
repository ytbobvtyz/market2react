// frontend/src/pages/TelegramAuthPage.jsx
import React from 'react';
import TelegramAuth from '../components/TelegramAuth';

const TelegramAuthPage = () => {
  return (
    <div style={{ minHeight: '100vh', background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}>
      <TelegramAuth />
    </div>
  );
};

export default TelegramAuthPage;