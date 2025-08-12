import { useState, useContext } from 'react';
import { AuthContext } from './contexts/auth-context';
import { UserMenu } from './components/UserMenu';
import './App.css';
import axios from 'axios';

function App() {
  const [nmId, setNmId] = useState('');
  const [product, setProduct] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const { isAuthenticated, user, login } = useContext(AuthContext);
  const [saveStatus, setSaveStatus] = useState('');

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
      return;
    }

    try {
      setSaveStatus('Сохранение...');
      await axios.post('http://localhost:8000/saved-requests/', {
        user_id: user.id,
        nm_id: nmId,
        product_data: product
      });
      setSaveStatus('Запрос сохранён!');
    } catch (err) {
      setSaveStatus('Ошибка сохранения');
      console.error(err);
    }
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1>WishBenefit</h1>
        <UserMenu />
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
                disabled={!!saveStatus}
              >
                {saveStatus || 'Сохранить мой запрос'}
              </button>
              
              <a 
                href={`https://www.wildberries.ru/catalog/${nmId}/detail.aspx`}
                target="_blank"
                rel="noopener noreferrer"
                className="wb-link"
              >
                Открыть на Wildberries
              </a>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;