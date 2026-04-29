import { create } from 'zustand';
import { persist } from 'zustand/middleware';
export const useAuthStore = create(persist((set) => ({ user: null, token: null, language: 'en',
  setAuth: (user, token) => { localStorage.setItem('omz_token', token); set({ user, token }); },
  setLanguage: (lang) => { localStorage.setItem('omz_lang', lang); set({ language: lang }); },
  logout: () => { localStorage.removeItem('omz_token'); set({ user: null, token: null }); },
}), { name: 'omz_auth', partialize: (s) => ({ user: s.user, language: s.language }) }));
export const useCartStore = create((set, get) => ({
  items: [], wholesaler_id: null,
  addItem: (product, qty) => {
    const ex = get().items.find((i) => i.product.id === product.id);
    if (ex) set({ items: get().items.map((i) => i.product.id === product.id ? { ...i, quantity: i.quantity + qty } : i) });
    else set({ items: [...get().items, { product, quantity: qty }], wholesaler_id: product.wholesaler_id });
  },
  removeItem: (pid) => set({ items: get().items.filter((i) => i.product.id !== pid) }),
  clear: () => set({ items: [], wholesaler_id: null }),
  total: () => get().items.reduce((s, i) => s + i.product.base_price * i.quantity, 0),
}));
