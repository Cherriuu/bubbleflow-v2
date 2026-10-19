// organized place to store all the API endpoints so React can communicate with Django backend
import type { HealthCheckResponse } from "../types/api";

// Methods that change data. Django requires a CSRF token for these.
const UNSAFE_METHODS = ["POST", "PUT", "PATCH", "DELETE"];

// Read the CSRF token that Django sets in the csrftoken cookie
function getCsrfToken(): string | null {
    const cookie = document.cookie
        .split("; ")
        .find((row) => row.startsWith("csrftoken="));

    return cookie ? decodeURIComponent(cookie.split("=")[1]) : null;
}

type ApiFetchOptions = {
    // Set to false for requests where being logged out is expected, such as checking the session or logging in
    redirectOnAuthError?: boolean;
};

// Use this instead of fetch for every API request.
// Sends the session cookie, adds the CSRF token to requests that change data,
// and sends the user to the login page if their session has ended.
export async function apiFetch(
    url: string,
    init: RequestInit = {},
    { redirectOnAuthError = true }: ApiFetchOptions = {}
): Promise<Response> {
    const method = (init.method ?? "GET").toUpperCase();
    const headers = new Headers(init.headers);

    if (UNSAFE_METHODS.includes(method)) {
        const token = getCsrfToken();

        if (token) {
            headers.set("X-CSRFToken", token);
        }
    }

    const response = await fetch(url, {
        ...init,
        headers,
        credentials: "include",
    });

    const onAuthPage = ["/login", "/register"].includes(window.location.pathname);

    if (redirectOnAuthError && !onAuthPage && (response.status === 401 || response.status === 403)) {
        window.location.assign("/login");
    }

    return response;
}

export async function checkHealth(): Promise<HealthCheckResponse> {
    const response = await apiFetch('/api/health/');
    if (!response.ok) {
        throw new Error('HTTP error! status: ' + response.status);
    }
    const data = await response.json();
    return data;
}
