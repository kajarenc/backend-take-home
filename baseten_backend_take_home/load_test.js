import http from 'k6/http';

export const options = {
    scenarios: {
        constant_request_rate: {
            executor: 'constant-arrival-rate',
            rate: 10, // 10 requests per second
            timeUnit: '1s',
            duration: '30s', // for 30 seconds
            preAllocatedVUs: 2, // how many VUs to pre-allocate
            maxVUs: 10, // maximum number of VUs to scale up to
        },
    },
};

export default function () {
    const url = 'http://localhost:8000/invoke';
    const payload = JSON.stringify({
        worklet_input: {
            model_id: '1',
            input: [1, 2, 3],
        },
    });

    const params = {
        headers: {
            'Content-Type': 'application/json',
        },
    };

    http.post(url, payload, params);
}