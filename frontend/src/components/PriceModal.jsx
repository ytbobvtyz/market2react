import { useState } from 'react';
import './PriceModal.css';

export function PriceModal({ isOpen, onClose, onConfirm, currentPrice }) {
  const [targetPrice, setTargetPrice] = useState('');

  if (!isOpen) return null;

  const handleSubmit = (e) => {
    e.preventDefault();
    const price = parseInt(targetPrice);
    if (price && price > 0) {
      onConfirm(price);
      setTargetPrice('');
      onClose();
    }
  };

  return (
    <div className="modal-overlay">
      <div className="modal price-modal">
        <button className="close-btn" onClick={onClose}>×</button>
        <h2>Уведомление о снижении цены</h2>
        
        {currentPrice && (
          <p className="current-price">
            Текущая цена: <strong>{Math.floor(currentPrice)} ₽</strong>
          </p>
        )}
        
        <form onSubmit={handleSubmit}>
          <div className="input-group">
            <label htmlFor="targetPrice">Целевая цена (рубли):</label>
            <input
              type="number"
              id="targetPrice"
              value={targetPrice}
              onChange={(e) => setTargetPrice(e.target.value)}
              placeholder="Введите целевую цену"
              min="1"
              step="1"
              required
            />
          </div>
          
          <p className="notification-info">
            Мы пришлём уведомление на email, когда цена достигнет указанного значения
          </p>
          
          <div className="modal-actions">
            <button type="button" onClick={onClose} className="cancel-btn">
              Отмена
            </button>
            <button type="submit" className="confirm-btn">
              Подтвердить
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}