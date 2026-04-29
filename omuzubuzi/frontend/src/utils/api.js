import axios from 'axios';
const api = axios.create({ baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000', timeout: 15000 });
api.interceptors.request.use((c) => { const t = localStorage.getItem('omz_token'); if (t) c.headers.Authorization = 'Bearer ' + t; return c; });
api.interceptors.response.use((r) => r, (e) => { if (e.response?.status === 401) { localStorage.removeItem('omz_token'); window.location.href = '/login'; } return Promise.reject(e); });
export default api;
export const authAPI = { register: (d) => api.post('/api/auth/register', d), verifyOTP: (d) => api.post('/api/auth/verify-otp', d), login: (phone) => api.post('/api/auth/login', { phone }), loginVerify: (d) => api.post('/api/auth/login/verify', d) };
export const catalogAPI = { list: (p) => api.get('/api/products/', { params: p }) };
export const ordersAPI = { place: (d) => api.post('/api/orders/', d), track: (id) => api.get('/api/orders/' + id + '/track'), cancel: (id) => api.post('/api/orders/' + id + '/cancel') };
export const paymentsAPI = { initiate: (d) => api.post('/api/payments/initiate', d) };
