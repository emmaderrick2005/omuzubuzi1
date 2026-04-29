import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useCartStore, useAuthStore } from '../store';
import { ordersAPI, paymentsAPI } from '../utils/api';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';

const KYC_THRESHOLD = 1_000_000;

export default function CheckoutPage() {
  const { t } = useTranslation();
  const { items, total, wholesaler_id, clear } = useCartStore();
  const { user } = useAuthStore();
  const navigate = useNavigate();
  const [address, setAddress] = useState('');
  const [momoPhone, setMomoPhone] = useState('');
  const [method, setMethod] = useState('mtn_momo');
  const [loading, setLoading] = useState(false);

  const cartTotal = total();
  const needsKYC = cartTotal >= KYC_THRESHOLD && !user?.id_verified;

  const handleOrder = async () => {
    if (!address) { toast.error('Enter delivery address'); return; }
    if (!momoPhone) { toast.error('Enter MoMo phone number'); return; }
    if (needsKYC) { toast.error(t('kyc_required')); return; }

    setLoading(true);
    try {
      // 1. Place order
      const orderRes = await ordersAPI.place({
        wholesaler_id, items: items.map((i) => ({ product_id: i.product.id, quantity: i.quantity })),
        delivery_address: address, total_weight_kg: 5,
      });
      const orderId = orderRes.data.order_id;

      // 2. Initiate payment
      await paymentsAPI.initiate({ order_id: orderId, method, phone: momoPhone });

      clear();
      toast.success('Order placed! Check your phone to approve payment.');
      navigate('/orders/' + orderId + '/track');
    } catch (e) {
      const detail = e.response?.data?.detail;
      if (detail?.code === 'ID_VERIFICATION_REQUIRED') {
        toast.error(t('kyc_required'));
      } else {
        toast.error(typeof detail === 'string' ? detail : t('error'));
      }
    } finally { setLoading(false); }
  };

  const formatUGX = (n) => 'UGX ' + Math.round(n).toLocaleString('en-UG');

  if (!items.length) return <div className="text-center py-20 text-gray-400 text-xl">{t('cart_empty')}</div>;

  return (
    <div className="max-w-lg mx-auto">
      <h2 className="text-2xl font-black mb-4">{t('checkout')}</h2>

      <div className="bg-white rounded-2xl shadow p-4 mb-4">
        <h3 className="font-bold mb-3">Order Summary</h3>
        {items.map((i) => (
          <div key={i.product.id} className="flex justify-between py-2 border-b last:border-0">
            <span>{i.product.name} × {i.quantity}</span>
            <span className="font-semibold">{formatUGX(i.product.base_price * i.quantity)}</span>
          </div>
        ))}
        <div className="flex justify-between font-black text-lg mt-3 pt-3 border-t">
          <span>Total</span>
          <span className="text-yellow-600">{formatUGX(cartTotal)}</span>
        </div>
      </div>

      {/* NPS Act 2020 KYC Warning */}
      {needsKYC && (
        <div className="bg-red-50 border-2 border-red-300 rounded-2xl p-4 mb-4">
          <p className="text-red-700 font-semibold text-sm">⚠️ {t('kyc_required')}</p>
          <p className="text-red-600 text-xs mt-1">Please verify your ID in your profile before proceeding.</p>
        </div>
      )}

      <div className="bg-white rounded-2xl shadow p-4 mb-4">
        <label className="block font-semibold mb-1">{t('delivery_address')}</label>
        <textarea value={address} onChange={(e) => setAddress(e.target.value)}
          placeholder="e.g. Nakasero Market, Kampala Central" rows={3}
          className="w-full border-2 border-gray-200 rounded-xl p-3 focus:border-yellow-400 outline-none" />
      </div>

      <div className="bg-white rounded-2xl shadow p-4 mb-4">
        <p className="font-semibold mb-3">Payment Method</p>
        {['mtn_momo','airtel_money'].map((m) => (
          <button key={m} onClick={() => setMethod(m)}
            className={'w-full text-left p-3 rounded-xl border-2 mb-2 font-medium ' + (method === m ? 'border-yellow-400 bg-yellow-50' : 'border-gray-200')}>
            {m === 'mtn_momo' ? '🟡 ' + t('pay_momo') : '🔴 ' + t('pay_airtel')}
          </button>
        ))}
        <input type="tel" value={momoPhone} onChange={(e) => setMomoPhone(e.target.value)}
          placeholder="MoMo phone: +256XXXXXXXXX"
          className="w-full border-2 border-gray-200 rounded-xl p-3 mt-2 focus:border-yellow-400 outline-none" />
      </div>

      <button onClick={handleOrder} disabled={loading || needsKYC}
        className="w-full bg-yellow-400 hover:bg-yellow-500 text-gray-900 font-black py-4 rounded-2xl text-lg disabled:opacity-50">
        {loading ? t('loading') : t('place_order') + ' · ' + formatUGX(cartTotal)}
      </button>
    </div>
  );
}
