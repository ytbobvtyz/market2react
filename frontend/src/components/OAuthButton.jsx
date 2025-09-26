import React from 'react';
import './OAuthButton.css';

const OAuthButton = ({ provider, onSuccess, onError }) => {
  const getOAuthUrl = () => {
    // Приоритеты для определения URL:
    // 1. Переменная окружения VITE_API_URL
    // 2. Текущий origin (для production)
    // 3. Локальный хост (fallback)
    
    const envApiUrl = import.meta.env.VITE_API_URL;
    
    if (envApiUrl) {
      return `${envApiUrl}/api/oauth/${provider}`;
    }
    
    if (window.location.origin.includes('localhost')) {
      // Development
      return `http://localhost:8000/api/oauth/${provider}`;
    } else {
      // Production
      return `${window.location.origin}/api/oauth/${provider}`;
    }
  };

  const handleOAuthLogin = async () => {
    try {
      const oauthUrl = getOAuthUrl();
      
      // Валидация URL
      if (!oauthUrl.startsWith('http')) {
        throw new Error(`Invalid OAuth URL: ${oauthUrl}`);
      }
      
      console.log(`🎯 OAuth redirect: ${oauthUrl}`);
      window.location.href = oauthUrl;
      
      // Optional: Call success callback after a delay
      setTimeout(() => {
        if (onSuccess) onSuccess();
      }, 100);
      
    } catch (error) {
      console.error('OAuth redirect error:', error);
      if (onError) {
        onError(`Ошибка перенаправления: ${error.message}`);
      } else {
        // Fallback error handling
        alert(`Ошибка OAuth: ${error.message}`);
      }
    }
  };

  const getButtonText = () => {
    const providers = {
      google: 'Google',
      github: 'GitHub',
      yandex: 'Yandex'
    };
    return `Войти через ${providers[provider] || provider}`;
  };

  const getIcon = () => {
    const icons = {
      google: 'G',
      github: 'G', 
      yandex: 'Y'
    };
    return icons[provider] || provider.charAt(0).toUpperCase();
  };

  return (
    <button 
      className={`oauth-btn oauth-btn-${provider}`}
      onClick={handleOAuthLogin}
      type="button"
      disabled={!provider}
    >
      <span className="oauth-icon">
        {getIcon()}
      </span>
      {getButtonText()}
    </button>
  );
};

export default OAuthButton;