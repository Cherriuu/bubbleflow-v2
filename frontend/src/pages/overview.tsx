import { useEffect, useState } from "react";

import InventoryRow from "../components/inventory_row";


type InventoryItem = {
    id: number;
    name: string;
    base_unit: string;
    inventory: string;
    estimated_servings: number;
    status: "available" | "low" | "out";
};


type Topping = {
    id: number;
    prepared_item: number;
    quantity: string;
};


type OrderItem = {
    id: number;
    menu_item: number;
    quantity: number;
    size: "small" | "medium" | "large";
    sugar_level: string;
    ice_level: "no_ice" | "less_ice" | "regular_ice" | "extra_ice";
    toppings: Topping[];
};


type Order = {
    id: number;
    shop: number;
    status: "pending" | "completed"; /*| "cancelled"; */
    created_at: string;
    order_items: OrderItem[];
};


type Batch = {
    id: number;
    prepared_item: number;
    storage_location: number;
    initial_quantity: string;
    status: string;
    started_at: string;
    ready_at: string | null;
    expires_at: string;
    created_at: string;
    balance: string;
};


type PreparedItem = {
    id: number;
    name: string;
    default_batch_quantity: string;
    batch_label: string;
};


type MenuItem = {
    id: number;
    name: string;
};


type Recommendation = {
    id: number;
    name: string;
    base_unit: string;
    recommended_quantity: number | string;
};


