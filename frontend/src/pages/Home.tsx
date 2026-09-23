import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { apiFetch } from '../lib/api';

interface Farm {
    id: number;
    name: string;
    city: string | null;
    status: string;
}

export function Home() {
    const [farms, setFarms] = useState<Farm[]>([]);
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        let cancelled = false;
        apiFetch<Farm[]>('/farms?limit=200')
            .then((rows) => {
                if (!cancelled) setFarms(rows);
            })
            .catch((err: unknown) => {
                if (!cancelled) setError(err instanceof Error ? err.message : 'Could not load farms.');
            })
            .finally(() => {
                if (!cancelled) setLoading(false);
            });
        return () => {
            cancelled = true;
        };
    }, []);

    return (
        <div className="mx-auto max-w-5xl">
            <h1 className="mb-6 text-xl font-bold text-brand-dark">Farms</h1>
            {loading && <p className="text-sm text-ink-muted">Loading farms…</p>}
            {error && <p className="text-sm text-red-600">{error}</p>}
            {!loading && !error && farms.length === 0 && (
                <p className="text-sm text-ink-muted">No farms assigned.</p>
            )}
            <ul className="grid gap-3 sm:grid-cols-2">
                {farms.map((farm) => (
                    <li key={farm.id}>
                        <Link
                            to={`/farms/${farm.id}`}
                            className="block rounded-lg border border-brand-muted/40 bg-white p-4 hover:border-brand"
                        >
                            <p className="font-semibold text-brand-dark">{farm.name}</p>
                            <p className="text-sm text-ink-muted">{farm.city ?? '—'}</p>
                            <p className="mt-2 text-xs text-ink-muted">{farm.status}</p>
                        </Link>
                    </li>
                ))}
            </ul>
        </div>
    );
}