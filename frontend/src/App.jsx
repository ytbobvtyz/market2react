import { useState } from 'react';
import './App.css';

function App() {
  const [nmId, setNmId] = useState('');
  const [product, setProduct] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSearch = async () => {
    if (!nmId.trim()) {
      setError('Введите артикул WB');
      return;
    }

    setLoading(true);
    setError('');
    
    try {
      const response = await fetch(`http://localhost:5000/api/wb/product/${nmId.trim()}`);
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Ошибка при запросе данных');
      }
      
      const data = await response.json();
      setProduct(data);
    } catch (err) {
      setError(err.message);
      setProduct(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app">
      <h1>WB Wishlist</h1>
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
          <div className="product-images">
            {product.pics.slice(0, 3).map((pic, index) => (
              <img 
                key={index} 
                src={pic} 
                alt={`${product.name} ${index + 1}`}
                onError={(e) => e.target.src = 'https://via.placeholder.com/150'}
              />
            ))}
          </div>
          
          <div className="product-info">
            <h2>{product.name}</h2>
            <p><strong>Бренд:</strong> {product.brand}</p>
            <p><strong>Цена:</strong> {Math.floor(product.price / 100)} ₽</p>
            <p><strong>Рейтинг товара:</strong> {product.rating || 'нет данных'}</p>
            <p><strong>Рейтинг продавца:</strong> {product.sellerRating || 'нет данных'}</p>
            <p><strong>Отзывы:</strong> {product.feedbacks || 0}</p>
            
            <div className="characteristics">
              <h3>Характеристики:</h3>
              <ul>
                {product.characteristics.map((group, i) => (
                  <li key={i}>
                    <strong>{group.name}:</strong> {group.options.join(', ')}
                  </li>
                ))}
              </ul>
            </div>
            
            <a 
              href={`https://www.wildberries.ru/catalog/${product.nmId}/detail.aspx`}
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