import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate, Link } from 'react-router-dom';
import { authAPI } from '../utils/api';
import { useAuthStore } from '../store';
import i18n from '../i18n';
import toast from 'react-hot-toast';

const ROLES = ['buyer', 'wholesaler', 'delivery_partner'];
const ROLE_LABELS = { buyer: 'role_buyer', wholesaler: 'role_wholesaler', delivery_partner: 'role_delivery' };

export default function RegisterPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { setAuth, setLanguage } = useAuthStore();
  const [step, setStep] = useState(1);
  const [form, setForm] = useState({ phone: '', name: '', role: 'buyer', language: 'en' });
  const [otp, setOtp] = useState('');
  const [loading, setLoading] = useState(false);

  const selectLang = (lang) => {
    setForm((f) => ({ ...f, language: lang }));
    i18n.changeLanguage(lang);
    setLanguage(lang);
  };

  const sendOTP = async () => {
    if (!form.phone.match(/^\+256[0-9]{9}$/)) { toast.error('Enter a valid Uganda phone: +256XXXXXXXXX'); return; }
    setLoading(true);
    try {
      await authAPI.register(form);
      setStep(2);
      toast.success('OTP sent!');
    } catch (e) {
      toast.error(e.response?.data?.detail || t('error'));
    } finally { setLoading(false); }
  };

  const verify = async () => {
    setLoading(true);
    try {
      const res = await authAPI.verifyOTP({ phone: form.phone, otp });
      const { access_token, user_id, role, language } = res.data;
      setAuth({ id: user_id, role, language }, access_token);
      toast.success('Account created!');
      navigate('/');
    } catch (e) {
      toast.error(e.response?.data?.detail || t('error'));
    } finally { setLoading(false); }
  };

  return (
    <div className="min-h-screen bg-yellow-50 flex items-center justify-center px-4">
      <div className="bg-white rounded-2xl shadow-xl p-8 w-full max-w-sm">
        <h1 className="text-3xl font-black text-center mb-6">🛒 {t('register')}</h1>

        {step === 1 && (
          <>
            {/* Language toggle — FR-01-06 */}
            <div className="mb-4">
              <p className="text-sm font-semibold mb-2">{t('language')}</p>
              <div className="flex gap-2">
                {['en', 'lg'].map((l) => (
                  <button key={l} onClick={() => selectLang(l)}
                    className={'flex-1 py-2 rounded-xl border-2 font-semibold ' + (form.language === l ? 'border-yellow-400 bg-yellow-50' : 'border-gray-200')}>
                    {l === 'en' ? '🇬🇧 English' : '🇺🇬 Luganda'}
                  </button>
                ))}
              </div>
            </div>

            <input type="text" placeholder={t('name')} value={form.name} onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
              className="w-full border-2 border-gray-200 rounded-xl p-3 mb-3 focus:border-yellow-400 outline-none" />
            <input type="tel" placeholder={t('phone_placeholder')} value={form.phone} onChange={(e) => setForm((f) => ({ ...f, phone: e.target.value }))}
              className="w-full border-2 border-gray-200 rounded-xl p-3 mb-3 focus:border-yellow-400 outline-none" />

            <p className="text-sm font-semibold mb-2">I am a...</p>
            {ROLES.map((r) => (
              <button key={r} onClick={() => setForm((f) => ({ ...f, role: r }))}
                className={'w-full text-left p-3 rounded-xl border-2 mb-2 font-medium ' + (form.role === r ? 'border-yellow-400 bg-yellow-50' : 'border-gray-200')}>
                {t(ROLE_LABELS[r])}
              </button>
            ))}

            <button onClick={sendOTP} disabled={loading}
              className="w-full bg-yellow-400 hover:bg-yellow-500 text-gray-900 font-bold py-3 rounded-xl mt-2 disabled:opacity-50">
              {loading ? t('loading') : t('send_otp')}
            </button>
          </>
        )}

        {step === 2 && (
          <>
            <p className="text-gray-600 mb-3">{t('enter_otp')} <strong>{form.phone}</strong></p>
            <input type="number" value={otp} onChange={(e) => setOtp(e.target.value)} placeholder="123456" maxLength={6}
              className="w-full border-2 border-gray-200 rounded-xl p-3 text-2xl text-center tracking-widest mb-4 focus:border-yellow-400 outline-none" />
            <button onClick={verify} disabled={loading}
              className="w-full bg-yellow-400 text-gray-900 font-bold py-3 rounded-xl disabled:opacity-50">
              {loading ? t('loading') : t('verify')}
            </button>
          </>
        )}

        <p className="text-center mt-4 text-sm text-gray-500">
          Already have an account? <Link to="/login" className="text-yellow-600 font-semibold">{t('login')}</Link>
        </p>
      </div>
    </div>
  );
}
