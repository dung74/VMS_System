import { useEffect, useState } from "react";
import modelApi from "../api/modelApi";

export default function Models() {
    const [models, setModels] = useState([]);
    const [formData, setFormData] = useState({ id: '', name: '', type: '', task_type: 'detection', file_path: '' });
    const [isEditing, setIsEditing] = useState(false);

    const isAdmin = localStorage.getItem('role') === 'admin';

    const loadModels = async () => {
        try {
            const response = await modelApi.getList();
            setModels(response.data?.models || []);

        } catch (error) {
            console.error('Error fetching models:', error);
        }
    };
    useEffect(() => { loadModels(); }, []);

    const handleEdit = (model) => {
        setFormData( { id: model.id, name: model.name, type: model.type, task_type: 'detection', file_path: model.file_path});
        setIsEditing(true);
        
    };

    const handleReset = () => {
        setFormData({ id: '', name: '', type: '', task: 'detection', file_path: '' });
        setIsEditing(false);
    };

    const handleSave = async (e) => {
        e.preventDefault();
        try {
            const payload = {
                name: formData.name,
                type: formData.type,
                task_type: formData.task_type,
                file_path: formData.file_path
            };
            if (isEditing) {
                await modelApi.edit(formData.id, payload);
                alert('Model updated successfully');
                

            } else {
                await modelApi.add(payload);
                alert('Model added successfully');
            }
            handleReset();
            loadModels();
        } catch (error){
            console.error(error);
        }
    };

    const handleRemove = async (id) => {
        if (!isAdmin || !window.confirm('Are you sure you want to remove this model?')) return;
        try {
            await modelApi.remove(id);
            loadModels();
        } catch (error) {
            console.error('Error removing model:', error);
        }
    };

    return (
        <div className={`grid grid-cols-1 ${isAdmin ? 'xl:grid-cols-3' : 'max-w-4xl mx-auto'} gap-6`}>
            {isAdmin && (
                <div className="space-y-6 xl:col-span-1">
                    <div className="bg-gray-900 p-5 rounded-2xl border border-gray-800 shadow-lg">
                        <div className="flex items-center space-x-2 mb-4 border-b border-gray-800 pb-2">
                            <span className="text-lg">📦</span>
                            <h2 className="text-base font-semibold text-purple-400">
                                {isEditing ? `Cập nhật Model #${formData.id}` : "Thêm Model mới"}
                            </h2>
                        </div>
                        <form onSubmit={handleSave} className="space-y-3 text-sm">
                            <div>
                                <label className="block text-xs text-gray-500 mb-1">Tên mô hình</label>
                                <input type="text" value={formData.name} onChange={e => setFormData({...formData, name: e.target.value})} className="w-full bg-gray-950 border border-gray-800 rounded-lg p-2.5 outline-none focus:border-purple-500" required />
                            </div>
                            <div className="grid grid-cols-2 gap-3">
                                <div>
                                    <label className="block text-xs text-gray-500 mb-1">Type</label>
                                    <input type="text" value={formData.type} onChange={e => setFormData({...formData, type: e.target.value})} className="w-full bg-gray-950 border border-gray-800 rounded-lg p-2.5 outline-none focus:border-purple-500" required />
                                </div>
                                <div>
                                    <label className="block text-xs text-gray-500 mb-1">Tác vụ</label>
                                    <input type="text" value={formData.task_type} onChange={e => setFormData({...formData, task_type: e.target.value})} className="w-full bg-gray-950 border border-gray-800 rounded-lg p-2.5 outline-none focus:border-purple-500" />
                                </div>
                            </div>
                            <div>
                                <label className="block text-xs text-gray-500 mb-1">Đường dẫn tệp (.pt)</label>
                                <input type="text" value={formData.file_path} onChange={e => setFormData({...formData, file_path: e.target.value})} className="w-full bg-gray-950 border border-gray-800 rounded-lg p-2.5 outline-none focus:border-purple-500" required />
                            </div>
                            <div className="flex space-x-2">
                                <button type="submit" className="flex-1 bg-purple-600 hover:bg-purple-500 text-white font-semibold py-2.5 rounded-lg shadow-lg">
                                    {isEditing ? "Lưu thay đổi" : "Thêm Model"}
                                </button>
                                {isEditing && (
                                    <button type="button" onClick={handleReset} className="px-4 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-lg">Hủy</button>
                                )}
                            </div>
                        </form>
                    </div>
                </div>
            )}

            <div className={`${isAdmin ? 'xl:col-span-2' : 'xl:col-span-1'} space-y-6`}>
                <div className="bg-gray-900 p-5 rounded-2xl border border-gray-800 shadow-lg">
                    <div className="flex justify-between items-center mb-4 border-b border-gray-800 pb-2">
                        <div className="flex items-center space-x-2">
                            <span className="text-lg">⚙️</span><h2 className="text-base font-semibold text-purple-400">Danh sách AI Models</h2>
                        </div>
                        <button onClick={loadModels} className="text-xs bg-gray-800 hover:bg-gray-700 px-3 py-1.5 rounded-lg border border-gray-700">🔄 Làm mới</button>
                    </div>
                    <div className="overflow-x-auto">
                        <table className="w-full text-left text-sm text-gray-400">
                            <thead className="text-xs uppercase bg-gray-950">
                                <tr>
                                    <th className="px-4 py-3">ID</th>
                                    <th className="px-4 py-3">Tên & Loại</th>
                                    <th className="px-4 py-3">Đường dẫn</th>
                                    {isAdmin && <th className="px-4 py-3 text-center">Tác vụ</th>}
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-800">
                                {models.map(m => (
                                    <tr key={m.id} className="hover:bg-gray-850/50">
                                        <td className="px-4 py-3 font-mono font-bold">{m.id}</td>
                                        <td className="px-4 py-3 text-gray-200 font-semibold">
                                            {m.name} <br/><span className="text-xs text-gray-500 font-normal">{m.type} | {m.task_type}</span>
                                        </td>
                                        <td className="px-4 py-3 text-xs font-mono text-gray-400">{m.file_path}</td>
                                        {isAdmin && (
                                            <td className="px-4 py-3 text-center">
                                                <button onClick={() => handleEdit(m)} className="text-blue-400 hover:text-blue-300 px-2 text-xs">Sửa</button>
                                                <button onClick={() => handleRemove(m.id)} className="text-red-500 hover:text-red-400 px-2 text-xs">Xóa</button>
                                            </td>
                                        )}
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    );

}