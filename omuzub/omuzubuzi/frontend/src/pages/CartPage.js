import React from 'react';
import { useTranslation } from 'react-i18next';
import { useCartStore } from '../store';
import { Link } from 'react-router-dom';

export default function CartPage() {
  const { t } = useTranslation();
  const { items, removeItem, total } = useCartStore();
  if (!items.length) return <div className="text-center py-20 text-gray-400 text-xl">{t('cart_empty')}</div>;
  return (
    <div className="max-w-lg mx-auto">
      <h2 className="text-2xl font-black mb-4">🛒 Cart</h2>
      <div className="bg-white rounded-2xl shadow p-4 mb-4">
        {items.map((i) => (
          <div key={i.product.id} className="flex justify-between items-center py-3 border-b last:border-0">
            <div>
              <p className="font-semibold">{i.product.name}</p>
              <p className="text-sm text-gray-500">Qty: {i.quantity} · UGX {(i.product.base_price * i.quantity).toLocaleString()}</p>
            </div>
            <button onClick={() => removeItem(i.product.id)} className="text-red-400 hover:text-red-600 text-xl">✕</button>
          </div>
        ))}
        <div className="flex justify-between font-black text-lg mt-4 pt-3 border-t">
          <span>Total</span><span>UGX {Math.round(total()).toLocaleString()}</span>
        </div>
      </div>
      <Link to="/checkout" className="block w-full bg-yellow-400 text-center text-gray-900 font-black py-4 rounded-2xl text-lg">
        {t('checkout')} →
      </Link>
    </div>
  );
}
