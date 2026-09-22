import { createContext, useContext, useState, useCallback, useEffect, type ReactNode } from 'react';
import { apiFetch } from '../lib/api';
import type { CurrentUser } from '../types/user';

interface AuthContextValue {
    token: string | null;
    user: CurrentUser | null;
    isAuthenticated: boolean;
    isLoading: boolean;
    login: (token: string) => Promise<void>;
    logout: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
    const [token, setToken] = useState<string | null>(() => localStorage.getItem('token'));
    const [user, setUser] = useState<CurrentUser | null>(null);
    const [isLoading, setIsLoading] = useState(true);

    const fetchUser = useCallback(async () => {
        try {
            const me = await apiFetch<CurrentUser>('/auth/me');
            setUser(me);
        } catch {
            localStorage.removeItem('token');
            setToken(null);
            setUser(null);
        }
    }, []);

    useEffect(() => {
        if (!token) {
            setIsLoading(false);
            return;
        }
        setIsLoading(true);
        fetchUser().finally(() => setIsLoading(false));
    }, []);

    const login = useCallback(async (newToken: string) => {
        localStorage.setItem('token', newToken);
        setToken(newToken);
        await fetchUser();
    }, [fetchUser]);

    const logout = useCallback(() => {
        localStorage.removeItem('token');
        setToken(null);
        setUser(null);
    }, []);

    return (
        <AuthContext.Provider value={{ token, user, isAuthenticated: !!token, isLoading, login, logout }}>
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth() {
    const ctx = useContext(AuthContext);
    if (!ctx) throw new Error('useAuth must be used within AuthProvider');
    return ctx;
}
