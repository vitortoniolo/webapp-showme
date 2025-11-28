const API_BASE_URL = 'http://localhost:8000';

const Auth = {
  storageKey: 'showme_auth',
  apiBase: API_BASE_URL,
  getState() {
    try {
      const raw = localStorage.getItem(this.storageKey);
      return raw ? JSON.parse(raw) : null;
    } catch (error) {
      console.warn('Erro ao ler autenticação', error);
      return null;
    }
  },
  saveState(payload) {
    localStorage.setItem(this.storageKey, JSON.stringify(payload));
    this.notify();
  },
  clearState() {
    localStorage.removeItem(this.storageKey);
    this.notify();
  },
  notify() {
    const detail = this.getState();
    document.dispatchEvent(new CustomEvent('auth:changed', { detail }));
  },
  getToken() {
    return this.getState()?.token || null;
  },
  getUser() {
    return this.getState()?.user || null;
  },
  isAuthenticated() {
    return Boolean(this.getToken());
  },
  buildAuthHeaders(headers = {}) {
    const token = this.getToken();
    if (!token) return headers;
    return { ...headers, Authorization: `Bearer ${token}` };
  },
  async login(email, password) {
    const res = await fetch(`${this.apiBase}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      throw new Error(data?.detail || 'Não foi possível entrar.');
    }
    const payload = await res.json();
    this.saveState(payload);
    return payload;
  },
  async signup({ email, password, name }) {
    const res = await fetch(`${this.apiBase}/auth/signup`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password, name })
    });
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      throw new Error(data?.detail || 'Não foi possível criar a conta.');
    }
    const payload = await res.json();
    this.saveState(payload);
    return payload;
  },
  async logout() {
    const token = this.getToken();
    try {
      if (token) {
        await fetch(`${this.apiBase}/auth/logout`, {
          method: 'POST',
          headers: this.buildAuthHeaders({})
        });
      }
    } catch (error) {
      console.warn('Erro ao encerrar sessão', error);
    } finally {
      this.clearState();
    }
  },
  onChange(callback) {
    const handler = (event) => callback(event.detail);
    document.addEventListener('auth:changed', handler);
    // Emite valor inicial
    callback(this.getState());
    return () => document.removeEventListener('auth:changed', handler);
  }
};

function authMenu() {
  return {
    user: Auth.getUser(),
    loading: false,
    init() {
      Auth.onChange((state) => {
        this.user = state?.user || null;
      });
    },
    async logout() {
      this.loading = true;
      await Auth.logout();
      this.loading = false;
    }
  };
}

function accountApp() {
  return {
    apiBase: API_BASE_URL,
    mode: 'login',
  loading: false,
  error: '',
  success: '',
  user: Auth.getUser(),
  loginForm: {
    email: '',
    password: ''
  },
  signupForm: {
    name: '',
    email: '',
    password: ''
  },
  init() {
      Auth.onChange((state) => {
        this.user = state?.user || null;
      });
    },
    async submitLogin() {
    this.loading = true;
    this.error = '';
    this.success = '';
    try {
      await Auth.login(this.loginForm.email, this.loginForm.password);
      this.success = 'Login realizado. Redirecionando para o painel...';
      setTimeout(() => {
        window.location.href = 'admin-events.html';
      }, 1000);
    } catch (error) {
        this.error = error?.message || 'Falha ao entrar.';
      } finally {
        this.loading = false;
      }
    },
    async submitSignup() {
    this.loading = true;
    this.error = '';
    this.success = '';
    try {
      await Auth.signup({
        email: this.signupForm.email,
        password: this.signupForm.password,
        name: this.signupForm.name
      });
      this.success = 'Conta criada! Redirecionando...';
      setTimeout(() => {
        window.location.href = 'admin-events.html';
      }, 1000);
      } catch (error) {
        this.error = error?.message || 'Falha ao criar conta.';
      } finally {
        this.loading = false;
      }
    },
    async logout() {
      await Auth.logout();
    }
  };
}

window.Auth = Auth;
window.authMenu = authMenu;
window.accountApp = accountApp;
