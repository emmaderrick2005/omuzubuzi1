import React from 'react';
import { Outlet, Link, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuthStore, useCartStore } from '../../store';
import i18n from '../../i18n';

export default function Layout() {
  const { t } = useTranslation();
  const { user, setLanguage, logout } = useAuthStore();
  const items = useCartStore((s) => s.items);
  const navigate = useNavigate();

  const toggleLang = () => {
    const next = i18n.language === 'en' ? 'lg' : 'en';
    i18n.changeLanguage(next);
    setLanguage(next);
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Top nav */}
      <header className="bg-yellow-400 shadow-md">
        <div className="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2">
            <span className="text-2xl font-black text-gray-900">🛒 {t('app_name')}</span>
          </Link>
          <div className="flex items-center gap-3">
            <button onClick={toggleLang} className="text-sm bg-white px-3 py-1 rounded-full font-semibold shadow">
              {i18n.language === 'en' ? '🇺🇬 Luganda' : '🇬🇧 English'}
            </button>
            {user ? (
              <>
                <Link to="/cart" className="relative">
                  <span className="text-2xl">🛒</span>
                  {items.length > 0 && (
                    <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
                      {items.length}
                    </span>
                  )}
                </Link>
                {user.role === 'wholesaler' && <Link to="/wholesaler" className="text-sm font-semibold">Dashboard</Link>}
                {user.role === 'admin' && <Link to="/admin" className="text-sm font-semibold">Admin</Link>}
                <button onClick={() => { logout(); navigate('/login'); }} className="text-sm bg-gray-800 text-white px-3 py-1 rounded-full">Logout</button>
              </>
            ) : (
              <Link to="/login" className="bg-gray-900 text-white px-4 py-2 rounded-full text-sm font-semibold">{t('login')}</Link>
            )}
          </div>
        </div>
      </header>
      <main className="flex-1 max-w-6xl mx-auto w-full px-4 py-6">
        <Outlet />
      </main>
      <footer className="bg-gray-900 text-gray-400 text-center py-4 text-sm">
        © 2026 Omuzubuzi · Kampala, Uganda · <em>{t('tagline')}</em>
      </footer>
    </div>
  );
}
