import api, { setAuthToken } from './apiService';
import { API_AUTH_LOGIN, API_AUTH_REGISTER } from './config';

export const login = async (email, password) => {
  const params = new URLSearchParams();
  params.append('username', email);
  params.append('password', password);

  try {
    const response = await api.post(API_AUTH_LOGIN, params.toString(), {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      }
    });
    
    // Сохраняем токен после успешного логина
    if (response.data.access_token) {
      setAuthToken(response.data.access_token);
      localStorage.setItem('user', JSON.stringify(response.data.user));
    }
    
    return response.data;
  } catch (error) {
    console.error('Login error:', error);
    throw error;
  }
};

export const register = async (userData) => {
  try {
    const response = await api.post(API_AUTH_REGISTER, userData);
    return response.data;
  } catch (error) {
    console.error('Register error:', error);
    throw error;
  }
};

export const logout = () => {
  setAuthToken(null);
  localStorage.removeItem('user');
};

export const getCurrentUser = () => {
  const user = localStorage.getItem('user');
  return user ? JSON.parse(user) : null;
};

export const isAuthenticated = () => {
  return !!localStorage.getItem('access_token');
};