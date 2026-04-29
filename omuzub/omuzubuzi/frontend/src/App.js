import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import './i18n';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import MarketplacePage from './pages/MarketplacePage';
import CartPage from './pages/CartPage';
import CheckoutPage from './pages/CheckoutPage';
import OrderTrackingPage from './pages/OrderTrackingPage';
import WholesalerDashboardPage from './pages/WholesalerDashboardPage';
import AdminDashboardPage from './pages/AdminDashboardPage';
import Layout from './components/layout/Layout';
import { useAuthStore } from './store';

const PrivateRoute = ({ children, roles }) => {
  const { user } = useAuthStore();
  if (!user) return <Navigate to="/login" replace />;
  if (roles && !roles.includes(user.role)) return <Navigate to="/" replace />;
  return children;
};

export default function App() {
  return (
    <BrowserRouter>
      <Toaster position="top-center" toastOptions={{ duration: 3000 }} />
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/" element={<Layout />}>
          <Route index element={<MarketplacePage />} />
          <Route path="cart" element={<PrivateRoute><CartPage /></PrivateRoute>} />
          <Route path="checkout" element={<PrivateRoute><CheckoutPage /></PrivateRoute>} />
          <Route path="orders/:id/track" element={<PrivateRoute><OrderTrackingPage /></PrivateRoute>} />
          <Route path="wholesaler" element={<PrivateRoute roles={['wholesaler']}><WholesalerDashboardPage /></PrivateRoute>} />
          <Route path="admin" element={<PrivateRoute roles={['admin']}><AdminDashboardPage /></PrivateRoute>} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
