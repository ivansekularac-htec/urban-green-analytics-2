import { type ReactNode } from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

// Sends users without `role` back to Home. The API enforces the same rule;
// this only keeps them off a page whose every request would be a 403.
export function RequireRole({ role, children }: { role: string; children: ReactNode }) {
    const { user } = useAuth();

    if (!user) {
        return null;
    }

    if (!user.roles.includes(role)) {
        return <Navigate to="/" replace />;
    }

    return children;
}
