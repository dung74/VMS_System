import { useState, useEffect } from "react";
import VideoStream from "../components/VideoStream";
import cameraApi from "../api/cameraApi";
import modelApi from "../api/modelApi";

export default function Cameras() {
    const [cameras, setCameras] = useState([]);
    const [models, setModels] = useState([]);
    const [liveViews, setLiveViews] = useState([]);
    const isAdmin = localStorage.getItem('role') === 'admin';


    const [editingId, setEditingId] = useState(null);
    const [formData, setFormData] = useState({
        name: "",
        source: "",
        location: "",
        current_model: "",

    })

    const loadModels = async () => {
        if (!isAdmin) return;

        try {
            const response = await modelApi.getList();
            setModels(response.data?.models || []);
        } catch (error) {
            console.error('Error fetching models:', error);
        }
    }

    const loadCameras = async () => {
        try {
            const response = await cameraApi.getList();
            setCameras(response.data?.cameras || []);

        } catch (error) {
            console.error('Error fetching cameras:', error);
        }
    }
    
    useEffect(() => { loadCameras();  loadModels()}, []);

    const toggleLiveView = (id) => {
        setLiveViews(prev => prev.includes(id) ? prev.filter(vid => vid !== id) : [...prev, id]);
    };

    const handleStartAI = async (cameraId) => {
        try {
            await cameraApi.startCamera(cameraId, { edge_id: "edge_node_1" });
            // setLiveViews(prev => [...prev, cameraId]);
            alert('Camera started successfully. You can now view the live stream.');
        } catch (error) {
            console.error('Error starting AI:', error);
        }
    };

    const handleStopAI = async (cameraId) => {
        try {
            await cameraApi.stopCamera(cameraId, { edge_id: "edge_node_1" });            
            setLiveViews(prev => prev.filter(vid => vid !== cameraId));
        } catch (error) {
            console.error('Error stopping AI:', error);
        }
    };

    const handleDeleteCamera = async (cameraId) => {
        if (!isAdmin || !window.confirm('Are you sure you want to remove this camera?')) return;
        try {
            await cameraApi.remove(cameraId, {edge_id: "edge_node_1"});
            loadCameras();
        } catch (error) {
            console.error('Error deleting camera:', error);
        }
    };


    const handleInputChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({...prev, [name]: value }));
    };

    const handleModelSelect = (e) => {
        const selectedOption = Array.from(e.target.selectedOptions).map(option => parseInt(option.value));
        setFormData(prev => ({...prev, current_model: selectedOption }));
    };

    const handleEditClick = (camera) => {
        setEditingId(camera.id);
        setFormData({
            name: camera.name,
            source: camera.source,
            location: camera.location || "",
            current_model: camera.current_model || []
        });
    }

    const resetForm = () => {
        setEditingId(null);
        setFormData({
            name: "",
            source: "",
            location: "",
            current_model: []
        });
    }

    const handleSubmitForm = async (e) => {
        e.preventDefault();
        try {
            if (editingId) {
                await cameraApi.edit(editingId, formData);
                alert('Camera updated successfully');
            } else {
                await cameraApi.add(formData);
                alert('Camera added successfully');
            }
            resetForm();
            loadCameras();

        } catch (error) {
            console.error('Error saving camera:', error);
        }
    }

    return (
        <div className={`grid grid-cols-1 ${isAdmin ? 'xl:grid-cols-3' : 'xl:grid-cols-2'} gap-6`}>
            
            {/* Cột trái: Form Thêm/Sửa Camera (Chỉ Admin) */}
            {isAdmin && (
                <div className="space-y-6 xl:col-span-1">
                    <div className="bg-gray-900 p-5 rounded-2xl border border-gray-800 shadow-lg">
                        <div className="flex items-center space-x-2 mb-4 border-b border-gray-800 pb-2">
                            <span className="text-lg">📹</span>
                            <h2 className="text-base font-semibold text-blue-400">
                                {editingId ? `Cập nhật Camera #${editingId}` : 'Thêm Camera mới'}
                            </h2>
                        </div>
                        <form onSubmit={handleSubmitForm} className="space-y-3 text-sm">
                            <div>
                                <label className="block text-xs text-gray-500 mb-1">Tên camera</label>
                                <input name="name" value={formData.name} onChange={handleInputChange} type="text" className="w-full bg-gray-950 border border-gray-800 rounded-lg p-2.5 outline-none focus:border-blue-500 text-white" required />
                            </div>
                            <div>
                                <label className="block text-xs text-gray-500 mb-1">Nguồn luồng (Source/RTSP)</label>
                                <input name="source" value={formData.source} onChange={handleInputChange} type="text" className="w-full bg-gray-950 border border-gray-800 rounded-lg p-2.5 outline-none focus:border-blue-500 text-white" required />
                            </div>
                            <div>
                                <label className="block text-xs text-gray-500 mb-1">Khu vực lắp đặt</label>
                                <input name="location" value={formData.location} onChange={handleInputChange} type="text" className="w-full bg-gray-950 border border-gray-800 rounded-lg p-2.5 outline-none focus:border-blue-500 text-white" />
                            </div>
                            <div>
                                <label className="flex justify-between text-xs text-gray-500 mb-1">
                                    <span>Chỉ định Mô hình AI</span>
                                    <span className="text-gray-600">Giữ Ctrl để chọn nhiều</span>
                                </label>
                                <select 
                                    multiple 
                                    value={formData.current_model_id} 
                                    onChange={handleModelSelect}
                                    className="w-full h-24 bg-gray-950 border border-gray-800 rounded-lg p-2 outline-none focus:border-blue-500 text-white"
                                >
                                    {models.map(m => (
                                        <option key={m.id} value={m.id}>{m.name} ({m.type})</option>
                                    ))}
                                </select>
                            </div>
                            <div className="flex space-x-2 pt-2">
                                <button type="submit" className="flex-1 bg-blue-600 hover:bg-blue-500 text-white font-semibold py-2.5 rounded-lg shadow-lg transition-colors">
                                    {editingId ? 'Lưu thay đổi' : 'Thêm Camera'}
                                </button>
                                {editingId && (
                                    <button type="button" onClick={resetForm} className="px-4 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-lg transition-colors">
                                        Hủy
                                    </button>
                                )}
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {/* Cột phải: Bảng Danh sách & Live Video Wall */}
            <div className={`${isAdmin ? 'xl:col-span-2' : 'xl:col-span-3'} space-y-6`}>
                <div className="bg-gray-900 p-5 rounded-2xl border border-gray-800 shadow-lg">
                    <div className="flex justify-between items-center mb-4 border-b border-gray-800 pb-2">
                        <div className="flex items-center space-x-2">
                            <span className="text-lg">📋</span><h2 className="text-base font-semibold text-yellow-500">Danh sách Camera</h2>
                        </div>
                        <button onClick={loadCameras} className="text-xs bg-gray-800 hover:bg-gray-700 px-3 py-1.5 rounded-lg transition-colors text-white">🔄 Làm mới</button>
                    </div>
                    <div className="overflow-x-auto">
                        <table className="w-full text-left text-sm text-gray-400">
                            <thead className="text-xs uppercase bg-gray-950">
                                <tr>
                                    <th className="px-4 py-3">Mã</th>
                                    <th className="px-4 py-3">Thông tin</th>
                                    <th className="px-4 py-3 text-center">Tác vụ</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-800">
                                {cameras.map(c => {
                                    const isViewing = liveViews.includes(c.id);
                                    const rowClass = isViewing ? "bg-indigo-900/10 border-l-2 border-indigo-500" : "hover:bg-gray-850/50 border-l-2 border-transparent";
                                    
                                    return (
                                        <tr key={c.id} className={`transition-colors ${rowClass}`}>
                                            <td className="px-4 py-3 font-mono font-bold">{c.id}</td>
                                            <td className="px-4 py-3 text-xs">
                                                <div className="flex items-center">
                                                    <span className="text-sm font-semibold text-gray-200">{c.name}</span>
                                                    {isViewing && (
                                                        <span className="ml-2 inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-bold bg-red-500/20 text-red-500 border border-red-500/30 animate-pulse">LIVE</span>
                                                    )}
                                                </div>
                                                <div className="mt-1 text-gray-500">Nguồn: <span className="text-gray-400">{c.source}</span> | Khu: <span className="text-gray-400">{c.location}</span></div>
                                                <div className="mt-0.5">Models: <span className="text-purple-400">{JSON.stringify(c.current_model_id || [])}</span></div>
                                            </td>
                                            <td className="px-4 py-3">
                                                <div className="flex flex-wrap items-center justify-start xl:justify-center gap-1.5">
                                                    <button onClick={() => handleStartAI(c.id)} className="bg-emerald-600 hover:bg-emerald-500 px-2 py-1.5 rounded text-xs text-white transition-colors shadow min-w-[60px]">Bật AI</button>
                                                    
                                                    {isViewing ? (
                                                        <button disabled className="bg-gray-800 border border-gray-700 px-2 py-1.5 rounded text-xs text-gray-400 cursor-not-allowed shadow inline-flex items-center justify-center gap-1.5 min-w-[70px]">
                                                            <span className="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse"></span> Đang Xem
                                                        </button>
                                                    ) : (
                                                        <button onClick={() => toggleLiveView(c.id)} className="bg-indigo-600 hover:bg-indigo-500 px-2 py-1.5 rounded text-xs text-white transition-colors shadow min-w-[70px]">Xem</button>
                                                    )}
                                                    
                                                    <button onClick={() => handleStopAI(c.id)} className="bg-gray-700 hover:bg-gray-600 px-2 py-1.5 rounded text-xs text-white transition-colors shadow min-w-[60px]">Tắt</button>
                                                    
                                                    {isAdmin && (
                                                        <>
                                                            <button onClick={() => handleEditClick(c)} className="text-blue-400 hover:text-blue-300 px-2 py-1.5 font-medium text-xs">Sửa</button>
                                                            <button onClick={() => handleDeleteCamera(c.id)} className="text-red-500 hover:text-red-400 px-2 py-1.5 font-medium text-xs">Xóa</button>
                                                        </>
                                                    )}
                                                </div>
                                            </td>
                                        </tr>
                                    );
                                })}
                            </tbody>
                        </table>
                    </div>
                </div>

                <div className="bg-gray-900 p-5 rounded-2xl border border-gray-800 shadow-lg">
                    <div className="flex items-center space-x-2 mb-4 border-b border-gray-800 pb-2">
                        <span className="text-lg">📺</span><h2 className="text-base font-semibold text-green-400">Live Video Wall</h2>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {liveViews.length === 0 ? (
                            <div className="text-gray-600 italic col-span-full py-8 text-center text-sm">Chưa có luồng WebRTC nào.</div>
                        ) : (
                            liveViews.map(id => <VideoStream key={id} cameraId={id} onClose={() => toggleLiveView(id)} />)
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}