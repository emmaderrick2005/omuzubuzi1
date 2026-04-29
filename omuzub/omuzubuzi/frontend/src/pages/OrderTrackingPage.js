import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { ordersAPI } from '../utils/api';

const STEPS = ['confirmed','packed','picked_up','in_transit','delivered'];
const STEP_LABELS = { confirmed:'Order Confirmed', packed:'Being Packed', picked_up:'Picked Up', in_transit:'In Transit', delivered:'Delivered!' };

export default function OrderTrackingPage() {
  const { id } = useParams();
  const [order, setOrder] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const poll = async () => {
      try { const r = await ordersAPI.track(id); setOrder(r.data); }
      catch { /* ignore */ }
      finally { setLoading(false); }
    };
    poll();
    const timer = setInterval(poll, 10000); // poll every 10s
    return () => clearInterval(timer);
  }, [id]);

  if (loading) return <p className="text-center py-12">Loading...</p>;
  if (!order) return <p className="text-center py-12 text-red-500">Order not found</p>;

  const currentIdx = STEPS.indexOf(order.status);

  return (
    <div className="max-w-lg mx-auto">
      <h2 className="text-2xl font-black mb-6">📦 Track Order</h2>
      <div className="bg-white rounded-2xl shadow p-6">
        <p className="text-sm text-gray-500 mb-6">Order ID: {id.slice(0,8)}...</p>
        {STEPS.map((step, idx) => (
          <div key={step} className="flex items-start gap-4 mb-4">
            <div className={'w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold flex-shrink-0 ' +
              (idx <= currentIdx ? 'bg-yellow-400 text-gray-900' : 'bg-gray-100 text-gray-400')}>
              {idx < currentIdx ? '✓' : idx + 1}
            </div>
            <div className="pt-1">
              <p className={'font-semibold ' + (idx <= currentIdx ? 'text-gray-900' : 'text-gray-400')}>
                {STEP_LABELS[step]}
              </p>
              {idx === currentIdx && <p className="text-xs text-yellow-600 mt-0.5">Current status</p>}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
