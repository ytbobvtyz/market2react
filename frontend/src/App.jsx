import { useState } from 'react';
import { AuthContext } from './contexts/auth-context';
import { UserMenu } from './components/UserMenu';
import './App.css';
import axios from 'axios';


function App() {
  const [nmId, setNmId] = useState('');
  const [product, setProduct] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const handleSearch = async () => {
  const { isAuthenticated } = useContext(AuthContext);

  const handleSearch = async () => {
    if (!/^\d+$/.test(nmId)) {
      setError('Артикул должен содержать только цифры');
      return;
    }
  };

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
              {/* <h3>Характеристики:</h3>
              <ul>
                {product.characteristics.map((group, i) => (
                  <li key={i}>
                    <strong>{group.name}:</strong> {group.options.join(', ')}
                  </li>
                ))}
              </ul> */}
            </div>
            
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
      )}
    </div>
  );
}

export default App;