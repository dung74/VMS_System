import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { useState, useEffect } from 'react';
import authApi from '../api/authApi';


export default function Layout() {
    const navigate = useNavigate();
    
    const [user, setUser] = useState({username: 'Loadding....', role: '', email:''});

    useEffect(() => {
        const loadUserInfo = async () => {
            const token = localStorage.getItem('access_token');
            const role = localStorage.getItem('role');

            if (!token) {
                navigate('login');
                return;
            }

            try {
                const response = await authApi.getCurrentUser();
                setUser(response.data);
            } catch (error) {
                console.error(error);
            }
        }

        loadUserInfo();
    }, [navigate]);

    const handleLogout = async () => {
        try {
            localStorage.removeItem('access_token');
            localStorage.removeItem('role');

            await fetch('/api/cloud/auth/logout', {method: 'POST'})
            navigate('/login');

        } catch (error) {
            console.error(error);
        }
    };
    return (
        <div className="bg-gray-950 text-gray-100 font-sans min-h-screen flex flex-col">
            <header className="bg-gray-900 border-b border-gray-800 shadow-xl sticky top-0 z-50">
                <div className="px-6 py-4 flex justify-between items-center">
                    <div className="flex items-center space-x-3">
                        <span className="text-3xl">🛡️</span>
                        <div>
                            <h1 className="text-xl font-bold bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
                                AI VMS CLOUD PLATFORM
                            </h1>
                            <p className="text-xs text-gray-500">Hệ thống Điều phối & Quản lý Camera Phân tán</p>
                        </div>
                    </div>
                    
                    <div className="flex items-center space-x-5">
                        <div className="flex items-center space-x-2 text-right">
                            <span className="w-2.5 h-2.5 rounded-full bg-green-500 inline-block mt-1 animate-pulse"></span>
                            <div>
                                <p className="font-medium text-gray-200 text-sm">
                                    {user.username} 
                                    <span className={`text-xs px-1.5 py-0.5 rounded uppercase ml-1 ${user.role === 'admin' ? 'bg-red-900/50 text-red-400' : 'bg-blue-900/50 text-blue-400'}`}>
                                        {user.role}
                                    </span>
                                </p>
                                <p className="text-xs text-gray-500">{user.email}</p>
                            </div>
                        </div>
                        <button onClick={handleLogout} className="text-xs bg-gray-800 border border-gray-700 hover:bg-red-600 hover:text-white hover:border-red-500 text-gray-300 px-3 py-1.5 rounded-lg transition-all">Đăng xuất</button>
                    </div>
                </div>
                
                <nav className="flex px-6 space-x-6 border-t border-gray-800 text-sm font-medium text-gray-400">
                    <NavLink to="/" className={({ isActive }) => `py-3 border-b-2 transition-all ${isActive ? 'border-blue-500 text-blue-500' : 'border-transparent hover:text-gray-200'}`}>📹 Quản lý Camera</NavLink>
                    <NavLink to="/models" className={({ isActive }) => `py-3 border-b-2 transition-all ${isActive ? 'border-blue-500 text-blue-500' : 'border-transparent hover:text-gray-200'}`}>📦 Quản lý Model</NavLink>
                    <NavLink to="/events" className={({ isActive }) => `py-3 border-b-2 transition-all ${isActive ? 'border-blue-500 text-blue-500' : 'border-transparent hover:text-gray-200'}`}>🚨 Quản lý Sự kiện</NavLink>
                </nav>
            </header>

            <main className="flex-1 max-w-7xl w-full mx-auto p-6">
                <Outlet />
            </main>
        </div>
    );
}