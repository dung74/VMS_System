import React, { useEffect, useState } from 'react';
import axios from 'axios';

export default function Users() {
    const [users, setUsers] = useState([]);
    const [newUsername, setNewUsername] = useState('');
    const [newPassword, setNewPassword] = useState('');
    const [newRole, setNewRole] = useState('user');
    const [newEmail, setNewEmail] = useState('');

    const fetchUsers = async () => {
        try {
            const response = await axios.get('/api/cloud/users/');
            setUsers(response.data);
        } catch (error) {
            alert('Error fetching users: ' + (error.response?.data?.detail || error.message));
        }
    };

    useEffect(() => {
        fetchUsers();
    }, []);

    const handleCreateUser = async (e) => {
        e.preventDefault();
        try {
            await axios.post('/api/cloud/users/', {
                username: newUsername,
                password: newPassword,
                role: newRole,
                email: newEmail
            });
            alert('✅ User created successfully');
            fetchUsers();
            setNewUsername('');
            setNewPassword('');
            setNewRole('user');
            setNewEmail('');
        } catch (error) {
            alert('❌ Error creating user: ' + (error.response?.data?.detail || error.message));
        }
    };

    const handleDelete = async (id) => {
        if(!window.confirm("⚠️ Bạn có chắc chắn muốn xóa người dùng này?")) return;
        try {
          await axios.delete(`/api/cloud/users/${id}`);
          fetchUsers();
        } catch (err) {
          alert(`❌ ${err.response?.data?.detail || "Lỗi xóa"}`);
        }
    };

    return (
    <div className="max-w-7xl mx-auto p-6 space-y-6">
      
      {/* 1. KHỐI FORM THÊM NGƯỜI DÙNG */}
      <div className="bg-gray-900 p-5 rounded-2xl border border-gray-800 shadow-lg">
        <div className="flex items-center space-x-2 mb-4 border-b border-gray-800 pb-2">
          <span className="text-lg">👥</span>
          <h2 className="text-base font-semibold text-blue-400">Thêm người dùng mới</h2>
        </div>
        
        {/* Đã đổi thành md:grid-cols-2 lg:grid-cols-5 để responsive tốt hơn với 5 ô */}
        <form onSubmit={handleCreateUser} className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4 text-sm">
          <div>
            <input 
              required 
              placeholder="Username" 
              value={newUsername} 
              onChange={e => setNewUsername(e.target.value)} 
              className="w-full bg-gray-950 border border-gray-800 rounded-lg p-2.5 text-gray-200 outline-none focus:border-blue-500 transition-all"
            />
          </div>
          
          {/* Ô nhập Email mới được thêm vào */}
          <div>
            <input 
              required 
              type="email"
              placeholder="Email (VD: admin@vms.com)" 
              value={newEmail} 
              onChange={e => setNewEmail(e.target.value)} 
              className="w-full bg-gray-950 border border-gray-800 rounded-lg p-2.5 text-gray-200 outline-none focus:border-blue-500 transition-all"
            />
          </div>

          <div>
            <input 
              required 
              placeholder="Mật khẩu" 
              type="password" 
              value={newPassword} 
              onChange={e => setNewPassword(e.target.value)} 
              className="w-full bg-gray-950 border border-gray-800 rounded-lg p-2.5 text-gray-200 outline-none focus:border-blue-500 transition-all"
            />
          </div>
          <div>
            <select 
              value={newRole} 
              onChange={e => setNewRole(e.target.value)} 
              className="w-full bg-gray-950 border border-gray-800 rounded-lg p-2.5 text-gray-300 outline-none focus:border-blue-500 transition-all"
            >
              <option value="user">User (Chỉ xem)</option>
              <option value="admin">Admin (Toàn quyền)</option>
            </select>
          </div>
          <button 
            type="submit" 
            className="w-full bg-blue-600 hover:bg-blue-500 text-white font-semibold py-2.5 rounded-lg transition-all shadow-lg shadow-blue-900/30"
          >
            Tạo tài khoản
          </button>
        </form>
      </div>

      {/* 2. KHỐI BẢNG DANH SÁCH NGƯỜI DÙNG */}
      <div className="bg-gray-900 p-5 rounded-2xl border border-gray-800 shadow-lg">
        <div className="flex items-center space-x-2 mb-4 border-b border-gray-800 pb-2">
          <span className="text-lg">📋</span>
          <h2 className="text-base font-semibold text-purple-400">Danh sách tài khoản hệ thống</h2>
        </div>
        
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-gray-400">
            <thead className="text-xs text-gray-400 uppercase bg-gray-950">
              <tr>
                <th className="px-4 py-3 rounded-l-lg">ID</th>
                <th className="px-4 py-3">Tên đăng nhập</th>
                <th className="px-4 py-3">Email</th> {/* Thêm cột Email */}
                <th className="px-4 py-3 text-center">Vai trò (Role)</th>
                <th className="px-4 py-3 text-center rounded-r-lg">Thao tác</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800">
              {users.map(u => (
                <tr key={u.id} className="hover:bg-gray-850/50 transition-colors">
                  <td className="px-4 py-4 font-mono text-gray-500">{u.id}</td>
                  <td className="px-4 py-4 text-gray-200 font-medium">{u.username}</td>
                  {/* Hiển thị Email từ API */}
                  <td className="px-4 py-4 text-gray-400">{u.email || '—'}</td>
                  <td className="px-4 py-4 text-center">
                    <span className={`px-2.5 py-1 rounded-md text-xs font-bold ${
                      u.role === 'admin' 
                        ? 'bg-purple-900/40 text-purple-400 border border-purple-800/50' 
                        : 'bg-gray-800 text-gray-300 border border-gray-700'
                    }`}>
                      {u.role ? u.role.toUpperCase() : 'USER'}
                    </span>
                  </td>
                  <td className="px-4 py-4 text-center">
                    {u.username !== 'admin1' ? (
                      <button 
                        onClick={() => handleDelete(u.id)} 
                        className="text-red-500 hover:text-red-400 p-1.5 text-xs font-semibold transition-colors"
                      >
                        Xóa
                      </button>
                    ) : (
                      <span className="text-xs text-gray-600 italic">Bảo vệ</span>
                    )}
                  </td>
                </tr>
              ))}
              {users.length === 0 && (
                <tr>
                  <td colSpan="5" className="text-center py-6 text-gray-600 italic">
                    Chưa có dữ liệu người dùng.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

    </div>
  );
}