import { useState, type SubmitEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import logo from '../assets/logo.png';
import sensorNetwork from '../assets/sensor-network.jpg';

export function Login() {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState<string | null>(null);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const { login } = useAuth();
    const navigate = useNavigate();

    async function handleSubmit(e: SubmitEvent<HTMLFormElement>) {
        e.preventDefault();
        setError(null);
        setIsSubmitting(true);

        try {
            const res = await fetch('/api/auth/login', {
                method: 'POST',
                body: new URLSearchParams({ username: email, password }),
            });

            if (!res.ok) {
                const body = await res.json().catch(() => null);
                throw new Error(body?.detail ?? 'Incorrect email or password.');
            }

            const data = await res.json();
            login(data.access_token);
            navigate('/');
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Something went wrong.');
        } finally {
            setIsSubmitting(false);
        }
    }

    return (
        <div className="flex min-h-screen">
            {/* Brand panel */}
            <div className="relative hidden w-1/2 items-center justify-center overflow-hidden bg-panel px-12 md:flex">
                <div
                    className="absolute inset-0 bg-cover bg-top"
                    style={{
                        backgroundImage: `linear-gradient(rgba(220,238,228,0.82), rgba(220,238,228,0.82)), url(${sensorNetwork})`,
                    }}
                />

                <div className="relative flex w-full items-center gap-6">
                    <img src={logo} alt="Urban Green Analytics" className="w-44 shrink-0 lg:w-56" />
                    <div className="h-16 w-1 shrink-0 rounded-full bg-brand-deep" />
                    <p className="text-lg text-brand-deep">
                        Real-time sensor monitoring and analytics for your farms.
                    </p>
                </div>
            </div>

            {/* Form */}
            <div className="flex flex-1 items-center justify-center bg-white px-6">
                <form onSubmit={handleSubmit} className="w-full max-w-sm">
                    <h2 className="mb-6 text-xl font-semibold text-ink">Log in</h2>

                    <label className="mb-1 block text-sm text-ink-muted" htmlFor="email">Email</label>
                    <input
                        id="email"
                        type="email"
                        required
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        className="mb-4 w-full rounded-md border border-brand-muted px-3 py-2 focus:outline-none focus:ring-2 focus:ring-brand"
                    />

                    <label className="mb-1 block text-sm text-ink-muted" htmlFor="password">Password</label>
                    <input
                        id="password"
                        type="password"
                        required
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        className="mb-4 w-full rounded-md border border-brand-muted px-3 py-2 focus:outline-none focus:ring-2 focus:ring-brand"
                    />

                    {error && <p className="mb-4 text-sm text-red-600">{error}</p>}

                    <button
                        type="submit"
                        disabled={isSubmitting}
                        className="w-full rounded-md bg-brand py-2 font-medium text-white hover:opacity-90 disabled:opacity-60"
                    >
                        {isSubmitting ? 'Logging in…' : 'Log in'}
                    </button>
                </form>
            </div>
        </div>
    );
}
