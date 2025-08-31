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
import { api } from '../api/apiService'; // Импортируем настроенный api
import './TrackingHistory.css';

// Регистрируем компоненты ChartJS
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

  const location = useLocation();

  useEffect(() => {
    fetchUserTrackings();
  }, [location.key]);

  useEffect(() => {
    if (selectedTracking) {
      fetchPriceHistory(selectedTracking.id);
    }
  }, [selectedTracking]);

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

      const response = await api.get('/api/v1/user-trackings/', {
        timeout: 10000 // Таймаут 10 секунд
      });
      
      setTrackings(response.data);
      if (response.data.length > 0) {
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
      const response = await api.get(`/api/v1/tracking/${trackingId}/`);
      setPriceHistory(response.data.price_history || []);
    } catch (err) {
      console.error('Error fetching price history:', err);
    }
  };

  const handleDeleteTracking = async (trackingId) => {
    if (!window.confirm('Вы уверены, что хотите удалить этот трекинг?')) {
      return;
    }

    try {
      await api.delete(`/api/v1/tracking/${trackingId}/`);

      // Обновляем список трекингов
      setTrackings(prev => prev.filter(t => t.id !== trackingId));
      
      // Если удалили выбранный трекинг, сбрасываем выбор
      if (selectedTracking && selectedTracking.id === trackingId) {
        setSelectedTracking(null);
        setPriceHistory([]);
      }

      alert('Трекинг успешно удален!');
    } catch (err) {
      console.error('Error deleting tracking:', err);
      alert('Ошибка при удалении трекинга');
    }
  };

  // Функция переименования трекинга
  const handleRenameTracking = async (trackingId, newName, newPrice) => {
    try {
      const updateData = {};
      
      if (newName) updateData.custom_name = newName;
      if (newPrice) updateData.desired_price = parseFloat(newPrice);

      const response = await api.patch(
        `/api/v1/tracking/${trackingId}/`,
        updateData
      );

      // Обновляем список трекингов
      setTrackings(prev => prev.map(t => 
        t.id === trackingId ? response.data : t
      ));

      // Обновляем выбранный трекинг если он редактировался
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

  // Функция для начала редактирования
  const startEditing = (tracking) => {
    setEditingTracking(tracking.id);
    setNewName(tracking.custom_name || '');
    setNewPrice(tracking.desired_price || '');
  };

  // Функция отмены редактирования
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
          borderColor: 'rgb(75, 192, 192)',
          backgroundColor: 'rgba(75, 192, 192, 0.2)',
          tension: 0.1,
          fill: true
        },
        {
          label: 'Желаемая цена',
          data: Array(prices.length).fill(selectedTracking.desired_price),
          borderColor: 'rgb(255, 99, 132)',
          backgroundColor: 'rgba(255, 99, 132, 0.2)',
          borderDash: [5, 5],
          tension: 0,
          fill: false
        }
      ]
    };
  };

  const chartOptions = {
    responsive: true,
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
        {/* Левая панель - список трекингов */}
        <div className="tracking-list">
          <h2>Мои товары</h2>
          {trackings.length === 0 ? (
            <p className="empty-state">У вас нет сохранённых товаров</p>
          ) : (
            <div className="tracking-items">
              {trackings.map(tracking => (
                <div
                  key={tracking.id}
                  className={`tracking-item ${selectedTracking?.id === tracking.id ? 'active' : ''}`}
                >
                  {/* Основная информация - кликабельна для выбора */}
                  <div 
                    className="tracking-info"
                    onClick={() => setSelectedTracking(tracking)}
                  >
                    <h3>{tracking.custom_name}</h3>
                    <p className="wb-id">Артикул: {tracking.wb_item_id}</p>
                    <p className="target-price">
                      Цель: {tracking.desired_price ? `${tracking.desired_price} ₽` : 'не задана'}
                    </p>
                    <p className="status">
                      Статус: {tracking.is_active ? 'Активен' : 'Неактивен'}
                    </p>
                    <p className="created-date">
                      Добавлен: {new Date(tracking.created_at).toLocaleDateString('ru-RU')}
                    </p>
                  </div>
                  
                  {/* Кнопки управления - справа от информации */}
                  <div className="tracking-item-actions">
                    <button 
                      className="btn-rename"
                      onClick={(e) => {
                        e.stopPropagation(); // Предотвращаем всплытие клика
                        startEditing(tracking);
                      }}
                      title="Переименовать"
                    >
                      ✏️
                    </button>
                    <button 
                      className="btn-delete"
                      onClick={(e) => {
                        e.stopPropagation(); // Предотвращаем всплытие клика
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

        {/* Правая панель - график и детали */}
        <div className="tracking-details">
          {selectedTracking ? (
            <>
              <div className="tracking-header">
                <h2>{selectedTracking.custom_name}</h2>
                <div className="tracking-stats">
                  <span>Артикул: {selectedTracking.wb_item_id}</span>
                  <span>Цель: {selectedTracking.desired_price ? `${selectedTracking.desired_price} ₽` : 'не задана'}</span>
                </div>
              </div>

              {/* Форма редактирования */}
              {editingTracking === selectedTracking.id && (
                <div className="edit-form">
                  <h3>Редактирование трекинга</h3>
                  <div className="form-group">
                    <label>Название товара:</label>
                    <input
                      type="text"
                      value={newName}
                      onChange={(e) => setNewName(e.target.value)}
                      placeholder="Введите новое название"
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
                  <div className="form-buttons">
                    <button 
                      className="btn-save"
                      onClick={() => handleRenameTracking(selectedTracking.id, newName, newPrice)}
                    >
                      Сохранить
                    </button>
                    <button 
                      className="btn-cancel"
                      onClick={cancelEditing}
                    >
                      Отмена
                    </button>
                  </div>
                </div>
              )}

              {/* График */}
              {priceHistory.length > 0 ? (
                <div className="chart-container">
                  <Line data={prepareChartData()} options={chartOptions} />
                </div>
              ) : (
                <div className="no-data">
                  <p>Нет данных для построения графика</p>
                </div>
              )}

              {/* История цен */}
              <div className="price-history">
                <h3>История цен</h3>
                <div className="history-table">
                  <div className="table-header">
                    <span>Дата</span>
                    <span>Цена</span>
                    <span>Рейтинг</span>
                    <span>Отзывы</span>
                  </div>
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