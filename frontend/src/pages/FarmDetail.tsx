import { useEffect, useMemo, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { apiFetch } from '../lib/api';

interface Farm {
    id: number;
    name: string;
    city: string | null;
}

interface Crop {
    id: number;
    name: string;
}

interface FarmCrop {
    id: number;
    farm_id: number;
    crop_id: number;
    started_at: number;
}

interface Harvest {
    id: number;
    farm_id: number;
    crop_id: number;
    weight_kg: string;
    created_at: number;
}

const PAGE = 200;

async function fetchAll<T>(path: string, farmId?: number): Promise<T[]> {
    const rows: T[] = [];
    for (let skip = 0; ; skip += PAGE) {
        const farm = farmId === undefined ? '' : `farm_id=${farmId}&`;
        const page = await apiFetch<T[]>(`${path}?${farm}skip=${skip}&limit=${PAGE}`);
        rows.push(...page);
        if (page.length < PAGE) return rows;
    }
}

function uniqueById<T extends { id: number }>(rows: T[]): T[] {
    return [...new Map(rows.map((row) => [row.id, row])).values()];
}

function formatDate(epochSeconds: number): string {
    return new Date(epochSeconds * 1000).toISOString().slice(0, 10);
}

function formatKg(value: number): string {
    return value.toLocaleString(undefined, { maximumFractionDigits: 1 });
}

export function FarmDetail() {
    const { farmId } = useParams();
    const id = Number(farmId);
    const validId = Number.isInteger(id);
    const [farm, setFarm] = useState<Farm | null>(null);
    const [crops, setCrops] = useState<Crop[]>([]);
    const [farmCrops, setFarmCrops] = useState<FarmCrop[]>([]);
    const [harvests, setHarvests] = useState<Harvest[]>([]);
    const [cropQuery, setCropQuery] = useState('');
    const [selectedCropId, setSelectedCropId] = useState<number | null>(null);
    const [dateFrom, setDateFrom] = useState('');
    const [dateTo, setDateTo] = useState('');
    const [error, setError] = useState<string | null>(validId ? null : 'Invalid farm.');
    const [loading, setLoading] = useState(validId);
    const [harvestsLoading, setHarvestsLoading] = useState(validId);
    const [trackedId, setTrackedId] = useState(id);

    if (id !== trackedId) {
        setTrackedId(id);
        setError(validId ? null : 'Invalid farm.');
        setLoading(validId);
        setHarvestsLoading(validId);
        setFarm(null);
        setHarvests([]);
    }

    useEffect(() => {
        if (!Number.isInteger(id)) return;
        let cancelled = false;

        async function load() {
            try {
                const [farmRow, cropRows, farmCropRows] = await Promise.all([
                    apiFetch<Farm>(`/farms/${id}`),
                    fetchAll<Crop>('/crops'),
                    fetchAll<FarmCrop>('/farm-crops', id),
                ]);
                if (cancelled) return;
                setFarm(farmRow);
                setCrops(cropRows);
                setFarmCrops(uniqueById(farmCropRows));
                setLoading(false);

                const harvestRows = await fetchAll<Harvest>('/harvests', id);
                if (cancelled) return;
                setHarvests(uniqueById(harvestRows));
            } catch (err: unknown) {
                if (!cancelled) setError(err instanceof Error ? err.message : 'Could not load farm.');
            } finally {
                if (!cancelled) {
                    setLoading(false);
                    setHarvestsLoading(false);
                }
            }
        }

        load();
        return () => {
            cancelled = true;
        };
    }, [id]);

    const cropName = useMemo(() => {
        const names = new Map(crops.map((crop) => [crop.id, crop.name]));
        return (cropId: number) => names.get(cropId) ?? `Crop ${cropId}`;
    }, [crops]);

    const q = cropQuery.trim().toLowerCase();
    const visibleCrops = farmCrops.filter((row) => !q || cropName(row.crop_id).toLowerCase().includes(q));

    const visibleHarvests = harvests.filter((row) => {
        if (selectedCropId !== null && row.crop_id !== selectedCropId) return false;
        if (selectedCropId === null && q && !cropName(row.crop_id).toLowerCase().includes(q)) return false;
        const date = formatDate(row.created_at);
        if (dateFrom && date < dateFrom) return false;
        if (dateTo && date > dateTo) return false;
        return true;
    });

    const byCrop = new Map<number, Harvest[]>();
    for (const row of visibleHarvests) {
        const list = byCrop.get(row.crop_id) ?? [];
        list.push(row);
        byCrop.set(row.crop_id, list);
    }
    const groups = [...byCrop.entries()]
        .map(([cropId, rows]) => {
            const dates = rows.map((row) => formatDate(row.created_at)).sort();
            const totalKg = rows.reduce((sum, row) => sum + Number(row.weight_kg), 0);
            return {
                cropId,
                name: cropName(cropId),
                count: rows.length,
                totalKg,
                from: dates[0] ?? '',
                to: dates[dates.length - 1] ?? '',
                rows: rows.slice().sort((a, b) => b.created_at - a.created_at),
            };
        })
        .sort((a, b) => b.totalKg - a.totalKg);

    function toggleCrop(cropId: number) {
        setSelectedCropId((current) => (current === cropId ? null : cropId));
    }

    return (
        <div className="mx-auto max-w-6xl">
            <Link to="/" className="text-sm text-brand-dark hover:underline">Back to farms</Link>
            {loading && <p className="mt-4 text-sm text-ink-muted">Loading…</p>}
            {error && <p className="mt-4 text-sm text-red-600">{error}</p>}
            {farm && (
                <>
                    <h1 className="mt-2 text-xl font-bold text-brand-dark">{farm.name}</h1>
                    <p className="mb-6 text-sm text-ink-muted">{farm.city ?? '—'}</p>

                    <div className="grid items-start gap-6 lg:grid-cols-2">
                        <section className="rounded-lg border border-brand-muted/40 bg-white p-4">
                            <h2 className="mb-3 text-base font-semibold text-brand-dark">Crops ({visibleCrops.length})</h2>
                            <input
                                value={cropQuery}
                                onChange={(e) => setCropQuery(e.target.value)}
                                placeholder="Crop name"
                                className="mb-3 w-full rounded-md border border-brand-muted px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand"
                            />
                            <ul className="max-h-[32rem] divide-y divide-brand-muted/30 overflow-y-auto">
                                {visibleCrops.map((row) => {
                                    const selected = selectedCropId === row.crop_id;
                                    return (
                                        <li key={row.id}>
                                            <button
                                                type="button"
                                                onClick={() => toggleCrop(row.crop_id)}
                                                className={`flex w-full items-center justify-between px-2 py-2 text-left text-sm ${selected ? 'bg-brand/15' : 'hover:bg-surface'}`}
                                            >
                                                <span className="font-medium text-brand-dark">{cropName(row.crop_id)}</span>
                                                <span className="text-ink-muted">since {formatDate(row.started_at)}</span>
                                            </button>
                                        </li>
                                    );
                                })}
                                {visibleCrops.length === 0 && <li className="px-2 py-3 text-sm text-ink-muted">No crops match.</li>}
                            </ul>
                        </section>

                        <section className="rounded-lg border border-brand-muted/40 bg-white p-4">
                            <h2 className="mb-3 text-base font-semibold text-brand-dark">
                                Harvests ({visibleHarvests.length}){harvestsLoading ? ' · loading…' : ''}
                            </h2>
                            <div className="mb-3 flex gap-2">
                                <label className="flex flex-1 flex-col text-xs text-ink-muted">
                                    From
                                    <input
                                        type="date"
                                        value={dateFrom}
                                        onChange={(e) => setDateFrom(e.target.value)}
                                        className="mt-1 rounded-md border border-brand-muted px-2 py-2 text-sm text-ink focus:outline-none focus:ring-2 focus:ring-brand"
                                    />
                                </label>
                                <label className="flex flex-1 flex-col text-xs text-ink-muted">
                                    To
                                    <input
                                        type="date"
                                        value={dateTo}
                                        onChange={(e) => setDateTo(e.target.value)}
                                        className="mt-1 rounded-md border border-brand-muted px-2 py-2 text-sm text-ink focus:outline-none focus:ring-2 focus:ring-brand"
                                    />
                                </label>
                            </div>
                            <div className="flex max-h-[32rem] flex-col gap-2 overflow-y-auto">
                                {groups.map((group) => (
                                    <details key={group.cropId} className="rounded-md border border-brand-muted/30">
                                        <summary className="cursor-pointer px-3 py-2 text-sm">
                                            <span className="font-medium text-brand-dark">{group.name}</span>
                                            <span className="mt-0.5 block text-ink-muted">
                                                {group.count} harvests · {formatKg(group.totalKg)} kg · {group.from} – {group.to}
                                            </span>
                                        </summary>
                                        <ul className="divide-y divide-brand-muted/20 border-t border-brand-muted/30">
                                            {group.rows.map((row) => (
                                                <li key={row.id} className="flex justify-between px-3 py-1.5 text-xs text-ink-muted">
                                                    <span>{formatDate(row.created_at)}</span>
                                                    <span>{row.weight_kg} kg</span>
                                                </li>
                                            ))}
                                        </ul>
                                    </details>
                                ))}
                                {groups.length === 0 && <p className="text-sm text-ink-muted">No harvests match.</p>}
                            </div>
                        </section>
                    </div>
                </>
            )}
        </div>
    );
}