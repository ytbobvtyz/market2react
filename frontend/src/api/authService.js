import axios from 'axios';
import { API_BASE_URL, API_AUTH_LOGIN, API_AUTH_REGISTER } from './config';

export const login = async (email, password) => {
  try {
    const formData = new URLSearchParams();
    formData.append('username', email);
    formData.append('password', password);

    console.log('Request data:', Object.fromEntries(formData)); // Логируем данные

    const response = await axios.post(
      `${API_BASE_URL}${API_AUTH_LOGIN}`,
      formData,
      {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
        },
        validateStatus: (status) => status < 500 // Чтобы не выбрасывать ошибку на 4xx
      }
    );

    console.log('Response:', response.data); // Логируем ответ
    return response.data;
  } catch (error) {
    console.error('Full error:', {
      request: error.config,
      response: error.response?.data,
      status: error.response?.status
    });
    throw error;
  }
};

export const register = async (userData) => {
  const response = await axios.post(
    `${API_BASE_URL}${API_AUTH_REGISTER}`,
    userData
  );
  return response.data;
};