import axiosClient from './axiosClient';

const modelApi = {
    getList: () => {
        return axiosClient.get('/list_models');
    },
    add: (data) => {
        return axiosClient.post('/add_model', data);
    },
    edit: (id, data) => {
        return axiosClient.patch(`/edit_model/${id}`, data);
    },
    remove: (id) => {
        return axiosClient.post(`/remove_model/${id}`);
    }
};

export default modelApi;
