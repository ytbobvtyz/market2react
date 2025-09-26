import { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js';
import { api } from '../api/apiService';
import './TrackingHistory.css';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

export function TrackingHistory() {
  const [trackings, setTrackings] = useState([]);
  const [selectedTracking, setSelectedTracking] = useState(null);
  const [priceHistory, setPriceHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [editingTracking, setEditingTracking] = useState(null);
  const [newName, setNewName] = useState('');
  const [newPrice, setNewPrice] = useState('');
  const [updatingPrice, setUpdatingPrice] = useState(false);
  const [updateProgress, setUpdateProgress] = useState(0);

  const location = useLocation();

  useEffect(() => {
    fetchUserTrackings();
  }, [location.key]);

  useEffect(() => {
    if (selectedTracking) {
      fetchPriceHistory(selectedTracking.id);
    }
  }, [selectedTracking]);

  // Расчет текущей цены и разницы
  const getCurrentPriceInfo = () => {
    if (!priceHistory.length) return null;
    
    const latestPrice = priceHistory[0]?.price;
    const targetPrice = selectedTracking?.desired_price;
    
    if (!latestPrice || !targetPrice) return null;
    
    const difference = latestPrice - targetPrice;
    const differencePercent = ((difference / targetPrice) * 100).toFixed(1);
    
    return {
      current: latestPrice,
      target: targetPrice,
      difference: difference,
      differencePercent: differencePercent
    };
  };

  const fetchUserTrackings = async () => {
    try {
      setLoading(true);
      setError('');
      const token = localStorage.getItem('access_token');
      
      if (!token) {
        setError('Требуется авторизация');
        setLoading(false);
        return;
      }

      const response = await api.get('/api/user-trackings/', {
        timeout: 10000
      });
      
      setTrackings(response.data);
      if (response.data.length > 0 && !selectedTracking) {
        setSelectedTracking(response.data[0]);
      }
    } catch (err) {
      console.error('Error fetching trackings:', err);
      if (err.response?.status === 401) {
        setError('Ошибка авторизации. Пожалуйста, войдите снова.');
      } else if (err.response?.status === 404) {
        setError('Эндпоинт не найден. Проверьте настройки сервера.');
      } else if (err.code === 'NETWORK_ERROR') {
        setError('Ошибка сети. Проверьте подключение к серверу.');
      } else {
        setError('Ошибка загрузки данных. Проверьте консоль для деталей.');
      }
    } finally {
      setLoading(false);
    }
  };

  const fetchPriceHistory = async (trackingId) => {
    try {
      const response = await api.get(`/api/tracking/${trackingId}/`);
      setPriceHistory(response.data.price_history || []);
    } catch (err) {
      console.error('Error fetching price history:', err);
    }
  };

  const handleUpdatePrice = async (trackingId) => {
    if (!trackingId) return;
    
    setUpdatingPrice(true);
    setUpdateProgress(0);
    
    const progressInterval = setInterval(() => {
      setUpdateProgress(prev => {
        if (prev >= 95) return 95;
        return prev + 5;
      });
    }, 1000);

    try {
      console.log('Начинаем обновление цены для товара:', trackingId);
      
      const { data } = await api.get(`/api/products/${selectedTracking.wb_item_id}`, {
        timeout: 180000
      });
      
      clearInterval(progressInterval);
      setUpdateProgress(100);
      
      const newPriceEntry = {
        id: Date.now(),
        price: data.price,
        checked_at: new Date().toISOString(),
        rating: data.rating,
        comment_count: data.comment_count
      };
      
      setPriceHistory(prev => [newPriceEntry, ...prev]);
      
      setTimeout(() => {
        setUpdateProgress(0);
        setUpdatingPrice(false);
      }, 1000);
      
      alert('Цена успешно обновлена!');
      
    } catch (err) {
      clearInterval(progressInterval);
      setUpdateProgress(0);
      setUpdatingPrice(false);
      
      console.error('❌ Ошибка обновления цены:', err);
      
      if (err.code === 'ECONNABORTED') {
        alert('Обновление заняло слишком много времени. Попробуйте еще раз.');
      } else if (err.message === 'Network Error') {
        alert('Сервер недоступен. Проверьте соединение.');
      } else if (err.response?.status === 504) {
        alert('Сервер занят. Попробуйте через минуту.');
      } else {
        alert(err.response?.data?.detail || 'Ошибка обновления. Попробуйте еще раз.');
      }
    }
  };

  const handleDeleteTracking = async (trackingId) => {
    if (!window.confirm('Вы уверены, что хотите удалить этот трекинг?')) {
      return;
    }

    try {
      await api.delete(`/api/tracking/${trackingId}/`);
      setTrackings(prev => prev.filter(t => t.id !== trackingId));
      
      if (selectedTracking && selectedTracking.id === trackingId) {
        setSelectedTracking(trackings.length > 1 ? trackings.find(t => t.id !== trackingId) : null);
        setPriceHistory([]);
      }

      alert('Трекинг успешно удален!');
    } catch (err) {
      console.error('Error deleting tracking:', err);
      alert('Ошибка при удалении трекинга');
    }
  };

  const handleRenameTracking = async (trackingId, newName, newPrice) => {
    try {
      const updateData = {};
      
      if (newName) updateData.custom_name = newName;
      if (newPrice) updateData.desired_price = parseFloat(newPrice);

      const response = await api.patch(
        `/api/tracking/${trackingId}/`,
        updateData
      );

      setTrackings(prev => prev.map(t => 
        t.id === trackingId ? response.data : t
      ));

      if (selectedTracking && selectedTracking.id === trackingId) {
        setSelectedTracking(response.data);
      }

      setEditingTracking(null);
      setNewName('');
      setNewPrice('');
      alert('Трекинг успешно обновлен!');
    } catch (err) {
      console.error('Error updating tracking:', err);
      alert('Ошибка при обновлении трекинга');
    }
  };

  const startEditing = (tracking) => {
    setEditingTracking(tracking.id);
    setNewName(tracking.custom_name || '');
    setNewPrice(tracking.desired_price || '');
  };

  const cancelEditing = () => {
    setEditingTracking(null);
    setNewName('');
    setNewPrice('');
  };
  
  const prepareChartData = () => {
    if (!priceHistory.length) return null;

    const sortedHistory = [...priceHistory].sort((a, b) => 
      new Date(a.checked_at) - new Date(b.checked_at)
    );

    const labels = sortedHistory.map(item => 
      new Date(item.checked_at).toLocaleDateString('ru-RU')
    );

    const prices = sortedHistory.map(item => Number(item.price));

    return {
      labels,
      datasets: [
        {
          label: 'Фактическая цена',
          data: prices,
          borderColor: 'rgb(126, 34, 206)',
          backgroundColor: 'rgba(126, 34, 206, 0.1)',
          tension: 0.1,
          fill: true
        },
        {
          label: 'Желаемая цена',
          data: Array(prices.length).fill(selectedTracking.desired_price),
          borderColor: 'rgb(139, 92, 246)',
          backgroundColor: 'rgba(139, 92, 246, 0.1)',
          borderDash: [5, 5],
          tension: 0,
          fill: false
        }
      ]
    };
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top',
      },
      title: {
        display: true,
        text: 'Динамика изменения цены'
      },
      tooltip: {
        callbacks: {
          label: function(context) {
            return `${context.dataset.label}: ${context.parsed.y} ₽`;
          }
        }
      }
    },
    scales: {
      y: {
        beginAtZero: false,
        title: {
          display: true,
          text: 'Цена (рубли)'
        }
      },
      x: {
        title: {
          display: true,
          text: 'Дата проверки'
        }
      }
    }
  };

  const priceInfo = getCurrentPriceInfo();

  if (loading) {
    return <div className="loading">Загрузка истории...</div>;
  }

  if (error) {
    return <div className="error">{error}</div>;
  }

  return (
    <div className="tracking-history-page">
      <header className="page-header">
        <h1>История моих запросов</h1>
        <a href="/" className="back-link">← На главную</a>
      </header>

      <div className="tracking-content">
        {/* Левая панель - компактный список трекингов */}
        <div className="tracking-list">
          <div className="tracking-list-header">
            <h2>Мои товары ({trackings.length})</h2>
          </div>
          {trackings.length === 0 ? (
            <p className="empty-state">У вас нет сохранённых товаров</p>
          ) : (
            <div className="tracking-items">
              {trackings.map(tracking => (
                <div
                  key={tracking.id}
                  className={`tracking-item ${selectedTracking?.id === tracking.id ? 'active' : ''}`}
                  onClick={() => setSelectedTracking(tracking)}
                >
                  <div className="tracking-info">
                    <h3 title={tracking.custom_name}>{tracking.custom_name}</h3>
                    <div className="tracking-meta">
                      <span className="wb-id">{tracking.wb_item_id}</span>
                      <span className={`status ${tracking.is_active ? 'active' : 'inactive'}`}>
                        {tracking.is_active ? '✓' : '●'}
                      </span>
                    </div>
                  </div>
                  
                  <div className="tracking-actions">
                    <button 
                      className="btn-rename"
                      onClick={(e) => {
                        e.stopPropagation();
                        startEditing(tracking);
                      }}
                      title="Редактировать"
                    >
                      ✏️
                    </button>
                    <button 
                      className="btn-delete"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDeleteTracking(tracking.id);
                      }}
                      title="Удалить"
                    >
                      🗑️
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Правая панель - детали */}
        <div className="tracking-details">
          {selectedTracking ? (
            <>
              <div className="tracking-header">
                <div className="tracking-title">
                  <h2>
                    <a 
                      href={`https://www.wildberries.ru/catalog/${selectedTracking.wb_item_id}/detail.aspx`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="product-link"
                    >
                      {selectedTracking.custom_name}
                    </a>
                  </h2>
                  <div className="tracking-stats">
                    <span className="stat-item">
                      <strong>Артикул:</strong>{' '}
                      <a 
                        href={`https://www.wildberries.ru/catalog/${selectedTracking.wb_item_id}/detail.aspx`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="wb-link"
                      >
                        {selectedTracking.wb_item_id}
                      </a>
                    </span>
                    {/* <span className="stat-item">
                      <strong>Цель:</strong> {selectedTracking.desired_price ? `${selectedTracking.desired_price} ₽` : 'не задана'}
                    </span>
                    <span className="stat-item">
                      <strong>Статус:</strong> 
                      <span className={`status-badge ${selectedTracking.is_active ? 'active' : 'inactive'}`}>
                        {selectedTracking.is_active ? 'Активен' : 'Неактивен'}
                      </span>
                    </span> */}
                  </div>
                </div>
                
                {/* Кнопка обновления цены */}
                <button 
                  className="btn-update-price"
                  onClick={() => handleUpdatePrice(selectedTracking.id)}
                  disabled={updatingPrice}
                >
                  {updatingPrice ? '🔄 Обновление...' : '🔄 Обновить'}
                </button>
              </div>

              {/* Прогресс-бар обновления */}
              {updatingPrice && (
                <div className="update-progress">
                  <div className="progress-bar">
                    <div 
                      className="progress-fill" 
                      style={{ width: `${updateProgress}%` }}
                    ></div>
                  </div>
                  <span>{updateProgress}%</span>
                </div>
              )}

              {/* Форма редактирования */}
              {editingTracking === selectedTracking.id && (
                <div className="edit-form highlight">
                  <h3>✏️ Редактирование трекинга</h3>
                  <div className="form-row">
                    <div className="form-group">
                      <label>Название товара:</label>
                      <input
                        type="text"
                        value={newName}
                        onChange={(e) => setNewName(e.target.value)}
                        placeholder="Введите новое название"
                        autoFocus
                      />
                    </div>
                    <div className="form-group">
                      <label>Желаемая цена:</label>
                      <input
                        type="number"
                        value={newPrice}
                        onChange={(e) => setNewPrice(e.target.value)}
                        placeholder="Введите желаемую цену"
                      />
                    </div>
                  </div>
                  <div className="form-buttons">
                    <button 
                      className="btn-save"
                      onClick={() => handleRenameTracking(selectedTracking.id, newName, newPrice)}
                    >
                      💾 Сохранить
                    </button>
                    <button 
                      className="btn-cancel"
                      onClick={cancelEditing}
                    >
                      ❌ Отмена
                    </button>
                  </div>
                </div>
              )}

              {/* График с информацией о ценах */}
              <div className="chart-section">
                <div className="chart-header">
                  <h3>График цен</h3>
                  {priceInfo && (
                    <div className="price-info">
                      <span className="price-item">
                        <strong>Цель:</strong> {priceInfo.target} ₽
                      </span>
                      <span className="price-item">
                        <strong>Текущая:</strong> {priceInfo.current} ₽
                      </span>
                      <span className={`price-item difference ${priceInfo.difference < 0 ? 'negative' : 'positive'}`}>
                        <strong>Разница:</strong> {priceInfo.difference >= 0 ? '+' : ''}{priceInfo.difference} ₽ ({priceInfo.differencePercent}%)
                      </span>
                    </div>
                  )}
                </div>
                {priceHistory.length > 0 ? (
                  <div className="chart-container">
                    <Line data={prepareChartData()} options={chartOptions} />
                  </div>
                ) : (
                  <div className="no-data">
                    <p>Нет данных для построения графика</p>
                  </div>
                )}
              </div>

              {/* История цен */}
              <div className="price-history">
                <h3>История изменений</h3>
                <div className="history-table">
                  <div className="table-header">
                    <span>Дата</span>
                    <span>Цена</span>
                    <span>Рейтинг</span>
                    <span>Отзывы</span>
                  </div>
                  <div className="table-body">
                    {priceHistory.map(item => (
                      <div key={item.id} className="table-row">
                        <span>{new Date(item.checked_at).toLocaleDateString('ru-RU')}</span>
                        <span className="price">{Number(item.price)} ₽</span>
                        <span className="rating">{item.rating || '-'}</span>
                        <span className="comments">{item.comment_count || '-'}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </>
          ) : (
            <div className="no-selection">
              <p>Выберите товар для просмотра истории цен</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}