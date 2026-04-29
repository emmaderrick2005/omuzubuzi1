import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate, Link } from 'react-router-dom';
import { authAPI } from '../utils/api';
import { useAuthStore } from '../store';
import toast from 'react-hot-toast';

export default function LoginPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { setAuth } = useAuthStore();
  const [step, setStep] = useState(1); // 1=phone, 2=OTP
  const [phone, setPhone] = useState('');
  const [otp, setOtp] = useState('');
  const [loading, setLoading] = useState(false);

  const sendOTP = async () => {
    if (!phone.match(/^\+256[0-9]{9}$/)) {
      toast.error('Enter a valid Uganda phone number: +256XXXXXXXXX');
      return;
    }
    setLoading(true);
    try {
      await authAPI.login(phone);
      setStep(2);
      toast.success('OTP sent to your phone!');
    } catch (e) {
      toast.error(e.response?.data?.detail || t('error'));
    } finally {
      setLoading(false);
    }
  };

  const verifyOTP = async () => {
    setLoading(true);
    try {
      const res = await authAPI.loginVerify({ phone, otp });
      const { access_token, user_id, role, language } = res.data;
      setAuth({ id: user_id, role, language }, access_token);
      toast.success('Welcome back!');
      navigate('/');
    } catch (e) {
      toast.error(e.response?.data?.detail || t('error'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-yellow-50 flex items-center justify-center px-4">
      <div className="bg-white rounded-2xl shadow-xl p-8 w-full max-w-sm">
        <h1 className="text-3xl font-black text-center mb-2">🛒 Omuzubuzi</h1>
        <p className="text-center text-gray-500 text-sm mb-6">{t('tagline')}</p>

        {step === 1 ? (
          <>
            <label className="block text-sm font-semibold mb-1">{t('phone')}</label>
            <input type="tel" value={phone} onChange={(e) => setPhone(e.target.value)}
              placeholder={t('phone_placeholder')}
              className="w-full border-2 border-gray-200 rounded-xl p-3 text-lg mb-4 focus:border-yellow-400 outline-none"
            />
            <button onClick={sendOTP} disabled={loading}
              className="w-full bg-yellow-400 hover:bg-yellow-500 text-gray-900 font-bold py-3 rounded-xl text-lg disabled:opacity-50">
              {loading ? t('loading') : t('send_otp')}
            </button>
          </>
        ) : (
          <>
            <p className="text-sm text-gray-600 mb-3">{t('enter_otp')} <strong>{phone}</strong></p>
            <input type="number" value={otp} onChange={(e) => setOtp(e.target.value)}
              placeholder="123456" maxLength={6}
              className="w-full border-2 border-gray-200 rounded-xl p-3 text-2xl text-center tracking-widest mb-4 focus:border-yellow-400 outline-none"
            />
            <button onClick={verifyOTP} disabled={loading}
              className="w-full bg-yellow-400 hover:bg-yellow-500 text-gray-900 font-bold py-3 rounded-xl text-lg disabled:opacity-50">
              {loading ? t('loading') : t('verify')}
            </button>
            <button onClick={() => setStep(1)} className="w-full mt-2 text-sm text-gray-500 underline">Change number</button>
          </>
        )}
        <p className="text-center mt-4 text-sm text-gray-500">
          New? <Link to="/register" className="text-yellow-600 font-semibold">{t('register')}</Link>
        </p>
      </div>
    </div>
  );
}
