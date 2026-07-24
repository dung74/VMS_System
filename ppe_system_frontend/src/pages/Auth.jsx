import { useState } from 'react';
import {useNavigate, NavLink, Outlet} from 'react-router-dom';
import authApi from '../api/authApi';

export default function Auth() {
    const [activeTab, setActiveTab] = useState('login');
    const [errorMsg, setErrorMsg] = useState('');
    const [successMsg, setSuccessMsg] = useState('');
    const navigate = useNavigate();

    const [loginData, setLoginData] = useState({username: '', password: ''});
    const [registerData, setRegisterData] = useState({username: '', email: '', password: '', role: 'user'});

    const handleLogin = async (e) => {
        e.preventDefault();
        try {
            const data = await authApi.login({...loginData, email: "", role: "admin"});
            localStorage.setItem('access_token', data.data.access_token);
            localStorage.setItem('role', data.data.role);
            navigate('/');

        } catch (error) {
            const detail = error.response?.data?.detail;
            setErrorMsg("Error connecting to the server. Please try again later.");
        }
    };

    const handleRegister = async (e) => {
        e.preventDefault();
        setErrorMsg('');
        setSuccessMsg('');
        try {
            await authApi.register(registerData);
            setSuccessMsg('Registration successful! you can now log in.');
            setActiveTab('login');
            setRegisterData({username: '', email: '', password: '', role: 'user'});
        } catch (error) {
            const detail = error.response?.data?.detail;
            setErrorMsg("Error connecting to the server. Please try again later.");
        }
    }

    return(
        <div className="bg-gray-950 flex items-center justify-center min-h-screen">
            <div className="bg-gray-900 p-8 rounded-2xl border border-gray-800 shadow-2xl w-full max-w-md">
                <div className="text-center mb-6">
                    <span className="text-5xl">🛡️</span>
                    <h2 className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent mt-3">AI VMS CLOUD</h2>
                </div>

                <div className="flex border-b border-gray-800 mb-6 text-sm">
                    <button onClick={() => {setActiveTab('login'); setErrorMsg(''); setSuccessMsg('');}} className={`flex-1 pb-2 border-b-2 font-semibold transition-colors ${activeTab === 'login' ? 'border-blue-500 text-blue-500' : 'border-transparent text-gray-500'}`}>Đăng nhập</button>
                    <button onClick={() => {setActiveTab('register'); setErrorMsg(''); setSuccessMsg('');}} className={`flex-1 pb-2 border-b-2 font-semibold transition-colors ${activeTab === 'register' ? 'border-purple-500 text-purple-500' : 'border-transparent text-gray-500'}`}>Đăng ký</button>
                </div>

                {/* Hiển thị thông báo */}
                {successMsg && <div className="mb-4 text-green-500 text-center text-sm font-medium p-2 bg-green-500/10 border border-green-500/20 rounded">{successMsg}</div>}
                {errorMsg && <div className="mb-4 text-red-500 text-center text-sm font-medium p-2 bg-red-500/10 border border-red-500/20 rounded">{errorMsg}</div>}

                {activeTab === 'login' ? (
                    <form onSubmit={handleLogin} className="space-y-4 text-sm">
                        <div>
                            <label className="block text-gray-400 mb-1">Tài khoản</label>
                            <input type="text" required value={loginData.username} onChange={e => setLoginData({...loginData, username: e.target.value})} className="w-full bg-gray-950 border border-gray-800 rounded-lg p-3 text-white outline-none focus:border-blue-500 transition-colors" placeholder="Nhập tài khoản" />
                        </div>
                        <div>
                            <label className="block text-gray-400 mb-1">Mật khẩu</label>
                            <input type="password" required value={loginData.password} onChange={e => setLoginData({...loginData, password: e.target.value})} className="w-full bg-gray-950 border border-gray-800 rounded-lg p-3 text-white outline-none focus:border-blue-500 transition-colors" placeholder="Nhập mật khẩu" />
                        </div>
                        <button type="submit" className="w-full bg-blue-600 hover:bg-blue-500 text-white font-bold py-3 rounded-lg mt-2 shadow-lg transition-colors">Đăng nhập</button>
                    </form>
                ) : (
                    <form onSubmit={handleRegister} className="space-y-4 text-sm">
                        <div>
                            <label className="block text-gray-400 mb-1">Tài khoản mới</label>
                            <input type="text" required value={registerData.username} onChange={e => setRegisterData({...registerData, username: e.target.value})} className="w-full bg-gray-950 border border-gray-800 rounded-lg p-3 text-white outline-none focus:border-purple-500 transition-colors" placeholder="Nhập tên tài khoản" />
                        </div>
                        <div>
                            <label className="block text-gray-400 mb-1">Email</label>
                            <input type="email" required value={registerData.email} onChange={e => setRegisterData({...registerData, email: e.target.value})} className="w-full bg-gray-950 border border-gray-800 rounded-lg p-3 text-white outline-none focus:border-purple-500 transition-colors" placeholder="Nhập email" />
                        </div>
                        <div>
                            <label className="block text-gray-400 mb-1">Mật khẩu</label>
                            <input type="password" required minLength={6} value={registerData.password} onChange={e => setRegisterData({...registerData, password: e.target.value})} className="w-full bg-gray-950 border border-gray-800 rounded-lg p-3 text-white outline-none focus:border-purple-500 transition-colors" placeholder="Mật khẩu ít nhất 6 ký tự" />
                        </div>
                        <div>
                            <label className="block text-gray-400 mb-1">Vai trò</label>
                            <select value={registerData.role} onChange={e => setRegisterData({...registerData, role: e.target.value})} className="w-full bg-gray-950 border border-gray-800 rounded-lg p-3 text-white outline-none focus:border-purple-500 transition-colors">
                                <option value="user">Người dùng (User)</option>
                                {/* <option value="admin">Quản trị viên (Admin)</option> */}
                            </select>
                        </div>
                        <button type="submit" className="w-full bg-purple-600 hover:bg-purple-500 text-white font-bold py-3 rounded-lg mt-2 shadow-lg transition-colors">Tạo tài khoản</button>
                    </form>
                )}
            </div>
        </div>
    );

}