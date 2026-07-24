import axiosClient from './axiosClient';

const authApi = {
    login: (data) => {
        return axiosClient.post('/auth/login', data);
    },
    register: (data) => {
        return axiosClient.post('/auth/register', data);
    },
    logout: () => {
        return axiosClient.post('/auth/logout');
    },
    getCurrentUser: () => {
        return axiosClient.get('/auth/me');
    }
};

export default authApi;

