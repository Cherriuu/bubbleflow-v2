// organized place to store all the API endpoints so React can communicate with Django backend
import type { HealthCheckResponse } from "../types/api";

export async function checkHealth(): Promise<HealthCheckResponse> {
    const response = await fetch('/api/health/');
    if (!response.ok) {
        throw new Error('HTTP error! status: ' + response.status);
    }
    const data = await response.json();
    return data;
}


