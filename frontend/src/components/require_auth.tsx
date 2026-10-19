import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "../context/auth";
import Sidebar from "./sidebar";

// The app layout for logged-in shops. Sends everyone else to the login page.
function RequireAuth() {
    const { status } = useAuth();
    const location = useLocation();

    // Wait for /api/auth/me/ so a logged-in shop doesn't flash the login page
    if (status === "loading") {
        return <div className="min-h-screen bg-[#FAF8F2]" />;
    }

    if (status === "logged_out") {
        return <Navigate to="/login" replace state={{ from: location.pathname }} />;
    }

    return (
      <div className="flex min-h-screen bg-[#FAF8F2]">
        <Sidebar />

        <main className="flex-1 p-8">
          <Outlet />
        </main>
      </div>
    );
}

export default RequireAuth;
