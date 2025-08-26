import { useState, useEffect } from 'react';
import './PriceModal.css';

export function PriceModal({ isOpen, onClose, onConfirm, currentPrice, productName }) {
  const [targetPrice, setTargetPrice] = useState('');
  const [customName, setCustomName] = useState('');

  // Предзаполняем поле именем товара при открытии модалки
  useEffect(() => {
    if (isOpen && productName) {
      setCustomName(productName);
    }
  }, [isOpen, productName]);

  if (!isOpen) return null;

  const handleSubmit = (e) => {
    e.preventDefault();
    const price = parseInt(targetPrice);
    if (price && price > 0 && customName.trim()) {
      onConfirm(price, customName.trim());
      setTargetPrice('');
      setCustomName('');
      onClose();
    }
  };

  return (
    <div className="modal-overlay">
      <div className="modal price-modal">
        <button className="close-btn" onClick={onClose}>×</button>
        <h2>Настройка уведомления</h2>
        
        {currentPrice && (
          <p className="current-price">
            Текущая цена: <strong>{Math.floor(currentPrice)} ₽</strong>
          </p>
        )}
        
        <form onSubmit={handleSubmit}>
          {/* Поле для имени товара */}
          <div className="input-group">
            <label htmlFor="customName">Имя для отображения:</label>
            <input
              type="text"
              id="customName"
              value={customName}
              onChange={(e) => setCustomName(e.target.value)}
              placeholder="Введите название товара"
              required
            />
          </div>

          {/* Поле для целевой цены */}
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
              Сохранить
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}