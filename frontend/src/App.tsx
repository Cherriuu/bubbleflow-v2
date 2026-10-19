/* Enables client-side routing in */
import { BrowserRouter, Routes, Route } from "react-router-dom";
import AuthProvider from "./components/auth_provider";
import RequireAuth from "./components/require_auth";
/* Import the components for the different pages */
import Inventory from "./pages/inventory"
import Batches from "./pages/batches"
import Orders from "./pages/orders"
import Production from "./pages/production"
import About from "./pages/about"
import Overview from "./pages/overview"
import Login from "./pages/login"
import Register from "./pages/register"

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        {/* Routes */}
        <Routes>
          {/* Public pages */}
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />

          {/* Pages that need a logged-in shop, shown with the sidebar */}
          <Route element={<RequireAuth />}>
            <Route path="/" element={<Overview />} />
            <Route path="/about" element={<About />} />
            <Route path="/inventory" element={<Inventory />} />
            <Route path="/batches" element={<Batches />} />
            <Route path="/orders" element={<Orders />} />
            <Route path="/production" element={<Production />} />
          </Route>
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  )
}

export default App