function Overview() {
    const [inventory, setInventory] = useState<InventoryItem[]>([]);
    const [orders, setOrders] = useState<Order[]>([]);
    const [batches, setBatches] = useState<Batch[]>([]);
    const [preparedItems, setPreparedItems] = useState<PreparedItem[]>([]);
    const [menuItems, setMenuItems] = useState<MenuItem[]>([]);
    const [recommendations, setRecommendations] = useState<Recommendation[]>([]);


    useEffect(() => {
        async function getInventory() {
            const response = await fetch(
                "/api/inventory/"
            );

            const data = await response.json();
            setInventory(data);
        }


        async function getOrders() {
            const response = await fetch(
                "/api/orders/"
            );

            const data = await response.json();
            setOrders(data);
        }


        async function getBatches() {
            const response = await fetch(
                "/api/batches/"
            );

            const data = await response.json();
            setBatches(data);
        }


        async function getPreparedItems() {
            const response = await fetch(
                "/api/prepared-items/"
            );

            const data = await response.json();
            setPreparedItems(data);
        }


        async function getMenuItems() {
            const response = await fetch(
                "/api/menu-items/"
            );

            const data = await response.json();
            setMenuItems(data);
        }


        async function getRecommendations() {
            const response = await fetch(
                "/api/recommendations/"
            );

            const data = await response.json();
            setRecommendations(data);
        }


        getInventory();
        getOrders();
        getBatches();
        getPreparedItems();
        getMenuItems();
        getRecommendations();
    }, []);


    {/* Calculate counts for overview cards */}

    const lowStockCount = inventory.filter(
        (item) => item.status === "low" || item.status === "out"
    ).length;


    const batchesInProgressCount = batches.filter(
        (batch) =>
            batch.status === "preparing" ||
            batch.status === "cooling"
    ).length;


    const preparedItemsCount = inventory.length;


    const pendingOrdersCount = orders.filter(
        (order) => order.status === "pending"
    ).length;


    const inventorySnapshot = [...inventory]
        .sort((a, b) => {
            const priority = {
                out: 0,
                low: 1,
                available: 2
            };

            return priority[a.status] - priority[b.status];
        })
        .slice(0, 3);


    const batchesInProgress = batches
        .filter(
            (batch) =>
                batch.status === "preparing" ||
                batch.status === "cooling"
        )
        .slice(0, 3);


    const recentOrders = [...orders]
        .sort(
            (a, b) =>
                new Date(b.created_at).getTime() -
                new Date(a.created_at).getTime()
        )
        .slice(0, 3);


    const productionPriorities = recommendations
        .filter(
            (recommendation) =>
                Number(recommendation.recommended_quantity) > 0
        )
        .sort(
            (a, b) =>
                Number(b.recommended_quantity) -
                Number(a.recommended_quantity)
        )
        .slice(0, 3);


    return (
        <div className="w-full px-8 py-8">

            <div className="mb-10 text-center">
                <p className="mb-2 text-4xl font-semibold text-pink-300">
                    BubbleFlow
                </p>

                <h1 className="text-2xl font-bold tracking-tight text-stone-800">
                    Shop overview
                </h1>

                <p className="mt-3 text-base text-stone-500">
                    A quick look at inventory, production, and orders.
                </p>
            </div>


            <div className="mb-8 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">

                <div className="rounded-3xl border border-stone-200 bg-[#FFFDF7] p-6">
                    <p className="text-sm font-medium text-stone-400">
                        Prepared items
                    </p>

                    <p className="mt-2 text-3xl font-bold text-stone-800">
                        {preparedItemsCount}
                    </p>

                    <p className="mt-2 text-xs text-stone-400">
                        Currently tracked
                    </p>
                </div>


                <div className="rounded-3xl border border-stone-200 bg-[#FFFDF7] p-6">
                    <p className="text-sm font-medium text-stone-400">
                        Low stock
                    </p>

                    <p className="mt-2 text-3xl font-bold text-pink-300">
                        {lowStockCount}
                    </p>

                    <p className="mt-2 text-xs text-stone-400">
                        Items needing attention
                    </p>
                </div>


                <div className="rounded-3xl border border-stone-200 bg-[#FFFDF7] p-6">
                    <p className="text-sm font-medium text-stone-400">
                        Batches in progress
                    </p>

                    <p className="mt-2 text-3xl font-bold text-stone-800">
                        {batchesInProgressCount}
                    </p>

                    <p className="mt-2 text-xs text-stone-400">
                        Preparing or cooling
                    </p>
                </div>


                <div className="rounded-3xl border border-stone-200 bg-[#FFFDF7] p-6">
                    <p className="text-sm font-medium text-stone-400">
                        Pending orders
                    </p>

                    <p className="mt-2 text-3xl font-bold text-stone-800">
                        {pendingOrdersCount}
                    </p>

                    <p className="mt-2 text-xs text-stone-400">
                        Waiting to be completed
                    </p>
                </div>

            </div>


            {/* Inventory snapshot and active batches */}

            <div className="mb-6 grid gap-6 xl:grid-cols-2">

                <section className="overflow-hidden rounded-3xl border border-stone-200 bg-[#FFFDF7]">

                    <div className="border-b border-stone-200 px-6 py-5">
                        <div className="flex items-center justify-between">
                            <div>
                                <h2 className="text-lg font-semibold text-stone-800">
                                    Inventory snapshot
                                </h2>

                                <p className="mt-1 text-sm text-stone-400">
                                    Estimated drinks currently available.
                                </p>
                            </div>

                            <a
                                href="/inventory"
                                className="text-sm font-semibold text-pink-400 hover:text-pink-500"
                            >
                                View all
                            </a>
                        </div>
                    </div>


                    <div className="grid grid-cols-[2fr_1fr_1fr] px-6 py-3 text-xs font-semibold uppercase tracking-wide text-stone-400">
                        <span>Item</span>
                        <span>Servings</span>
                        <span>Status</span>
                    </div>


                    <div className="flex flex-col">
                        <div className="flex flex-col gap-2 px-6 py-3">
                            <div>
                                {inventorySnapshot.map((item) => (
                                    <div key={item.id} className="mb-2">
                                        <InventoryRow
                                            name={item.name}
                                            estimatedServings={item.estimated_servings}
                                            status={item.status}
                                        />
                                    </div>
                                ))}

                                {inventorySnapshot.length === 0 && (
                                    <p className="py-5 text-sm text-stone-400">
                                        No inventory available.
                                    </p>
                                )}
                            </div>
                        </div>
                    </div>

                </section>


                {/* Active batches */}

                <section className="overflow-hidden rounded-3xl border border-stone-200 bg-[#FFFDF7]">

                    <div className="border-b border-stone-200 px-6 py-5">
                        <div className="flex items-center justify-between">
                            <div>
                                <h2 className="text-lg font-semibold text-stone-800">
                                    Batches in progress
                                </h2>

                                <p className="mt-1 text-sm text-stone-400">
                                    What's being prepared right now.
                                </p>
                            </div>

                            <a
                                href="/batches"
                                className="text-sm font-semibold text-pink-400 hover:text-pink-500"
                            >
                                View all
                            </a>
                        </div>
                    </div>


                    {/* Active batches list */}

                    {batchesInProgress.map((batch) => {
                        const preparedItem = preparedItems.find(
                            (item) => item.id === batch.prepared_item
                        );

                        return (
                            <div
                                key={batch.id}
                                className="flex items-center justify-between border-b border-stone-100 px-6 py-5"
                            >
                                <div>
                                    <p className="font-medium text-stone-800">
                                        {preparedItem?.name || "Prepared item"}
                                    </p>

                                    <p className="mt-1 text-xs text-stone-400">
                                        Started at: {new Date(batch.started_at).toLocaleString()}
                                    </p>
                                </div>

                                <div className="text-right">
                                    <span
                                        className={
                                            batch.status === "cooling"
                                                ? "rounded-full bg-blue-100 px-3 py-1 text-xs font-semibold text-blue-700"
                                                : "rounded-full bg-[#dcecee] px-3 py-1 text-xs font-semibold text-stone-700"
                                        }
                                    >
                                        {batch.status === "cooling"
                                            ? "Cooling"
                                            : "Preparing"}
                                    </span>
                                </div>
                            </div>
                        );
                    })}

                    {batchesInProgress.length === 0 && (
                        <p className="px-6 py-6 text-sm text-stone-400">
                            No batches are currently in progress.
                        </p>
                    )}

                </section>

            </div>


            {/* Recent orders and up next */}

            <div className="grid gap-6 xl:grid-cols-[1.3fr_1fr]">

                <section className="overflow-hidden rounded-3xl border border-stone-200 bg-[#FFFDF7]">

                    <div className="border-b border-stone-200 px-6 py-5">
                        <div className="flex items-center justify-between">
                            <div>
                                <h2 className="text-lg font-semibold text-stone-800">
                                    Recent orders
                                </h2>

                                <p className="mt-1 text-sm text-stone-400">
                                    Latest activity from the order queue.
                                </p>
                            </div>

                            <a
                                href="/orders"
                                className="text-sm font-semibold text-pink-400 hover:text-pink-500"
                            >
                                View all
                            </a>
                        </div>
                    </div>


                    {/* Recent orders list */}

                    <div className="grid grid-cols-[0.7fr_1.6fr_1fr_1fr] px-6 py-3 text-xs font-semibold uppercase tracking-wide text-stone-400">
                        <span>Order</span>
                        <span>Drink</span>
                        <span>Status</span>
                        <span>Created</span>
                    </div>


                    <div className="flex flex-col">
                        {recentOrders.map((order) => {
                            const orderItem = order.order_items[0];

                            const menuItem = menuItems.find(
                                (item) => item.id === orderItem?.menu_item
                            );

                            return (
                                <div
                                    key={order.id}
                                    className="grid grid-cols-[0.7fr_1.6fr_1fr_1fr] items-center border-t border-stone-100 px-6 py-5"
                                >
                                    <p className="text-sm font-semibold text-stone-700">
                                        #{order.id}
                                    </p>

                                    <div>
                                        <p className="text-sm font-medium text-stone-800">
                                            {menuItem?.name || "Drink"}
                                        </p>

                                        {orderItem && (
                                            <p className="mt-1 text-xs text-stone-400">
                                                Qty {orderItem.quantity}
                                            </p>
                                        )}
                                    </div>

                                    <div>
                                        <span
                                            className={
                                                order.status === "completed"
                                                    ? "rounded-full bg-green-100 px-3 py-1 text-xs font-semibold text-green-700"
                                                    : "rounded-full bg-[#dcecee] px-3 py-1 text-xs font-semibold text-stone-700"
                                            }
                                        >
                                            {order.status === "completed"
                                                ? "Completed"
                                                : "Pending"}
                                        </span>
                                    </div>

                                    <p className="text-xs text-stone-400">
                                        {new Date(order.created_at).toLocaleString()}
                                    </p>
                                </div>
                            );
                        })}

                        {recentOrders.length === 0 && (
                            <p className="px-6 py-6 text-sm text-stone-400">
                                No recent orders.
                            </p>
                        )}
                    </div>

                </section>


                {/* Up next section */}

                <section className="rounded-3xl border border-stone-200 bg-[#FFFDF7] p-6">

                    <div className="flex items-center justify-between">
                        <div>
                            <h2 className="text-lg font-semibold text-stone-800">
                                Up next
                            </h2>

                            <p className="mt-1 text-sm text-stone-400">
                                Production priorities.
                            </p>
                        </div>

                        <a
                            href="/production"
                            className="text-sm font-semibold text-pink-400 hover:text-pink-500"
                        >
                            View all
                        </a>
                    </div>


                    <div className="mt-6 flex flex-col gap-3">

                        {productionPriorities.map((recommendation) => (
                            <div
                                key={recommendation.id}
                                className="rounded-2xl border border-pink-100 bg-pink-50 px-4 py-4"
                            >
                                <div className="flex items-center justify-between">
                                    <p className="font-medium text-stone-800">
                                        {recommendation.name}
                                    </p>

                                    <span className="rounded-full bg-pink-300 px-3 py-1 text-xs font-semibold text-white">
                                        Prepare
                                    </span>
                                </div>

                                <p className="mt-2 text-xs leading-5 text-stone-500">
                                    Suggested production:{" "}
                                    {Math.ceil(
                                        Number(recommendation.recommended_quantity)
                                    )}{" "}
                                    {recommendation.base_unit}
                                </p>
                            </div>
                        ))}


                        {productionPriorities.length === 0 && (
                            <div className="rounded-2xl border border-stone-200 px-4 py-4">
                                <p className="font-medium text-stone-800">
                                    Production looks good
                                </p>

                                <p className="mt-2 text-xs leading-5 text-stone-500">
                                    No additional production is currently recommended.
                                </p>
                            </div>
                        )}

                    </div>

                </section>

            </div>

        </div>
    );
}

export default Overview;