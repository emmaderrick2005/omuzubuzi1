import React from 'react';
import { useAuthStore } from '../store';
export default function WholesalerDashboardPage() {
  const { user } = useAuthStore();
  return (
    <div>
      <h2 className="text-2xl font-black mb-4">📊 Wholesaler Dashboard</h2>
      <div className="grid grid-cols-2 gap-4">
        {[['Total Orders','0'],['Revenue','UGX 0'],['Pending','0'],['Rating','5.0 ⭐']].map(([k,v]) => (
          <div key={k} className="bg-white rounded-2xl shadow p-4">
            <p className="text-gray-500 text-sm">{k}</p>
            <p className="text-2xl font-black">{v}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
