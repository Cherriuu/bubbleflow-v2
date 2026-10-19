import { useEffect, useState, type ReactNode } from "react";
import { apiFetch } from "../api/client";
import { AuthContext, type AuthStatus, type Shop } from "../context/auth";

// Pull the error message out of a Django REST Framework response
async function getErrorMessage(response: Response, fallback: string): Promise<string> {
    try {
        const data = await response.json();

        if (typeof data.error === "string") {
            return data.error;
        }

        if (typeof data.detail === "string") {
            return data.detail;
        }

        // Field errors look like {"email": ["Enter a valid email address."]}
        const firstField = Object.values(data)[0];

        if (Array.isArray(firstField) && typeof firstField[0] === "string") {
            return firstField[0];
        }
    } catch {
        // The response had no JSON body
    }

    return fallback;
}

function AuthProvider({ children }: { children: ReactNode }) {
    const [status, setStatus] = useState<AuthStatus>("loading");
    const [shop, setShop] = useState<Shop | null>(null);

    // Check whether the browser already has a session. This also sets the CSRF cookie.
    useEffect(() => {
        async function getCurrentShop() {
            try {
                const response = await apiFetch(
                    "/api/auth/me/",
                    {},
                    { redirectOnAuthError: false }
                );

                if (!response.ok) {
                    setStatus("logged_out");
                    return;
                }

                const data = await response.json();

                setShop(data.shop);
                setStatus("logged_in");
            } catch (error) {
                console.error(error);
                setStatus("logged_out");
            }
        }

        getCurrentShop();
    }, []);

    // Send login details and store the shop if it worked
    async function startSession(url: string, body: object | null, fallback: string): Promise<string | null> {
        try {
            const response = await apiFetch(
                url,
                {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: body ? JSON.stringify(body) : undefined
                },
                { redirectOnAuthError: false }
            );

            if (!response.ok) {
                return await getErrorMessage(response, fallback);
            }

            const data = await response.json();

            setShop(data.shop);
            setStatus("logged_in");

            return null;
        } catch (error) {
            console.error(error);
            return fallback;
        }
    }

    function login(email: string, password: string) {
        return startSession(
            "/api/auth/login/",
            { email, password },
            "Something went wrong while logging in."
        );
    }

    function register(shopName: string, email: string, password: string) {
        return startSession(
            "/api/auth/register/",
            { shop_name: shopName, email, password },
            "Something went wrong while creating your shop."
        );
    }

    function demoLogin() {
        return startSession(
            "/api/auth/demo-login/",
            null,
            "Something went wrong while opening the demo."
        );
    }

    async function logout() {
        try {
            await apiFetch(
                "/api/auth/logout/",
                { method: "POST" },
                { redirectOnAuthError: false }
            );
        } catch (error) {
            console.error(error);
        }

        setShop(null);
        setStatus("logged_out");
    }

    return (
        <AuthContext.Provider value={{ status, shop, login, register, demoLogin, logout }}>
            {children}
        </AuthContext.Provider>
    );
}

export default AuthProvider;
