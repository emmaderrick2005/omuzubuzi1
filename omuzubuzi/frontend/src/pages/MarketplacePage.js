import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { catalogAPI } from '../utils/api';
import { useCartStore, useAuthStore } from '../store';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';

const CATEGORIES = ['Groceries','Beverages','Personal Care','Household','Stationery','Electronics','Agri-produce','Other'];

const formatUGX = (n) => 'UGX ' + Math.round(n).toLocaleString('en-UG');

export default function MarketplacePage() {
  const { t } = useTranslation();
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [q, setQ] = useState('');
  const [category, setCategory] = useState('');
  const addItem = useCartStore((s) => s.addItem);
  const { user } = useAuthStore();
  const navigate = useNavigate();

  useEffect(() => {
    const fetch = async () => {
      setLoading(true);
      try {
        const res = await catalogAPI.list({ q: q || undefined, category: category || undefined });
        setProducts(res.data.products || []);
      } catch { setProducts([]); }
      finally { setLoading(false); }
    };
    const timer = setTimeout(fetch, 300);
    return () => clearTimeout(timer);
  }, [q, category]);

  const handleAdd = (p) => {
    if (!user) { navigate('/login'); return; }
    addItem(p, p.moq || 1);
    toast.success(p.name + ' added to cart!');
  };

  return (
    <div>
      {/* Hero */}
      <div className="bg-yellow-400 rounded-2xl p-6 mb-6 text-center">
        <h2 className="text-2xl font-black text-gray-900 mb-1">{t('browse')}</h2>
        <p className="text-gray-700">{t('tagline')}</p>
      </div>

      {/* Filters */}
      <div className="flex gap-3 mb-4 flex-wrap">
        <input type="text" value={q} onChange={(e) => setQ(e.target.value)}
          placeholder={t('search_placeholder')}
          className="flex-1 border-2 border-gray-200 rounded-xl px-4 py-2 focus:border-yellow-400 outline-none min-w-0" />
        <select value={category} onChange={(e) => setCategory(e.target.value)}
          className="border-2 border-gray-200 rounded-xl px-3 py-2 focus:border-yellow-400 outline-none">
          <option value="">{t('category')}</option>
          {CATEGORIES.map((c) => <option key={c} value={c}>{c}</option>)}
        </select>
      </div>

      {/* Product grid */}
      {loading ? (
        <p className="text-center text-gray-500 py-12">{t('loading')}</p>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {products.map((p) => (
            <div key={p.id} className="bg-white rounded-2xl shadow-md overflow-hidden hover:shadow-lg transition-shadow">
              <div className="h-40 bg-gray-100 flex items-center justify-center text-5xl">
                {p.category === 'Groceries' ? '🌾' : p.category === 'Beverages' ? '🥤' : p.category === 'Electronics' ? '📱' : '📦'}
              </div>
              <div className="p-4">
                <h3 className="font-bold text-gray-900 text-lg leading-tight">{p.name}</h3>
                <p className="text-yellow-600 font-black text-xl mt-1">{formatUGX(p.base_price)}<span className="text-sm text-gray-500 font-normal">/{p.unit}</span></p>
                <p className="text-xs text-gray-500 mt-1">MOQ: {p.moq} {p.unit}</p>
                {p.is_out_of_stock ? (
                  <span className="inline-block mt-3 bg-red-100 text-red-600 text-sm px-3 py-1 rounded-full">{t('out_of_stock')}</span>
                ) : (
                  <button onClick={() => handleAdd(p)}
                    className="mt-3 w-full bg-yellow-400 hover:bg-yellow-500 text-gray-900 font-bold py-2 rounded-xl">
                    {t('add_to_cart')}
                  </button>
                )}
              </div>
            </div>
          ))}
          {!products.length && !loading && (
            <div className="col-span-3 text-center text-gray-400 py-16">No products found.</div>
          )}
        </div>
      )}
    </div>
  );
}
