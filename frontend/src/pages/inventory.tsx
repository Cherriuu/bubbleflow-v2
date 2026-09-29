import InventoryRow from "../components/inventory_row"
import { useEffect, useState } from "react"

async function getInventory() {
    const response = await fetch('http://localhost:8000/api/inventory/');
    // reads the JSON response body and returns it as a Javascript object
    const data = await response.json();
    return data;
}

function Inventory() {
    const [inventory, setInventory] = useState([]);

    useEffect(() => {
        getInventory()
    })
  return (
    <div className="w-full px-8 py-8">

      {/* Page heading */}
      <div className="text-center mb-10">
        <p className="mb-2 text-4xl font-semibold text-pink-300">
          Inventory
        </p>

        <h1 className="text-2xl font-bold tracking-tight text-stone-800">
          What's in stock?
        </h1>

        <p className="mt-3 text-base text-black-500">
          Keep an eye on prepared ingredients and know when it's time
          to make more.
        </p>
      </div>


      {/* Summary cards */}
      <div className="mb-8 grid gap-4 sm:grid-cols-3">

        <div className="rounded-3xl border border-stone-200 bg-[#FFFDF7] p-6">
          <p className="text-sm font-medium text-stone-400">
            Prepared items
          </p>

          {/* TODO: You will eventually put real data here */}
          <p className="mt-2 text-3xl font-bold text-stone-800">
            --
          </p>
        </div>


        <div className="rounded-3xl border border-stone-200 bg-[#FFFDF7] p-6">
          <p className="text-sm font-medium text-stone-400">
            Low stock
          </p>

          {/* TODO: You will eventually calculate this */}
          <p className="mt-2 text-3xl font-bold text-pink-300">
            --
          </p>
        </div>


        <div className="rounded-3xl border border-stone-200 bg-[#FFFDF7] p-6">
          <p className="text-sm font-medium text-stone-400">
            Active batches
          </p>

          {/* TODO: You will eventually calculate this */}
          <p className="mt-2 text-3xl font-bold text-stone-800">
            --
          </p>
        </div>

      </div>


      {/* Inventory list */}
      <section className="overflow-hidden rounded-3xl border border-stone-200 bg-[#FFFDF7]">

        <div className="border-b border-stone-200 px-6 py-5">
          <h2 className="text-lg font-semibold text-stone-800">
            Prepared inventory
          </h2>

          <p className="mt-1 text-sm text-stone-400">
            Current usable inventory across ready batches.
          </p>
        </div>


        {/* Column labels */}
        <div className="grid grid-cols-[2fr_1fr_1fr] px-6 py-3 text-xs font-semibold uppercase tracking-wide text-stone-400">
          <span>Item</span>
          <span>Available</span>
          <span>Status</span>
        </div>


        <div className="flex flex-col gap-2 px-6 py-3">
        {/* Inventory rows are filled with real data in the future */}
        
        </div>

      </section>

    </div>
  );
}

export default Inventory;