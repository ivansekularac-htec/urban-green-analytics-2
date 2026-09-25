import { useEffect, useMemo, useState, type ReactNode, type SubmitEvent } from 'react';
import { ApiError, apiFetch, fetchAll } from '../lib/api';
import { ADMIN_ROLE, type Role, type User, type UserRole } from '../types/user';

interface Farm {
    id: number;
    name: string;
}

type Notice = { kind: 'success' | 'error'; text: string } | null;

const inputClass =
    'w-full rounded-md border border-brand-muted px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand disabled:bg-surface disabled:text-ink-muted';
const labelClass = 'mb-1 block text-sm text-ink-muted';
const buttonClass =
    'w-full rounded-md bg-brand py-2 text-sm font-medium text-white hover:opacity-90 disabled:opacity-60';

function errorText(err: unknown, fallback: string): string {
    return err instanceof Error ? err.message : fallback;
}

function byName<T>(rows: T[], name: (row: T) => string): T[] {
    return rows.slice().sort((a, b) => name(a).localeCompare(name(b)));
}

function Card({ title, children }: { title: string; children: ReactNode }) {
    return (
        <section className="rounded-lg border border-brand-muted/40 bg-white p-6">
            <h2 className="mb-4 text-base font-semibold text-brand-dark">{title}</h2>
            <div className="mb-4 h-px w-full bg-brand-muted/40" />
            {children}
        </section>
    );
}

function NoticeLine({ notice }: { notice: Notice }) {
    if (!notice) return null;
    const color = notice.kind === 'success' ? 'font-medium text-brand' : 'text-red-600';
    return <p role="status" className={`mb-4 text-sm ${color}`}>{notice.text}</p>;
}

function CreateUserForm({ onCreated }: { onCreated: (user: User) => void }) {
    const [email, setEmail] = useState('');
    const [fullName, setFullName] = useState('');
    const [password, setPassword] = useState('');
    const [notice, setNotice] = useState<Notice>(null);
    const [isSubmitting, setIsSubmitting] = useState(false);

    async function handleSubmit(e: SubmitEvent<HTMLFormElement>) {
        e.preventDefault();
        setNotice(null);
        setIsSubmitting(true);
        try {
            const created = await apiFetch<User>('/users', {
                method: 'POST',
                body: JSON.stringify({ email, full_name: fullName, password }),
            });
            setEmail('');
            setFullName('');
            setPassword('');
            setNotice({ kind: 'success', text: `Created ${created.email}.` });
            onCreated(created);
        } catch (err) {
            // Email is the only unique column on users, so a 409 here means it is taken.
            const text = err instanceof ApiError && err.status === 409
                ? 'A user with this email already exists.'
                : errorText(err, 'Could not create user.');
            setNotice({ kind: 'error', text });
        } finally {
            setIsSubmitting(false);
        }
    }

    return (
        <Card title="Create user">
            <form onSubmit={handleSubmit}>
                <label className={labelClass} htmlFor="new-email">Email</label>
                <input
                    id="new-email"
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className={`${inputClass} mb-4`}
                />

                <label className={labelClass} htmlFor="new-name">Full name</label>
                <input
                    id="new-name"
                    required
                    maxLength={255}
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    className={`${inputClass} mb-4`}
                />

                <label className={labelClass} htmlFor="new-password">Password</label>
                <input
                    id="new-password"
                    type="password"
                    required
                    minLength={8}
                    maxLength={255}
                    autoComplete="new-password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className={`${inputClass} mb-1`}
                />
                <p className="mb-4 text-xs text-ink-muted">At least 8 characters.</p>

                <NoticeLine notice={notice} />

                <button type="submit" disabled={isSubmitting} className={buttonClass}>
                    {isSubmitting ? 'Creating…' : 'Create user'}
                </button>
            </form>
        </Card>
    );
}

interface AssignRoleFormProps {
    users: User[];
    roles: Role[];
    farms: Farm[];
    assignments: UserRole[];
    userId: string;
    onUserChange: (userId: string) => void;
    onAssigned: () => void;
}

