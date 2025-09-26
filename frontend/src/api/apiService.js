import axios from 'axios';
import { API_BASE_URL } from './config';

// Создаем экземпляр axios с базовыми настройками
export const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000, // 60 секунд вместо стандартных 5-10с
  headers: {
    'Content-Type': 'application/json',
  },
});

// Функция для установки токена
export const setAuthToken = (token) => {
  if (token) {
    localStorage.setItem('access_token', token);
    api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
  } else {
    localStorage.removeItem('access_token');
    delete api.defaults.headers.common['Authorization'];
  }
};

// Интерцептор для автоматической подстановки токена
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Интерцептор для обработки ошибок авторизации
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Перенаправляем на страницу логина при истечении токена
      localStorage.removeItem('access_token');
      localStorage.removeItem('user');
    }
    return Promise.reject(error);
  }
);

export default api;