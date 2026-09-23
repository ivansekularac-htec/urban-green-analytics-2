import { NavLink, useNavigate } from 'react-router-dom';
import { LogOut } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import logo from '../assets/logo.png';

const linkBase = 'flex items-center rounded-md px-4 py-2.5 text-sm font-medium transition-colors';
const linkInactive = 'text-white/80 hover:bg-white/10 hover:text-white';
const linkActive = 'bg-brand text-white';

export function Navbar() {
    const { user, logout } = useAuth();
    const navigate = useNavigate();
    const isAdmin = user?.roles.includes('Admin') ?? false;

    const linkClass = ({ isActive }: { isActive: boolean }) =>
        `${linkBase} ${isActive ? linkActive : linkInactive}`;

    function handleLogout() {
        logout();
        navigate('/login');
    }

    return (
        <nav className="flex w-64 shrink-0 flex-col bg-brand-dark px-4 py-6">
            <img src={logo} alt="Urban Green Analytics" className="mx-auto w-36" />

            <div className="mt-10 flex flex-1 flex-col gap-1">
                <NavLink to="/" end className={linkClass}>Home</NavLink>
                <NavLink to="/dashboards" className={linkClass}>Dashboards</NavLink>
                {isAdmin && (
                    <>
                        <NavLink to="/users" className={linkClass}>Users</NavLink>
                        <NavLink to="/monitoring" className={linkClass}>Monitoring</NavLink>
                    </>
                )}
            </div>

            <div className="border-t border-white/10 pt-4">
                <NavLink to="/profile" className={linkClass}>
                    <span className="truncate">{user?.full_name ?? user?.email}</span>
                </NavLink>
                <button
                    onClick={handleLogout}
                    className="mt-1 flex w-full items-center gap-2 rounded-md px-4 py-2.5 text-sm font-medium text-white/80 transition-colors hover:bg-white/10 hover:text-white"
                >
                    <LogOut size={16} />
                    Log out
                </button>
            </div>
        </nav>
    );
}
