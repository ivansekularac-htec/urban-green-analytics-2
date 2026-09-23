import { BrowserRouter, Routes, Route, Outlet } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { RequireAuth } from './components/RequireAuth';
import { Navbar } from './components/Navbar';
import { Login } from './pages/Login';
import { Profile } from './pages/Profile';

function AppLayout() {
  return (
    <div className="flex min-h-screen">
      <Navbar />
      <main className="flex-1 p-6">
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
            <Route path="/" element={<div>Home</div>} />
            <Route path="/dashboards" element={<div>Dashboards</div>} />
            <Route path="/profile" element={<Profile />} />
            <Route path="/users" element={<div>Users</div>} />
            <Route path="/monitoring" element={<div>Monitoring</div>} />
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
