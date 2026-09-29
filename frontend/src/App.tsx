import './App.css'
import { useState } from "react"
import { BrowserRouter, Routes, Route} from "react-router-dom";
import Sidebar from "./components/sidebar";

/* Import the components for the different pages */
import Inventory from "./pages/inventory"
import { Batches } from "./pages/batches"
import { Orders } from "./pages/orders"
import { Production } from "./pages/production"
import About from "./pages/about"
import { Overview } from "./pages/overview"

function App() {
  return (
    <BrowserRouter>
    {/* Routes */}
      <div className="flex min-h-screen bg-[#FAF8F2]">
      <Sidebar />

      <main className="flex-1 p-8"></main>
      <Routes>
        <Route path="/" element={<Overview/>} />
        <Route path="/about" element={<About/>} />
        <Route path="/inventory" element={<Inventory/>} />
        <Route path="/batches" element={<Batches/>} />
        <Route path="/orders" element={<Orders/>} />
        <Route path="/production" element={<Production/>} />
      </Routes>

    </div>
    </BrowserRouter>
  )
}

export default App
