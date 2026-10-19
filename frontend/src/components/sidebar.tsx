import { NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../context/auth";

function Sidebar() {
  const { shop, logout } = useAuth();
  const navigate = useNavigate();

  async function handleLogout() {
    await logout();
    navigate("/login", { replace: true });
  }

  return (
    <aside className="flex min-h-screen w-64 flex-col border-r border-stone-200 bg-[#FFFDF7] px-5 py-8">
      
      {/* Logo */}
      <div className="mb-10 px-3">
        <h1 className="text-4xl font-bold tracking-tight text-pink-300">
          BubbleFlow
        </h1>
      </div>

      {/* Main navigation */}
      <nav className="flex flex-col gap-2">

        <NavLink to="/" className="flex items-center gap-3 rounded-2xl px-3 py-3 text-base font-medium text-stone-700 hover:bg-[#dcecee] hover:text-stone-900">
          Overview
        </NavLink>
        
        <NavLink to="/inventory" className="flex items-center gap-3 rounded-2xl px-3 py-3 text-base font-medium text-stone-700 hover:bg-[#dcecee] hover:text-stone-900">
          Inventory
        </NavLink>

        <NavLink to="/batches" className="flex items-center gap-3 rounded-2xl px-3 py-3 text-base font-medium text-stone-700 hover:bg-[#dcecee] hover:text-stone-900">
          Batches
        </NavLink>

        <NavLink to="/orders" className="flex items-center gap-3 rounded-2xl px-3 py-3 text-base font-medium text-stone-700 hover:bg-[#dcecee] hover:text-stone-900">
          Orders
        </NavLink>

        <NavLink to="/production" className="flex items-center gap-3 rounded-2xl px-3 py-3 text-base font-medium text-stone-700 hover:bg-[#dcecee] hover:text-stone-900">
          Production
        </NavLink>

        <NavLink to="/about" className="flex items-center gap-3 rounded-2xl px-3 py-3 text-base font-medium text-stone-700 hover:bg-[#dcecee] hover:text-stone-900">
          About
        </NavLink>

      </nav>

      {/* Logged-in shop */}
      <div className="mt-auto flex flex-col gap-2 border-t border-stone-200 pt-5">
        <p className="truncate px-3 text-sm font-medium text-stone-400">
          {shop?.name}
        </p>

        <button type="button" onClick={handleLogout} className="flex items-center gap-3 rounded-2xl px-3 py-3 text-left text-base font-medium text-stone-700 hover:bg-[#dcecee] hover:text-stone-900">
          Log out
        </button>
      </div>
    </aside>
  );
}

export default Sidebar;