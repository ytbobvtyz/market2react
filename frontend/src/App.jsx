import { useState, useContext, useEffect } from 'react';
import { AuthContext } from './contexts/auth-context';
import { UserMenu } from './components/UserMenu';
import { AuthModal } from './components/AuthModal';
import { parsingService } from './api/parsingService';
import { setAuthToken } from './api/apiService'; // Добавляем импорт
import './App.css';
import axios from 'axios';

// Настройка интерцепторов axios
const setupAxiosInterceptors = () => {
  axios.interceptors.request.use(config => {
    const token = localStorage.getItem('access_token'); // Меняем на access_token
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  });

  axios.interceptors.response.use(
    response => response,
    error => {
      if (error.response?.status === 401) {
        localStorage.removeItem('access_token'); // Меняем на access_token
        // Можно добавить редирект или обновление состояния
      }
      return Promise.reject(error);
    }
  );
};

function App() {
  const [nmId, setNmId] = useState('');
  const [product, setProduct] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const { isAuthenticated, user, login: authLogin } = useContext(AuthContext);
  const [saveStatus, setSaveStatus] = useState('');
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
  const [isLoginMode, setIsLoginMode] = useState(true);
  const [parsingLoading, setParsingLoading] = useState(false);

  useEffect(() => {
    setupAxiosInterceptors();
    
    const token = localStorage.getItem('access_token');
    if (token && !isAuthenticated) {
      const loadUser = async () => {
        try {
          const response = await axios.get('http://localhost:8000/auth/me', {
            headers: {
              Authorization: `Bearer ${token}`
            }
          });
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

  const handleSearch = async () => {
    if (!/^\d+$/.test(nmId)) {
      setError('Артикул должен содержать только цифры');
      return;
    }

    setLoading(true);
    setError('');
    
    try {
      const { data } = await axios.get(`http://localhost:8000/products/${nmId}`);
      setProduct(data);
      // Сохраняем данные в localStorage для последующего использования
      localStorage.setItem('searchData', JSON.stringify([data]));
      localStorage.setItem('query', nmId);

    } catch (err) {
      setError(err.response?.data?.detail || 
        err.message === 'Network Error' ? 'Сервер недоступен' : 'Ошибка запроса');
      setProduct(null);
    } finally {
      setLoading(false);
    }
  };

  const handleSaveRequest = async () => {
    if (!isAuthenticated) {
      setSaveStatus('Для сохранения необходимо авторизоваться');
      setIsAuthModalOpen(true);
      return;
    }

    setParsingLoading(true);
    try {
      // Получаем данные из localStorage
      const searchData = localStorage.getItem('searchData');
      const query = localStorage.getItem('query');
      
      if (!searchData || !query) {
        alert('Нет данных для сохранения. Сначала выполните поиск.');
        return;
      }

      const results = JSON.parse(searchData);
      
      // Сохраняем в базу данных через наш сервис
      const saveResult = await parsingService.saveParsingResults(query, results);
      
      
      alert(`Данные сохранены! Сохранено товаров: ${saveResult.details.saved_count}`);
      
    } catch (error) {
      console.error('Error:', error);
      
      // Если ошибка авторизации
      if (error.response?.status === 401) {
        alert('Сессия истекла. Пожалуйста, войдите снова.');
        localStorage.removeItem('access_token'); // Меняем на access_token
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
        <h1>WishBenefit</h1>
        <UserMenu onLoginClick={() => setIsAuthModalOpen(true)} />
      </header>

      <div className="search-form">
        <input
          type="text"
          value={nmId}
          onChange={(e) => setNmId(e.target.value)}
          placeholder="Введите артикул WB"
          disabled={loading}
        />
        <button onClick={handleSearch} disabled={loading}>
          {loading ? 'Поиск...' : 'Найти'}
        </button>
      </div>

      {error && <div className="error">{error}</div>}

      {product && (
        <div className="product-card">
          <div className="product-info">
            <h2>{product.name}</h2>
            <p><strong>Бренд:</strong> {product.brand}</p>
            <p><strong>Цена:</strong> {Math.floor(product.price)} ₽</p>
            <p><strong>Рейтинг товара:</strong> {product.rating || 'нет данных'}</p>
            <p><strong>Количество отзывов:</strong> {product.feedback_count || 'нет данных'}</p>
            <div className="characteristics">
              {/* Характеристики */}
            </div>
            <div className="product-actions">
              <button 
                onClick={handleSaveRequest}
                className="save-request-btn"
                disabled={parsingLoading} // Меняем условие disabled
              >
                {parsingLoading ? 'Сохранение...' : 'Сохранить запрос'}
              </button>
              
              <a 
                href={`https://www.wildberries.ru/catalog/${nmId}/detail.aspx`}
                target="_blank"
                rel="noopener noreferrer"
                className="wb-link"
              >
                Открыть на WB
              </a>
            </div>
          </div>
        </div>
      )}
      
      {/* Модальное окно авторизации */}
      {isAuthModalOpen && (
        <AuthModal
          isLoginMode={isLoginMode}
          onClose={() => setIsAuthModalOpen(false)}
          onLogin={handleLoginSuccess}
          switchMode={() => setIsLoginMode(!isLoginMode)}
        />
      )}
    </div>
  );
}

export default App;