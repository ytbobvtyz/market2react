import api from './apiService'; // Импортируем общий экземпляр axios
import { API_SAVE_PARSING } from './config';

export const parsingService = {
  // Сохранить результаты парсинга
  saveParsingResults: async (query, results) => {
    try {
      // Проверяем есть ли токен
      const token = localStorage.getItem('access_token');
      if (!token) {
        throw new Error('Токен не найден. Пожалуйста, войдите снова.');
      }

      // Используем общий экземпляр api, который уже добавляет Authorization header
      const response = await api.post(API_SAVE_PARSING, {
        query,
        results
      });
      
      return response.data;
    } catch (error) {
      console.error('Error saving parsing results:', error);
      throw new Error(error.response?.data?.detail || 'Ошибка при сохранении данных');
    }
  },

  // Проверить аутентификацию
  checkAuth: () => {
    const token = localStorage.getItem('access_token');
    const user = localStorage.getItem('user');
    return !!(token && user);
  }
};

export default parsingService;