import { useState, useEffect } from "react";
import eventApi from "../api/eventApi";

export default function Events() {
    const [events, setEvents] = useState([]);
    const [page, setPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);

    const [imageModal, setImageModal] = useState ({ isOpen: false, src: '' });
    const [jsonModal, setJsonModal] = useState ({isOpen: false, content: '' });
    const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000';
    const loadEvents = async (page) => {
        try {
            const response = await eventApi.getList(page, 10);

            const responseData = response.data || {};
            setEvents(responseData?.events || []);
            setPage(responseData?.current_page || page);
            setTotalPages(responseData?.total_pages || 1);

        } catch (error) {
            console.error('Error fetching events:', error);
        }
    };

    useEffect(() => { loadEvents(page); }, []);

    const changePage = (step) => {
        const newPage = page + step;
        if (newPage >= 1 || newPage <= totalPages) {
            loadEvents(newPage);
        }
    };

    const handleOpenJson = (detections) => {
        const content = typeof detections === 'string' ? JSON.parse(detections) : detections;
        setJsonModal({isOpen: true, content: JSON.stringify(content, null, 2)});

    };


    useEffect(() => {
        const handleKeyDown = (event) => {
            if (event.key === 'Escape') {
                setImageModal({ isOpen: false, src: '' });
                setJsonModal({isOpen: false, content: '' });
            }
        };
        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, []);


    const getFullImageUrl = (imagePath) => {
        if (!imagePath) return '';
        if (imagePath.startsWith('http://') || imagePath.startsWith('https://')) {
            return imagePath;
        }

        const cleanPath = imagePath.startsWith('/') ? imagePath.slice(1) : imagePath;

        if (cleanPath.startsWith('media/')) {
            return `${backendUrl}/${cleanPath}`;
        }

        return `${backendUrl}/media/${cleanPath}`;
        
    }

    return (
        <div className="space-y-6">
            <div className="bg-gray-900 p-5 rounded-2xl border border-gray-800 shadow-lg relative">
                <div className="flex justify-between items-center mb-4 border-b border-gray-800 pb-2">
                    <div className="flex items-center space-x-2">
                        <span className="text-lg">🚨</span><h2 className="text-base font-semibold text-red-400">Lịch sử Sự kiện</h2>
                    </div>
                    <button onClick={() => loadEvents(1)} className="text-xs bg-gray-800 hover:bg-gray-700 px-3 py-1.5 rounded-lg border border-gray-700 transition-colors">🔄 Tải lại dữ liệu</button>
                </div>
                
                <div className="overflow-x-auto">
                    <table className="w-full text-left text-sm text-gray-400">
                        <thead className="text-xs uppercase bg-gray-950 text-gray-400">
                            <tr>
                                <th className="px-4 py-3">Mã SV / ID</th>
                                <th className="px-4 py-3">Thời gian</th>
                                <th className="px-4 py-3">Cam/Model</th>
                                <th className="px-4 py-3">Phân loại</th>
                                <th className="px-4 py-3 text-center">Hình ảnh</th>
                                <th className="px-4 py-3 text-center">Detections</th>
                                <th className="px-4 py-3 text-center">Trạng thái</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-800">
                            {events.length === 0 ? (
                                <tr><td colSpan="7" className="text-center py-6 italic text-gray-500">Chưa có sự kiện nào được ghi nhận.</td></tr>
                            ) : (
                                events.map(ev => {
                                    const fullId = ev.code_event || ev.id || "N/A";
                                    const displayId = String(fullId).length > 12 ? String(fullId).substring(0, 8) + "..." : fullId;
                                    const hasDetections = ev.detections && (Array.isArray(ev.detections) ? ev.detections.length > 0 : Object.keys(ev.detections).length > 0);
                                    
                                    // Tạo sẵn URL cho ảnh của row này
                                    const imageUrl = getFullImageUrl(ev.image_path);

                                    return (
                                        <tr key={fullId} className="hover:bg-gray-850/50 border-b border-gray-800/30">
                                            <td className="px-4 py-3 font-mono text-gray-400 text-xs" title={fullId}>#{displayId}</td>
                                            <td className="px-4 py-3 text-xs text-gray-400">{ev.created_at ? new Date(ev.created_at).toLocaleString('vi-VN') : 'Đang cập nhật'}</td>
                                            <td className="px-4 py-3 text-xs font-mono text-gray-500">
                                                CAM: <span className="text-blue-400">{ev.camera_id}</span><br/>
                                                MDL: <span className="text-purple-400">{ev.model_id !== null ? ev.model_id : 'null'}</span>
                                            </td>
                                            <td className="px-4 py-3 text-red-400 font-semibold uppercase text-xs">{ev.event_type}</td>
                                            <td className="px-4 py-3 text-center">
                                                {imageUrl ? (
                                                    <img 
                                                        src={imageUrl} 
                                                        onClick={() => setImageModal({ isOpen: true, src: imageUrl })} 
                                                        onError={(e) => { e.target.src = 'https://via.placeholder.com/150?text=No+Image' }}
                                                        className="h-10 w-16 object-cover rounded cursor-pointer hover:opacity-75 border border-gray-700 mx-auto transition-opacity" 
                                                        alt="Event" 
                                                        title="Bấm để phóng to" 
                                                    />
                                                ) : (
                                                    <span className="text-gray-600 text-[10px] italic">Trống</span>
                                                )}
                                            </td>
                                            <td className="px-4 py-3 text-center">
                                                {hasDetections ? (
                                                    <button onClick={() => handleOpenJson(ev.detections)} className="bg-gray-800 hover:bg-gray-700 border border-gray-700 hover:border-blue-500 text-blue-400 px-3 py-1.5 rounded text-xs transition-all shadow-sm">Xem Log</button>
                                                ) : (
                                                    <span className="text-gray-600 text-xs">-</span>
                                                )}
                                            </td>
                                            <td className="px-4 py-3 text-center">
                                                <span className={`border px-2.5 py-1 rounded text-xs ${ev.status === 'pending' ? 'bg-yellow-900/40 text-yellow-500 border-yellow-800/50' : 'bg-green-900/40 text-green-500 border-green-800/50'}`}>
                                                    {ev.status}
                                                </span>
                                            </td>
                                        </tr>
                                    );
                                })
                            )}
                        </tbody>
                    </table>
                </div>

                <div className="flex justify-between items-center mt-6 pt-4 border-t border-gray-800 text-sm text-gray-400">
                    <span className="font-medium">Trang {page} / {totalPages}</span>
                    <div className="flex space-x-2">
                        <button onClick={() => changePage(-1)} disabled={page <= 1} className="px-4 py-2 bg-gray-800 rounded hover:bg-gray-700 transition-colors disabled:opacity-50">◀ Trang trước</button>
                        <button onClick={() => changePage(1)} disabled={page >= totalPages} className="px-4 py-2 bg-gray-800 rounded hover:bg-gray-700 transition-colors disabled:opacity-50">Trang tiếp ▶</button>
                    </div>
                </div>
            </div>

            {/* Modal Hình ảnh */}
            {imageModal.isOpen && (
                <div className="fixed inset-0 bg-black/80 z-[100] flex items-center justify-center backdrop-blur-sm transition-opacity">
                    <div className="relative max-w-4xl w-full p-4 flex flex-col items-center">
                        <button onClick={() => setImageModal({ isOpen: false, src: '' })} className="absolute -top-6 right-4 text-gray-300 hover:text-white text-4xl font-bold drop-shadow-md">&times;</button>
                        <img 
                            src={imageModal.src} 
                            alt="Event Zoom" 
                            onError={(e) => { e.target.src = 'https://via.placeholder.com/800?text=Image+Not+Found' }}
                            className="max-w-full max-h-[80vh] object-contain rounded-lg border border-gray-700 shadow-2xl bg-black" 
                        />
                    </div>
                </div>
            )}

            {/* Modal JSON */}
            {jsonModal.isOpen && (
                <div className="fixed inset-0 bg-black/80 z-[100] flex items-center justify-center backdrop-blur-sm transition-opacity">
                    <div className="bg-gray-900 w-full max-w-2xl rounded-xl border border-gray-700 shadow-2xl overflow-hidden flex flex-col">
                        <div className="flex justify-between items-center p-4 border-b border-gray-800 bg-gray-950">
                            <h3 className="text-sm font-semibold text-blue-400">📋 Chi tiết Detections</h3>
                            <button onClick={() => setJsonModal({ isOpen: false, content: '' })} className="text-gray-400 hover:text-red-500 text-2xl font-bold leading-none">&times;</button>
                        </div>
                        <div className="p-4 overflow-auto max-h-[60vh] bg-gray-950/50">
                            <pre className="text-xs text-green-400 font-mono whitespace-pre-wrap">{jsonModal.content}</pre>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );

}