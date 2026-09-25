import { BrowserRouter, Routes, Route, Outlet } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { RequireAuth } from './components/RequireAuth';
import { RequireRole } from './components/RequireRole';
import { Navbar } from './components/Navbar';
import { Login } from './pages/Login';
import { Profile } from './pages/Profile';
import { Home } from './pages/Home';
import { FarmDetail } from './pages/FarmDetail';
import { Users } from './pages/Users';
import { ADMIN_ROLE } from './types/user';

function AppLayout() {
  return (
    <div className="flex h-screen overflow-hidden">
      <Navbar />
      <main className="flex-1 overflow-y-auto p-6">
        <Outlet />
      </main>
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route element={<RequireAuth><AppLayout /></RequireAuth>}>
            <Route path="/" element={<Home />} />
            <Route path="/farms/:farmId" element={<FarmDetail />} />
            <Route path="/profile" element={<Profile />} />
            <Route path="/users" element={<RequireRole role={ADMIN_ROLE}><Users /></RequireRole>} />
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
