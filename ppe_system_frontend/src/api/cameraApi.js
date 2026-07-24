import axiosClient from './axiosClient';

const cameraApi = {
    getList: () => {
        return axiosClient.get('/list_cameras');
    },
    add: (data) => {
        return axiosClient.post('/add_camera', data);
    },
    edit: (id, data) => {
        return axiosClient.patch(`/edit_camera/${id}`, data);
    },
    remove: (id, data) => {
        return axiosClient.post(`/remove_camera/${id}`, data);
    },
    startCamera: (id, data) => {
        return axiosClient.post(`/start_camera/${id}`, data);
    },
    stopCamera: (id, data) => {
        return axiosClient.post(`/stop_camera/${id}`, data);
    },
    getStreamInfo: (id) => {
        return axiosClient.get(`/get_stream_info/${id}`);
    }

};

export default cameraApi;

