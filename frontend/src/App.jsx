import { useState, useContext, useEffect } from 'react';
import { Routes, Route, useNavigate } from 'react-router-dom';
import { AuthContext } from './contexts/auth-context';
import { UserMenu } from './components/UserMenu';
import { AuthModal } from './components/AuthModal';
import { PriceModal } from './components/PriceModal';
import { TrackingHistory } from './pages/TrackingHistory';
import { parsingService } from './api/parsingService';
import { setAuthToken } from './api/apiService';
import './App.css';
import { api } from './api/apiService';
import OAuthCallback from './pages/OAuthCallback';
import OAuthSuccess from './pages/OAuthSuccess';
import TelegramAuthWrapper from './components/TelegramAuthWrapper';

const setupAxiosInterceptors = () => {
  api.interceptors.request.use(config => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  });

  api.interceptors.response.use(
    response => response,
    error => {
      if (error.response?.status === 401) {
        localStorage.removeItem('access_token');
      }
      return Promise.reject(error);
    }
  );
};

function MainApp() {
  const [nmId, setNmId] = useState('');
  const [product, setProduct] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const { isAuthenticated, user, login: authLogin } = useContext(AuthContext);
  const [saveStatus, setSaveStatus] = useState('');
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
  const [isLoginMode, setIsLoginMode] = useState(true);
  const [parsingLoading, setParsingLoading] = useState(false);
  const [isPriceModalOpen, setIsPriceModalOpen] = useState(false);
  const [targetPrice, setTargetPrice] = useState(null);
  const [customName, setCustomName] = useState('');
  const [searchProgress, setSearchProgress] = useState(0);
  const navigate = useNavigate();
  
  useEffect(() => {
    setupAxiosInterceptors();
    
    const token = localStorage.getItem('access_token');
    if (token && !isAuthenticated) {
      const loadUser = async () => {
        try {
          const response = await api.get('/auth/me');
          authLogin(response.data);
        } catch (error) {
          console.error('Failed to load user', error);
          localStorage.removeItem('access_token');
        }
      };
      
      loadUser();
    }
  }, [isAuthenticated, authLogin]);

  const handleLoginSuccess = ({ user, token }) => {
    setAuthToken(token);
    authLogin(user);
    setIsAuthModalOpen(false);
  };

  const handleHistoryClick = () => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      alert('Для просмотра истории необходимо авторизоваться');
      setIsAuthModalOpen(true);
    } else {
      navigate('/history');
    }
  };

  const handleSearch = async () => {
    if (!/^\d+$/.test(nmId)) {
      setError('Артикул должен содержать только цифры');
      return;
    }

    setLoading(true);
    setError('');
    setSearchProgress(0);
    
    const progressInterval = setInterval(() => {
      setSearchProgress(prev => {
        if (prev >= 95) return 95;
        return prev + 5;
      });
    }, 1000);

    try {
      console.log('Начинаем парсинг товара:', nmId);
      
      const { data } = await api.get(`/api/products/${nmId}`, {
        timeout: 180000
      });
      
      clearInterval(progressInterval);
      setSearchProgress(100);
      
      console.log('✅ Парсинг завершен:', data);
      setProduct(data);
      localStorage.setItem('searchData', JSON.stringify([data]));
      localStorage.setItem('query', nmId);
      
      setTimeout(() => setSearchProgress(0), 2000);
      
    } catch (err) {
      clearInterval(progressInterval);
      setSearchProgress(0);
      
      console.error('❌ Ошибка парсинга:', err);
      
      if (err.code === 'ECONNABORTED') {
        setError('Парсинг занял слишком много времени. Попробуйте еще раз.');
      } else if (err.message === 'Network Error') {
        setError('Сервер недоступен. Проверьте соединение.');
      } else if (err.response?.status === 504) {
        setError('Сервер занят. Попробуйте через минуту.');
      } else {
        setError(err.response?.data?.detail || 'Ошибка запроса. Попробуйте еще раз.');
      }
      
      setProduct(null);
    } finally {
      setLoading(false);
    }
  };

  const handleSaveClick = () => {
    if (!isAuthenticated) {
      setSaveStatus('Для сохранения необходимо авторизоваться');
      setIsAuthModalOpen(true);
      return;
    }
    
    setIsPriceModalOpen(true);
  };

  const handlePriceConfirm = async (price, name) => {
    setTargetPrice(price);
    setCustomName(name);
    setParsingLoading(true);
    
    try {
      const searchData = localStorage.getItem('searchData');
      const query = localStorage.getItem('query');
      
      if (!searchData || !query) {
        alert('Нет данных для сохранения. Сначала выполните поиск.');
        return;
      }

      const results = JSON.parse(searchData);
      
      const saveData = {
        query,
        results,
        target_price: price,
        custom_name: name
      };
      
      const saveResult = await parsingService.saveParsingResults(saveData);
      
      alert(`Данные сохранены! Уведомление придёт на почту при достижении цены ${price} ₽`);
      
    } catch (error) {
      console.error('Error:', error);
      
      if (error.response?.status === 401) {
        alert('Сессия истекла. Пожалуйста, войдите снова.');
        localStorage.removeItem('access_token');
        window.location.reload();
      } else {
        alert(error.message || 'Ошибка при сохранении данных');
      }
    } finally {
      setParsingLoading(false);
    }
  };

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-content">
          <div className="header-title">
            <h1>Wish Benefit List</h1>
            <p>Следи за изменением цен и получай выгоду</p>
          </div>
          <div className="header-actions">
            <button onClick={handleHistoryClick} className="history-btn">
              Мой список отслеживания
            </button>
            <UserMenu onLoginClick={() => setIsAuthModalOpen(true)} />
          </div>
        </div>
      </header>

      <main className="main-content">
        <div className="search-container">
          <h2 className="search-title">Найди свой товар на Wildberries</h2>
          <div className="search-form">
            <input
              type="text"
              value={nmId}
              onChange={(e) => setNmId(e.target.value)}
              placeholder="Введите артикул товара WB"
              disabled={loading}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            />
            
            {loading ? (
              <div className="progress-indicator">
                <div className="progress-bar-container">
                  <div 
                    className="progress-bar" 
                    style={{ width: `${searchProgress}%` }}
                  ></div>
                </div>
                <span>Поиск товара... {searchProgress}%</span>
              </div>
            ) : (
              <button onClick={handleSearch} className="search-btn">
                Найти
              </button>
            )}
          </div>
        </div>

        {error && <div className="error-message">{error}</div>}

        {product && (
          <div className="product-card">
            <div className="product-header">
              <h3>{product.name}</h3>
              <div className="product-badge">
                <span className="brand">{product.brand}</span>
              </div>
            </div>
            
            <div className="product-stats">
              <div className="stat-item">
                <span className="stat-label">Цена:</span>
                <span className="stat-value price">{Math.floor(product.price)} ₽</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">Рейтинг:</span>
                <span className="stat-value rating">{product.rating || 'нет данных'}</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">Отзывы:</span>
                <span className="stat-value feedback">{product.feedback_count || 'нет данных'}</span>
              </div>
            </div>

            <div className="product-actions">
              <button 
                onClick={handleSaveClick}
                className="save-request-btn"
                disabled={parsingLoading}
              >
                {parsingLoading ? '💾 Сохранение...' : '💾 Сохранить запрос'}
              </button>
              
              <a 
                href={`https://www.wildberries.ru/catalog/${nmId}/detail.aspx`}
                target="_blank"
                rel="noopener noreferrer"
                className="wb-link"
              >
                📱 Открыть на WB
              </a>
            </div>
          </div>
        )}
      </main>
      
      {isAuthModalOpen && (
        <AuthModal
          isLoginMode={isLoginMode}
          onClose={() => setIsAuthModalOpen(false)}
          onLogin={handleLoginSuccess}
          switchMode={() => setIsLoginMode(!isLoginMode)}
        />
      )}
      
      <PriceModal
        isOpen={isPriceModalOpen}
        onClose={() => setIsPriceModalOpen(false)}
        onConfirm={handlePriceConfirm}
        currentPrice={product?.price}
        productName={product?.name} 
      />
    </div>
  );
}

function App() {
  return (
    <Routes>
      <Route path="/" element={<MainApp />} />      
      <Route path="/history" element={<TrackingHistory />} />
      <Route path="/oauth/callback" element={<OAuthCallback />} />
      <Route path="/oauth/success" element={<OAuthSuccess />} />
      <Route path="/telegram-auth" element={<TelegramAuthWrapper />} />
      {/* <Route path="/telegram-auth" element={<TelegramAuthPage />} /> */}
    </Routes>
  );
}

export default App;