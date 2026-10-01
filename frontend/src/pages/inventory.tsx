import InventoryRow from "../components/inventory_row";
import { useEffect, useState } from "react";

type InventoryItem = {
    id: number;
    name: string;
    base_unit: string;
    inventory: string;
    estimated_servings: number;
    status: "available" | "low" | "out";
};

function Inventory() {
    const [inventory, setInventory] = useState<InventoryItem[]>([]);

    useEffect(() => {
        async function getInventory() {
            const response = await fetch(
                "http://localhost:8000/api/inventory/"
            );

            const data = await response.json();
            setInventory(data);
        }

        getInventory();
    }, []);

    const lowStockCount = inventory.filter(
        (item) => item.status === "low" || item.status === "out"
    ).length;

    const readyBatchesCount = inventory.filter(
        (item) => item.status === "available" || item.status === "low"
    )

    return (
        <div className="w-full px-8 py-8">

            <div className="mb-10 text-center">
                <p className="mb-2 text-4xl font-semibold text-pink-300">
                    Inventory
                </p>

                <h1 className="text-2xl font-bold tracking-tight text-stone-800">
                    What's in stock?
                </h1>

                <p className="mt-3 text-base text-stone-500">
                    Keep an eye on prepared items and know when it's time
                    to make more.
                </p>
            </div>

            <div className="mb-8 grid gap-4 sm:grid-cols-3">

                <div className="rounded-3xl border border-stone-200 bg-[#FFFDF7] p-6">
                    <p className="text-sm font-medium text-stone-400">
                        Prepared items
                    </p>

                    <p className="mt-2 text-3xl font-bold text-stone-800">
                        {inventory.length}
                    </p>
                </div>

                <div className="rounded-3xl border border-stone-200 bg-[#FFFDF7] p-6">
                    <p className="text-sm font-medium text-stone-400">
                        Low stock
                    </p>

                    <p className="mt-2 text-3xl font-bold text-pink-300">
                        {lowStockCount}
                    </p>
                </div>

                <div className="rounded-3xl border border-stone-200 bg-[#FFFDF7] p-6">
                    <p className="text-sm font-medium text-stone-400">
                        Ready batches
                    </p>

                    <p className="mt-2 text-3xl font-bold text-stone-800">
                        {readyBatchesCount.length}
                    </p>
                </div>

            </div>

            <section className="overflow-hidden rounded-3xl border border-stone-200 bg-[#FFFDF7]">

                <div className="border-b border-stone-200 px-6 py-5">
                    <h2 className="text-lg font-semibold text-stone-800">
                        Prepared inventory
                    </h2>

                    <p className="mt-1 text-sm text-stone-400">
                        Estimated servings available across ready batches.
                    </p>
                </div>

                <div className="grid grid-cols-[2fr_1fr_1fr] px-6 py-3 text-xs font-semibold uppercase tracking-wide text-stone-400">
                    <span>Item</span>
                    <span>Servings</span>
                    <span>Status</span>
                </div>

                <div className="flex flex-col gap-2 px-6 py-3">
                    {inventory.map((item) => (
                        <InventoryRow
                            key={item.id}
                            name={item.name}
                            estimatedServings={item.estimated_servings}
                            status={item.status}
                        />
                    ))}
                </div>

            </section>

        </div>
    );
}

export default Inventory;