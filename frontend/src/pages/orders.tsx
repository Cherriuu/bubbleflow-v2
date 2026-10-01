import { useState, useEffect } from "react";

{/* Define the types for the data */}
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
    status: "pending" | "completed" | "cancelled";
    created_at: string;
    order_items: OrderItem[];
};

type MenuItem = {
    id: number;
    shop: number;
    name: string;
    is_active: boolean;
};

type PreparedItem = {
    id: number;
    shop: number;
    name: string;
};

{/* Pull data from the backend */}

function Orders() {
    const [orders, setOrders] = useState<Order[]>([]);
    const [menuItems, setMenuItems] = useState<MenuItem[]>([]);
    const [preparedItems, setPreparedItems] = useState<PreparedItem[]>([]);

    const [newOrder, setNewOrder] = useState<number | null>(null);

    const [selectedSize, setSelectedSize] = useState<"small" | "medium" | "large">("medium");

    const [selectedSugar, setSelectedSugar] = useState("100");

    const [selectedIce, setSelectedIce] = useState("regular_ice");

    const [extraBoba, setExtraBoba] = useState(0);

    const [quantity, setQuantity] = useState(1);
    

    useEffect(() => {
        async function getOrders() {
            const response = await fetch(
                "http://localhost:8000/api/orders/"
            );

            const data = await response.json();
            setOrders(data);
        }

        getOrders();
    }, []);

    useEffect(() => {
        async function getMenuItems() {
            const response = await fetch(
                "http://localhost:8000/api/menu-items/"
            );

            const data = await response.json();
            setMenuItems(data);
        }

        getMenuItems();
    }, []);

    useEffect(() => {
        async function getPreparedItems() {
            const response = await fetch(
                "http://localhost:8000/api/prepared-items/"
            );

            const data = await response.json();
            setPreparedItems(data);
        }

        getPreparedItems();
    }, []);

    async function createOrder() {
        if (newOrder === null) {
            alert("Please select a drink.");
            return;
        }

        const selectedMenuItem = menuItems.find(
            item => item.id === newOrder
        );

        if (!selectedMenuItem) {
            alert("Selected drink could not be found.");
            return;
        }

        const boba = preparedItems.find(
            item => item.name === "Tapioca Pearls"
        );

        if (extraBoba > 0 && !boba) {
            alert("Tapioca Pearls could not be found.");
            return;
        }

        const toppings = [];

        if (extraBoba > 0 && boba) {
            toppings.push({
                prepared_item_id: boba.id,
                quantity: extraBoba
            });
        }

        const orderData = {
            shop_id: selectedMenuItem.shop,
            items: [
                {
                    menu_item_id: newOrder,
                    quantity: quantity,
                    size: selectedSize,
                    sugar_level: selectedSugar,
                    ice_level: selectedIce,
                    toppings: toppings
                }
            ]
        };
        
        console.log("Sending:", orderData);

        try {
            const response = await fetch(
                "http://localhost:8000/api/orders/create/",
                {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify(orderData)
                }
            );

            const data = await response.json();

            if (!response.ok) {
                alert(
                    data.error ||
                    "The order could not be created."
                );
                return;
            }

            console.log(
                "Order created successfully:",
                data.order
            );

            setOrders(prevOrders => [
                ...prevOrders,
                data.order
            ]);

            if (data.warnings.length > 0) {
                alert(data.warnings.join("\n"));
            }

        } catch (error) {
            console.error(
                "Error creating order:",
                error
            );

            alert(
                "Something went wrong while creating the order."
            );
        }
    }

    async function completeOrder(orderId: number) {
        try {
            const response = await fetch(
                `http://localhost:8000/api/orders/${orderId}/complete/`,
                {
                    method: "POST"
                }
            );

            const data = await response.json();

            if (!response.ok) {
                alert(
                    data.error ||
                    "The order could not be completed."
                );
                return;
            }

            setOrders(prevOrders =>
                prevOrders.map(order =>
                    order.id === orderId
                        ? data
                        : order
                )
            );

        } catch (error) {
            console.error(
                "Error completing order:",
                error
            );

            alert(
                "Something went wrong while completing the order."
            );
        }
    }

    {/* Orders pending and completed orders for today */}

    const pendingOrders = orders.filter((order: Order) => {
        const orderDate = new Date(order.created_at);
        const today = new Date();

        return (
            order.status === "pending" &&
            orderDate.getFullYear() === today.getFullYear() &&
            orderDate.getMonth() === today.getMonth() &&
            orderDate.getDate() === today.getDate()
        );
    })

    const completedOrders = orders.filter((order: Order) => {
        const orderDate = new Date(order.created_at);
        const today = new Date();

        return (
            order.status === "completed" &&
            orderDate.getFullYear() === today.getFullYear() &&
            orderDate.getMonth() === today.getMonth() &&
            orderDate.getDate() === today.getDate()
        );
    })

    const amountOfPendingOrders = pendingOrders.length;
    const amountOfCompletedOrders = completedOrders.length;
    
    let drinksToday = 0;

    for (const order of completedOrders) {
        for (const item of order.order_items) {
            drinksToday += item.quantity;
        }
    }

    for (const order of pendingOrders) {
        for (const item of order.order_items) {
            drinksToday += item.quantity;
        }
    }

    const ordersToday = drinksToday;

    return (
        <div className="w-full px-8 py-8">

            <div className="mb-10 text-center">
                <p className="mb-2 text-4xl font-semibold text-pink-300">
                    Orders
                </p>

                <h1 className="text-2xl font-bold tracking-tight text-stone-800">
                    Keep orders moving
                </h1>

                <p className="mt-3 text-base text-stone-500">
                    Record customized drinks and keep track of current orders.
                </p>
            </div>

            <div className="mb-8 grid gap-4 sm:grid-cols-3">

                <div className="rounded-3xl border border-stone-200 bg-[#FFFDF7] p-6">
                    <p className="text-sm font-medium text-stone-400">
                        Pending
                    </p>

                    <p className="mt-2 text-3xl font-bold text-stone-800">
                        {amountOfPendingOrders}
                    </p>
                </div>

                <div className="rounded-3xl border border-stone-200 bg-[#FFFDF7] p-6">
                    <p className="text-sm font-medium text-stone-400">
                        Completed today
                    </p>

                    <p className="mt-2 text-3xl font-bold text-stone-800">
                        {amountOfCompletedOrders}
                    </p>
                </div>

                <div className="rounded-3xl border border-stone-200 bg-[#FFFDF7] p-6">
                    <p className="text-sm font-medium text-stone-400">
                        Drinks today
                    </p>

                    <p className="mt-2 text-3xl font-bold text-pink-300">
                        {ordersToday}
                    </p>
                </div>

            </div>

            { /* Order form and recent orders section */}

            <div className="grid gap-6 xl:grid-cols-[1fr_1.6fr]">

                <section className="rounded-3xl border border-stone-200 bg-[#FFFDF7] p-6">

                    <div className="mb-6">
                        <h2 className="text-lg font-semibold text-stone-800">
                            New order
                        </h2>

                        <p className="mt-1 text-sm text-stone-400">
                            Add a drink and its customizations.
                        </p>
                    </div>

                    <div className="flex flex-col gap-5">

                        <div>
                            <label className="mb-2 block text-sm font-medium text-stone-600">
                                Drink
                            </label>

                            <select
                                onChange={(e) => setNewOrder(Number(e.target.value))}
                                defaultValue=""
                                className="w-full rounded-2xl border border-stone-200 bg-white px-4 py-3 text-sm text-stone-700 outline-none focus:border-pink-300"
                            >
                                <option value="" disabled>
                                    Select a drink
                                </option>

                                {menuItems.map((item: MenuItem) => (
                                    <option key={item.id} value={item.id}>
                                        {item.name}
                                    </option>
                                ))}
                                
                            </select>
                        </div>

                        {/* Leaving sizes, sugar, ice, extra boba, and quantity as they are for now. */}

                        <div>
                            <label className="mb-2 block text-sm font-medium text-stone-600">
                                Size
                            </label>

                            <div className="grid grid-cols-3 gap-2">
                                <button
                                    onClick={() => setSelectedSize("small")}
                                    type="button"
                                    className={`rounded-full border px-4 py-2 text-sm font-medium transition ${
                                        selectedSize === "small"
                                            ? "border-pink-300 bg-pink-100 text-pink-500"
                                            : "border-stone-200 bg-white text-stone-600 hover:border-pink-300"
                                    }`}
                                >
                                    Small
                                </button>

                                <button
                                    onClick={() => setSelectedSize("medium")}
                                    type="button"
                                    className={`rounded-full border px-4 py-2 text-sm font-medium transition ${
                                        selectedSize === "medium"
                                            ? "border-pink-300 bg-pink-100 text-pink-500"
                                            : "border-stone-200 bg-white text-stone-600 hover:border-pink-300"
                                    }`}
                                >
                                    Medium
                                </button>

                                <button
                                    onClick={() => setSelectedSize("large")}
                                    type="button"
                                    className={`rounded-full border px-4 py-2 text-sm font-medium transition ${
                                        selectedSize === "large"
                                            ? "border-pink-300 bg-pink-100 text-pink-500"
                                            : "border-stone-200 bg-white text-stone-600 hover:border-pink-300"
                                    }`}
                                >
                                    Large
                                </button>
                            </div>
                        </div>

                        <div>
                            <label className="mb-2 block text-sm font-medium text-stone-600">
                                Sugar
                            </label>

                            <select
                                onChange={(e) => setSelectedSugar(e.target.value)}
                                defaultValue="100"
                                className="w-full rounded-2xl border border-stone-200 bg-white px-4 py-3 text-sm text-stone-700 outline-none focus:border-pink-300"
                            >
                                <option value="0">0%</option>
                                <option value="25">25%</option>
                                <option value="50">50%</option>
                                <option value="75">75%</option>
                                <option value="100">100%</option>
                            </select>
                        </div>

                        <div>
                            <label className="mb-2 block text-sm font-medium text-stone-600">
                                Ice
                            </label>

                            <select
                                onChange={(e) => setSelectedIce(e.target.value)}
                                defaultValue="regular_ice"
                                className="w-full rounded-2xl border border-stone-200 bg-white px-4 py-3 text-sm text-stone-700 outline-none focus:border-pink-300"
                            >
                                <option value="no_ice">No ice</option>
                                <option value="less_ice">Less ice</option>
                                <option value="regular_ice">Regular ice</option>
                                <option value="extra_ice">Extra ice</option>
                            </select>
                        </div>

                        <div>
                            <label className="mb-2 block text-sm font-medium text-stone-600">
                                Extra boba
                            </label>

                            <select
                                onChange={(e) => setExtraBoba(Number(e.target.value))}
                                defaultValue="0"
                                className="w-full rounded-2xl border border-stone-200 bg-white px-4 py-3 text-sm text-stone-700 outline-none focus:border-pink-300"
                            >
                                <option value="0">
                                    None
                                </option>

                                <option value="1">
                                    +1 scoop
                                </option>

                                <option value="2">
                                    +2 scoops
                                </option>
                            </select>
                        </div>

                        <div>
                            <label className="mb-2 block text-sm font-medium text-stone-600">
                                Quantity
                            </label>

                            <input
                                type="number"
                                min="1"
                                defaultValue="1"
                                onChange={(e) => setQuantity(Number(e.target.value))}
                                className="w-full rounded-2xl border border-stone-200 bg-white px-4 py-3 text-sm text-stone-700 outline-none focus:border-pink-300"
                            />
                        </div>

                        <button
                            type="button"
                            onClick={createOrder}
                            className="mt-2 rounded-full bg-[#dcecee] px-5 py-3 text-sm font-semibold text-stone-700 transition hover:brightness-95"
                        >
                            Create order
                        </button>

                    </div>

                </section>

                {/* Pending and completed orders section */}

                <section className="overflow-hidden rounded-3xl border border-stone-200 bg-[#FFFDF7]">

                    <div className="border-b border-stone-200 px-6 py-5">
                        <h2 className="text-lg font-semibold text-stone-800">
                            Recent orders
                        </h2>

                        <p className="mt-1 text-sm text-stone-400">
                            Pending and recently completed shop orders.
                        </p>
                    </div>

                    <div className="grid grid-cols-[0.7fr_1.6fr_1fr_1fr] px-6 py-3 text-xs font-semibold uppercase tracking-wide text-stone-400">
                        <span>Order</span>
                        <span>Drink</span>
                        <span>Status</span>
                        <span>Time</span>
                    </div>


                    {orders.map((order) => (

                        <div
                            key={order.id}
                            className="border-t border-stone-100 px-6 py-5"
                        >

                            <div className="grid grid-cols-[0.7fr_1.6fr_1fr_1fr] items-center">

                                {/* ORDER NUMBER */}
                                <div className="text-sm font-semibold text-stone-700">
                                    Order #{order.id}
                                </div>


                                {/* DRINKS */}
                                <div className="space-y-2">

                                    {order.order_items.map((item) => (

                                        <div key={item.id}>
                                            <p className="font-medium text-stone-800">
                                                {menuItems.find((menuItem) => menuItem.id === item.menu_item)?.name || "Unknown drink"}
                                            </p>

                                            <p className="mt-1 text-xs text-stone-400">
                                                {item.quantity} x {item.size} - Sugar: {item.sugar_level}, Ice: {item.ice_level}
                                            </p>
                                        </div>

                                    ))}
                                </div>


                                {/* STATUS */}
                                <div>
                                    <span className="rounded-full px-3 py-1 text-xs font-semibold">
                                        {order.status === "pending" && (
                                            <span className="bg-yellow-100 text-yellow-700">
                                                Pending
                                            </span>
                                        )}

                                        {order.status === "completed" && (
                                            <span className="bg-green-100 text-green-700">
                                                Completed
                                            </span>
                                        )}
                                    </span>
                                </div>


                                {/* TIME */}
                                <p className="text-sm text-stone-500">
                                    {new Date(order.created_at).toLocaleTimeString([], {
                                        hour: "2-digit",
                                        minute: "2-digit"
                                    })}
                                </p>

                            </div>


                            {order.status === "pending" && (
                                <div className="mt-4 flex justify-end gap-2">
                                    <button
                                        type="button"
                                        onClick={() => completeOrder(order.id)}
                                        className="rounded-full bg-pink-300 px-4 py-2 text-xs font-semibold text-white hover:brightness-95"
                                    >
                                        Complete
                                    </button>
                                </div>
                            )}

                        </div>
                    ))}
                </section>

            </div>

        </div>
    );
}

export default Orders;