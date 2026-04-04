"use client";

import React, { createContext, useState, useEffect, useContext } from 'react';
import apiClient from '../lib/apiClient';

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchCurrentUser = async () => {
    try {
      const accessToken = localStorage.getItem('accessToken');
      if (accessToken) {
        const { data } = await apiClient.get('/auth/me');
        setUser(data);
      }
    } catch (err) {
      console.error('Failed to fetch user', err);
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCurrentUser();
  }, []);

  const login = async (identifier, password) => {
    const { data } = await apiClient.post('/auth/login', { identifier, password });
    setUser(data.user);
    localStorage.setItem('accessToken', data.access_token);
    localStorage.setItem('refreshToken', data.refresh_token);
  };

  const register = async (username, email, password) => {
    try {
      console.log('--- REGISTRATION ATTEMPT ---');
      console.log('Target URL:', `${apiClient.defaults.baseURL}/auth/register`);
      console.log('Payload:', { username, email, password });

      const { data } = await apiClient.post('/auth/register', { username, email, password });

      console.log('Registration Success:', data);
      return data;
    } catch (error) {
      console.error('Registration Error Details:', {
        message: error.message,
        status: error.response?.status,
        statusText: error.response?.statusText,
        data: error.response?.data,
        config: error.config
      });
      throw error;
    }
  };

  const logout = async () => {
    const refreshToken = localStorage.getItem('refreshToken');
    if (refreshToken) {
      await apiClient.post('/auth/logout', { refresh_token: refreshToken });
    }
    setUser(null);
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
  };

  const setTokens = (accessToken, refreshToken) => {
    localStorage.setItem('accessToken', accessToken);
    localStorage.setItem('refreshToken', refreshToken);
    fetchCurrentUser();
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, setTokens }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
