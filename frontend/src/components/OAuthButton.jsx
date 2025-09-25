import React from 'react';
import './OAuthButton.css';

const OAuthButton = ({ provider, onSuccess, onError }) => {
  const handleOAuthLogin = async () => {
    try {
      // Перенаправление на backend OAuth endpoint
      window.location.href = `http://localhost:8000/oauth/${provider}`;
    } catch (error) {
      onError(`Ошибка OAuth: ${error.message}`);
    }
  };

  return (
    <button 
      className={`oauth-btn oauth-btn-${provider}`}
      onClick={handleOAuthLogin}
    >
      <span className="oauth-icon">
        {provider === 'google' ? 'G' : provider.charAt(0).toUpperCase()}
      </span>
      Войти через {provider === 'google' ? 'Google' : provider}
    </button>
  );
};

export default OAuthButton;