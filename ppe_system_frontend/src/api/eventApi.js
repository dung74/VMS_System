import axiosClient from './axiosClient';

const eventApi = {
    getList: (page = 1, limit = 10) => {
        return axiosClient.get('/list_events', { params: { page, limit}});
    }

};

export default eventApi;