function AssignRoleForm({ users, roles, farms, assignments, userId, onUserChange, onAssigned }: AssignRoleFormProps) {
    const [roleId, setRoleId] = useState('');
    const [farmId, setFarmId] = useState('');
    const [notice, setNotice] = useState<Notice>(null);
    const [isSubmitting, setIsSubmitting] = useState(false);

    const role = roles.find((row) => String(row.id) === roleId);
    // Admin is not scoped to a farm: the API treats it as access to every farm.
    const isAdminRole = role?.name === ADMIN_ROLE;
    const targetFarmId = isAdminRole || farmId === '' ? null : Number(farmId);
    const isComplete = userId !== '' && role !== undefined && (isAdminRole || targetFarmId !== null);
    const isDuplicate =
        isComplete &&
        assignments.some(
            (row) => row.user_id === Number(userId) && row.role_id === role.id && row.farm_id === targetFarmId,
        );

    async function handleSubmit(e: SubmitEvent<HTMLFormElement>) {
        e.preventDefault();
        if (!isComplete || isDuplicate) return;
        setNotice(null);
        setIsSubmitting(true);
        try {
            await apiFetch<UserRole>('/user-roles', {
                method: 'POST',
                body: JSON.stringify({ user_id: Number(userId), role_id: role.id, farm_id: targetFarmId }),
            });
            const user = users.find((row) => String(row.id) === userId);
            const farm = farms.find((row) => row.id === targetFarmId);
            const scope = farm ? ` on ${farm.name}` : '';
            setNotice({ kind: 'success', text: `Assigned ${role.name}${scope} to ${user?.full_name ?? 'user'}.` });
            setFarmId('');
            onAssigned();
        } catch (err) {
            setNotice({ kind: 'error', text: errorText(err, 'Could not assign role.') });
        } finally {
            setIsSubmitting(false);
        }
    }

    return (
        <Card title="Assign role and farm">
            <form onSubmit={handleSubmit}>
                <label className={labelClass} htmlFor="assign-user">User</label>
                <select
                    id="assign-user"
                    required
                    value={userId}
                    onChange={(e) => onUserChange(e.target.value)}
                    className={`${inputClass} mb-4`}
                >
                    <option value="">Select a user</option>
                    {byName(users, (row) => row.full_name).map((row) => (
                        <option key={row.id} value={row.id}>{row.full_name} ({row.email})</option>
                    ))}
                </select>

                <label className={labelClass} htmlFor="assign-role">Role</label>
                <select
                    id="assign-role"
                    required
                    value={roleId}
                    onChange={(e) => setRoleId(e.target.value)}
                    className={`${inputClass} mb-4`}
                >
                    <option value="">Select a role</option>
                    {byName(roles, (row) => row.name).map((row) => (
                        <option key={row.id} value={row.id}>{row.name}</option>
                    ))}
                </select>

                <label className={labelClass} htmlFor="assign-farm">Farm</label>
                <select
                    id="assign-farm"
                    required={!isAdminRole}
                    disabled={isAdminRole}
                    value={isAdminRole ? '' : farmId}
                    onChange={(e) => setFarmId(e.target.value)}
                    className={`${inputClass} mb-1`}
                >
                    <option value="">{isAdminRole ? 'All farms' : 'Select a farm'}</option>
                    {byName(farms, (row) => row.name).map((row) => (
                        <option key={row.id} value={row.id}>{row.name}</option>
                    ))}
                </select>
                <p className="mb-4 text-xs text-ink-muted">
                    {isDuplicate
                        ? 'This user already has this assignment.'
                        : isAdminRole
                          ? 'Admin has access to every farm.'
                          : 'The farm appears on the user’s Home.'}
                </p>

                <NoticeLine notice={notice} />

                <button type="submit" disabled={isSubmitting || !isComplete || isDuplicate} className={buttonClass}>
                    {isSubmitting ? 'Assigning…' : 'Assign'}
                </button>
            </form>
        </Card>
    );
}

