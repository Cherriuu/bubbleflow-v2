// Shares the logged-in shop with every page. The provider lives in components/auth_provider.tsx.
import { createContext, useContext } from "react";

export type Shop = {
    id: number;
    name: string;
};

export type AuthStatus = "loading" | "logged_in" | "logged_out";

export type AuthContextValue = {
    status: AuthStatus;
    shop: Shop | null;
    // Each action returns an error message, or null if it worked
    login: (email: string, password: string) => Promise<string | null>;
    register: (shopName: string, email: string, password: string) => Promise<string | null>;
    demoLogin: () => Promise<string | null>;
    logout: () => Promise<void>;
};

export const AuthContext = createContext<AuthContextValue | null>(null);

export function useAuth(): AuthContextValue {
    const value = useContext(AuthContext);

    if (value === null) {
        throw new Error("useAuth must be used inside AuthProvider");
    }

    return value;
}
