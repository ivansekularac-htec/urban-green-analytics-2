import { useAuth } from '../context/AuthContext';

function getInitials(fullName: string): string {
    const parts = fullName.trim().split(/\s+/);
    const first = parts[0]?.[0] ?? '';
    const last = parts.length > 1 ? parts[parts.length - 1][0] : '';
    return (first + last).toUpperCase();
}

function splitName(fullName: string): { first: string; last: string } {
    const parts = fullName.trim().split(/\s+/);
    if (parts.length === 1) {
        return { first: parts[0], last: '—' };
    }
    return { first: parts[0], last: parts.slice(1).join(' ') };
}

export function Profile() {
    const { user } = useAuth();

    if (!user) {
        return null;
    }

    const { first, last } = splitName(user.full_name);

    return (
        <div className="flex h-full items-center justify-center">
            <div className="w-full max-w-3xl">
                <div className="mb-4 flex items-center gap-4">
                    <h1 className="whitespace-nowrap text-xl font-bold text-brand-dark">My Profile</h1>
                    <div className="h-px flex-1 bg-brand-muted/40" />
                </div>

                <div className="flex flex-col gap-4">
                    {/* Card 1: avatar + name */}
                    <div className="flex items-center gap-4 rounded-lg border border-brand-muted/40 bg-white p-6">
                        <div className="flex h-16 w-16 shrink-0 items-center justify-center rounded-full border-4 border-brand-dark bg-brand-muted/20">
                            <span className="text-lg font-semibold text-brand-dark">{getInitials(user.full_name)}</span>
                        </div>
                        <div>
                            <p className="text-lg font-bold text-brand-dark">{user.full_name}</p>
                            <p className="text-sm text-ink-muted">{user.roles[0] ?? 'User'}</p>
                        </div>
                    </div>

                    {/* Card 2: personal information */}
                    <div className="rounded-lg border border-brand-muted/40 bg-white p-6">
                        <h2 className="mb-4 text-base font-semibold text-brand-dark">Personal Information</h2>
                        <div className="mb-4 h-px w-full bg-brand-muted/40" />
                        <dl className="space-y-4">
                            <div className="flex gap-48">
                                <div>
                                    <dt className="text-sm text-ink-muted">First Name</dt>
                                    <dd className="text-ink">{first}</dd>
                                </div>
                                <div>
                                    <dt className="text-sm text-ink-muted">Last Name</dt>
                                    <dd className="text-ink">{last}</dd>
                                </div>
                            </div>
                            <div>
                                <dt className="text-sm text-ink-muted">Email</dt>
                                <dd className="text-ink">{user.email}</dd>
                            </div>
                        </dl>
                    </div>

                    {/* Card 3: roles */}
                    <div className="rounded-lg border border-brand-muted/40 bg-white p-6">
                        <h2 className="mb-4 text-base font-semibold text-brand-dark">Roles</h2>
                        <div className="mb-4 h-px w-full bg-brand-muted/40" />
                        <div className="flex flex-wrap gap-2">
                            {user.roles.map((role) => (
                                <span
                                    key={role}
                                    className="rounded-full bg-brand-muted/20 px-3 py-1 text-xs font-medium text-brand-dark"
                                >
                                    {role}
                                </span>
                            ))}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
