import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import en from './en.json';
import lg from './lg.json';
i18n.use(initReactI18next).init({
  resources: { en: { translation: en }, lg: { translation: lg } },
  lng: localStorage.getItem('omz_lang') || 'en',
  fallbackLng: 'en',
  interpolation: { escapeValue: false },
});
export default i18n;
