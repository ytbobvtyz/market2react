import axios from 'axios';
import { API_BASE_URL, API_AUTH_LOGIN, API_AUTH_REGISTER } from './config';

export const login = async (email, password) => {
  // Используем URLSearchParams вместо FormData
  const params = new URLSearchParams();
  params.append('username', email); // Важно: username, а не email
  params.append('password', password);

  try {
    const response = await axios.post(
      `${API_BASE_URL}${API_AUTH_LOGIN}`,
      params.toString(), // Явное преобразование в строку
      {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded' // Правильный Content-Type
        }
      }
    );
    return response.data;
  } catch (error) {
    console.error('Error details:', {
      request: {
        data: params.toString(),
        headers: error.config.headers
      },
      response: error.response?.data
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