export function Users() {
    const [users, setUsers] = useState<User[]>([]);
    const [roles, setRoles] = useState<Role[]>([]);
    const [farms, setFarms] = useState<Farm[]>([]);
    const [assignments, setAssignments] = useState<UserRole[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [version, setVersion] = useState(0);
    const [query, setQuery] = useState('');
    const [assignUserId, setAssignUserId] = useState('');

    useEffect(() => {
        let cancelled = false;
        Promise.all([
            fetchAll<User>('/users'),
            fetchAll<Role>('/roles'),
            fetchAll<Farm>('/farms'),
            fetchAll<UserRole>('/user-roles'),
        ])
            .then(([userRows, roleRows, farmRows, assignmentRows]) => {
                if (cancelled) return;
                setUsers(userRows);
                setRoles(roleRows);
                setFarms(farmRows);
                setAssignments(assignmentRows);
                setError(null);
            })
            .catch((err: unknown) => {
                if (!cancelled) setError(errorText(err, 'Could not load users.'));
            })
            .finally(() => {
                if (!cancelled) setLoading(false);
            });
        return () => {
            cancelled = true;
        };
    }, [version]);

    const reload = () => setVersion((current) => current + 1);

    const assignmentLabels = useMemo(() => {
        const roleNames = new Map(roles.map((row) => [row.id, row.name]));
        const farmNames = new Map(farms.map((row) => [row.id, row.name]));
        const labels = new Map<number, { id: number; role: string; farm: string | null }[]>();
        for (const row of assignments) {
            const list = labels.get(row.user_id) ?? [];
            list.push({
                id: row.id,
                role: roleNames.get(row.role_id) ?? `Role ${row.role_id}`,
                farm: row.farm_id === null ? null : farmNames.get(row.farm_id) ?? `Farm ${row.farm_id}`,
            });
            labels.set(row.user_id, list);
        }
        return labels;
    }, [assignments, roles, farms]);

    const q = query.trim().toLowerCase();
    const visibleUsers = users.filter(
        (row) => !q || row.full_name.toLowerCase().includes(q) || row.email.toLowerCase().includes(q),
    );

    function handleCreated(user: User) {
        setAssignUserId(String(user.id));
        reload();
    }

    return (
        <div className="mx-auto max-w-6xl">
            <div className="mb-6 flex items-center gap-4">
                <h1 className="whitespace-nowrap text-xl font-bold text-brand-dark">Users</h1>
                <div className="h-px flex-1 bg-brand-muted/40" />
            </div>

            {loading && <p className="mb-4 text-sm text-ink-muted">Loading users…</p>}
            {error && <p className="mb-4 text-sm text-red-600">{error}</p>}

            <div className="grid items-start gap-6 lg:grid-cols-2">
                <CreateUserForm onCreated={handleCreated} />
                <AssignRoleForm
                    users={users}
                    roles={roles}
                    farms={farms}
                    assignments={assignments}
                    userId={assignUserId}
                    onUserChange={setAssignUserId}
                    onAssigned={reload}
                />
            </div>

            <div className="mt-6">
                <Card title={`All users (${users.length})`}>
                    <input
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        placeholder="Search by name or email"
                        aria-label="Search users"
                        className={`${inputClass} mb-4`}
                    />
                    <table className="w-full text-left text-sm">
                        <thead className="text-xs uppercase text-ink-muted">
                            <tr>
                                <th className="px-3 py-2 font-medium">User</th>
                                <th className="px-3 py-2 font-medium">Roles and farms</th>
                                <th className="px-3 py-2 font-medium">Status</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-brand-muted/30">
                            {visibleUsers.map((row) => {
                                const labels = assignmentLabels.get(row.id) ?? [];
                                return (
                                    <tr key={row.id}>
                                        <td className="px-3 py-2">
                                            <p className="font-medium text-brand-dark">{row.full_name}</p>
                                            <p className="text-xs text-ink-muted">{row.email}</p>
                                        </td>
                                        <td className="px-3 py-2">
                                            {labels.length === 0 ? (
                                                <span className="text-xs text-ink-muted">No roles</span>
                                            ) : (
                                                <div className="flex flex-wrap gap-1.5">
                                                    {labels.map((label) => (
                                                        <span
                                                            key={label.id}
                                                            className={`rounded-full px-3 py-1 text-xs font-medium ${label.role === ADMIN_ROLE ? 'bg-brand-dark text-white' : 'bg-brand-muted/20 text-brand-dark'}`}
                                                        >
                                                            {label.farm ? `${label.role} · ${label.farm}` : label.role}
                                                        </span>
                                                    ))}
                                                </div>
                                            )}
                                        </td>
                                        <td className="px-3 py-2 text-xs text-ink-muted">
                                            {row.is_active ? 'Active' : 'Inactive'}
                                        </td>
                                    </tr>
                                );
                            })}
                            {!loading && visibleUsers.length === 0 && (
                                <tr>
                                    <td colSpan={3} className="px-3 py-3 text-sm text-ink-muted">No users match.</td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </Card>
            </div>
        </div>
    );
}
