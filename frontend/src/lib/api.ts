const API_BASE = '/api';
const PAGE_SIZE = 200;

export class ApiError extends Error {
    status: number;
    constructor(status: number, message: string) {
        super(message);
        this.status = status;
    }
}

// FastAPI returns `detail` as a string for HTTPException and as a list of
// `{ msg }` objects for request validation errors (422).
function errorMessage(detail: unknown): string {
    if (typeof detail === 'string') return detail;
    if (Array.isArray(detail)) {
        const messages = detail
            .map((item) => (typeof item?.msg === 'string' ? item.msg : null))
            .filter((msg): msg is string => msg !== null);
        if (messages.length > 0) return messages.join('; ');
    }
    return 'Something went wrong';
}

export async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
    const token = localStorage.getItem('token');

    const res = await fetch(`${API_BASE}${path}`, {
        ...options,
        headers: {
            'Content-Type': 'application/json',
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
            ...options.headers,
        },
    });

    if (!res.ok) {
        const body = await res.json().catch(() => null);
        throw new ApiError(res.status, errorMessage(body?.detail));
    }

    return res.json();
}

// Reads every page of a list endpoint; the API caps `limit` at 200.
export async function fetchAll<T>(path: string, farmId?: number): Promise<T[]> {
    const rows: T[] = [];
    for (let skip = 0; ; skip += PAGE_SIZE) {
        const farm = farmId === undefined ? '' : `farm_id=${farmId}&`;
        const page = await apiFetch<T[]>(`${path}?${farm}skip=${skip}&limit=${PAGE_SIZE}`);
        rows.push(...page);
        if (page.length < PAGE_SIZE) return rows;
    }
}
