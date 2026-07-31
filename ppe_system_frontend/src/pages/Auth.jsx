import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import authApi from '../api/authApi';

export default function Auth() {
    const [errorMsg, setErrorMsg] = useState('');
    const navigate = useNavigate();

    const [loginData, setLoginData] = useState({username: '', password: ''});

    const handleLogin = async (e) => {
        e.preventDefault();
        setErrorMsg(''); // Xóa thông báo lỗi cũ nếu có khi thử đăng nhập lại
        
        try {
            const data = await authApi.login({...loginData, email: "", role: "admin"});
            localStorage.setItem('access_token', data.data.access_token);
            localStorage.setItem('role', data.data.role);
            navigate('/');
        } catch (error) {
            // Lấy thông báo lỗi từ server hoặc hiển thị lỗi mặc định
            const detail = error.response?.data?.detail;
            setErrorMsg(detail || "Error connecting to the server. Please try again later.");
        }
    };

    return(
        <div className="bg-gray-950 flex items-center justify-center min-h-screen">
            <div className="bg-gray-900 p-8 rounded-2xl border border-gray-800 shadow-2xl w-full max-w-md">
                <div className="text-center mb-6">
                    <span className="text-5xl">🛡️</span>
                    <h2 className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent mt-3">AI VMS CLOUD</h2>
                </div>

                {/* Hiển thị thông báo lỗi */}
                {errorMsg && <div className="mb-4 text-red-500 text-center text-sm font-medium p-2 bg-red-500/10 border border-red-500/20 rounded">{errorMsg}</div>}

                <form onSubmit={handleLogin} className="space-y-4 text-sm">
                    <div>
                        <label className="block text-gray-400 mb-1">Tài khoản</label>
                        <input 
                            type="text" 
                            required 
                            value={loginData.username} 
                            onChange={e => setLoginData({...loginData, username: e.target.value})} 
                            className="w-full bg-gray-950 border border-gray-800 rounded-lg p-3 text-white outline-none focus:border-blue-500 transition-colors" 
                            placeholder="Nhập tài khoản" 
                        />
                    </div>
                    <div>
                        <label className="block text-gray-400 mb-1">Mật khẩu</label>
                        <input 
                            type="password" 
                            required 
                            value={loginData.password} 
                            onChange={e => setLoginData({...loginData, password: e.target.value})} 
                            className="w-full bg-gray-950 border border-gray-800 rounded-lg p-3 text-white outline-none focus:border-blue-500 transition-colors" 
                            placeholder="Nhập mật khẩu" 
                        />
                    </div>
                    <button type="submit" className="w-full bg-blue-600 hover:bg-blue-500 text-white font-bold py-3 rounded-lg mt-2 shadow-lg transition-colors">
                        Đăng nhập
                    </button>
                </form>
            </div>
        </div>
    );
}