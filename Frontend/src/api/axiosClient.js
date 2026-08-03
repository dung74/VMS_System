import axios from 'axios';

const axiosClient = axios.create({

    baseURL: '/api/cloud',
    headers: {
        'Content-Type': 'application/json',
    },
});


axiosClient.interceptors.request.use(
    (config) => {
        //take token from localStorage after user login
        const token = localStorage.getItem('access_token');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => Promise.reject(error)
);


axiosClient.interceptors.response.use(
    (response) => {
        return response;
    },
    (error) => {
        if (error.response && error.response.status ===401) {
            console.error('Unauthorized access - perhaps the token is invalid or expired.');
        }
        return Promise.reject(error);
    }
);

export default axiosClient;

