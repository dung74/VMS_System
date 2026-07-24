import {useEffect, useRef} from 'react';
import cameraApi from "../api/cameraApi";


export default function VideoStream({cameraId, onClose}) {
    const videoRef = useRef(null);

    useEffect(() => {
        const  pc = new RTCPeerConnection();
        pc.addEventListener('track', (event) => {
            if (videoRef.current) videoRef.current.srcObject = event.streams[0];
        });
        pc.addTransceiver('video', {direction: 'recvonly'});

        const startStream = async () => {
            try {

                const response = await cameraApi.getStreamInfo(cameraId);
                const streamInfo = response.data || response;

                const webrtcUrl = streamInfo.webrtc_offer_url;
                if (!webrtcUrl) {
                    throw new Error('WebRTC offer URL not found');
                }
                const offer = await pc.createOffer();
                await pc.setLocalDescription(offer);

                const answerResponse = await fetch(webrtcUrl, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({sdp: pc.localDescription.sdp, type: pc.localDescription.type})
                });
                if (!answerResponse.ok) {
                    throw new Error('Failed to get WebRTC answer');
                }

                const answer = await answerResponse.json();
                await pc.setRemoteDescription(answer);

            } catch (error) {
                console.error('Error starting video stream:', error);
                alert('Camera have not been started by admin ')
                onClose(cameraId);
            }

        };
        startStream();

        return () => {
            pc.close();
        }

    }, [cameraId, onClose]);

    return (
        <div className="bg-black rounded-xl border border-gray-800 overflow-hidden relative aspect-video shadow-lg border-green-500/30 group">
            <div className="absolute top-2 left-2 bg-black/60 px-2 py-1 rounded text-xs flex items-center z-10">
                <span className="w-2 h-2 rounded-full bg-red-500 mr-2 animate-pulse"></span>CAM-{cameraId}
            </div>
            <button onClick={() => onClose(cameraId)} className="absolute top-2 right-2 bg-black/60 hover:bg-red-600 px-2 py-1 rounded text-xs text-white z-10 opacity-0 group-hover:opacity-100 transition-opacity">
                ✕ Đóng
            </button>
            <video ref={videoRef} className="w-full h-full object-contain" autoPlay playsInline muted></video>
        </div>
    );
}