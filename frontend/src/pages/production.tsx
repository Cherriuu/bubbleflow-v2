 import { useEffect, useState } from "react";


type InventoryItem = {
    id: number;
    name: string;
    base_unit: string;
    inventory: string;
    estimated_servings: number;
    status: "available" | "low" | "out";
};


type Recommendation = {
    id: number;
    name: string;
    base_unit: string;
    recommended_quantity: number | string;
};


type PreparedItem = {
    id: number;
    name: string;
    base_unit: string;
    default_batch_quantity: string;
    batch_label: string;
};


function Production() {
    const [inventory, setInventory] = useState<InventoryItem[]>([]);
    const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
    const [preparedItems, setPreparedItems] = useState<PreparedItem[]>([]);


    useEffect(() => {
        async function getInventory() {
            const response = await fetch(
                "http://localhost:8000/api/inventory/"
            );

            const data = await response.json();

            setInventory(data);
        }


        async function getRecommendations() {
            const response = await fetch(
                "http://localhost:8000/api/recommendations/"
            );

            const data = await response.json();

            setRecommendations(data);
        }


        async function getPreparedItems() {
            const response = await fetch(
                "http://localhost:8000/api/prepared-items/"
            );

            const data = await response.json();

            setPreparedItems(data);
        }


        getInventory();
        getRecommendations();
        getPreparedItems();
    }, []);


    const itemsToPrepare = recommendations.filter(
        (recommendation) =>
            Number(recommendation.recommended_quantity) > 0
    );


    const lowStockCount = inventory.filter(
        (item) =>
            item.status === "low" ||
            item.status === "out"
    ).length;


    const availableCount = inventory.filter(
        (item) =>
            item.status === "available"
    ).length;


    const productionQueue = [...itemsToPrepare].sort(
        (a, b) =>
            Number(b.recommended_quantity) -
            Number(a.recommended_quantity)
    );


    function getBatchSuggestion(
        recommendation: Recommendation
    ) {
        const preparedItem = preparedItems.find(
            (item) =>
                item.id === recommendation.id
        );

        if (!preparedItem) {
            return "";
        }

        const recommendedQuantity = Number(
            recommendation.recommended_quantity
        );

        const fullBatchQuantity = Number(
            preparedItem.default_batch_quantity
        );

        if (recommendedQuantity <= 0) {
            return "";
        }

        if (
            recommendedQuantity <=
            fullBatchQuantity / 2
        ) {
            return "½ batch suggested";
        }

        return "1 batch suggested";
    }


    return (
        <div className="w-full px-8 py-8">

            <div className="mb-10 text-center">
                <p className="mb-2 text-4xl font-semibold text-pink-300">
                    Production
                </p>

                <h1 className="text-2xl font-bold tracking-tight text-stone-800">
                    What should we make next?
                </h1>

                <p className="mt-3 text-base text-stone-500">
                    Use recent demand, current inventory, and batches already
                    in production to help plan what should be prepared next.
                </p>
            </div>


            <div className="mb-8 grid gap-4 sm:grid-cols-3">

                <div className="rounded-3xl border border-stone-200 bg-[#FFFDF7] p-6">
                    <p className="text-sm font-medium text-stone-400">
                        Items to prepare
                    </p>

                    <p className="mt-2 text-3xl font-bold text-pink-300">
                        {itemsToPrepare.length}
                    </p>

                    <p className="mt-2 text-xs text-stone-400">
                        Currently recommended
                    </p>
                </div>


                <div className="rounded-3xl border border-stone-200 bg-[#FFFDF7] p-6">
                    <p className="text-sm font-medium text-stone-400">
                        Low stock
                    </p>

                    <p className="mt-2 text-3xl font-bold text-stone-800">
                        {lowStockCount}
                    </p>

                    <p className="mt-2 text-xs text-stone-400">
                        Low or out of stock
                    </p>
                </div>


                <div className="rounded-3xl border border-stone-200 bg-[#FFFDF7] p-6">
                    <p className="text-sm font-medium text-stone-400">
                        Available
                    </p>

                    <p className="mt-2 text-3xl font-bold text-stone-800">
                        {availableCount}
                    </p>

                    <p className="mt-2 text-xs text-stone-400">
                        Prepared items at healthy stock
                    </p>
                </div>

            </div>


            <section className="mb-6 overflow-hidden rounded-3xl border border-stone-200 bg-[#FFFDF7]">

                <div className="border-b border-stone-200 px-6 py-5">
                    <h2 className="text-lg font-semibold text-stone-800">
                        Production recommendations
                    </h2>

                    <p className="mt-1 text-sm text-stone-400">
                        Suggested preparation based on recent usage,
                        ready inventory, and inventory already being made.
                    </p>
                </div>


                <div className="grid grid-cols-[1.5fr_1fr_1fr_1.2fr] px-6 py-3 text-xs font-semibold uppercase tracking-wide text-stone-400">
                    <span>Item</span>
                    <span>Available</span>
                    <span>Suggested amount</span>
                    <span>Recommendation</span>
                </div>


                {recommendations.map((recommendation) => {
                    const inventoryItem = inventory.find(
                        (item) =>
                            item.id === recommendation.id
                    );

                    const recommendedQuantity = Number(
                        recommendation.recommended_quantity
                    );

                    const batchSuggestion = getBatchSuggestion(
                        recommendation
                    );

                    return (
                        <div
                            key={recommendation.id}
                            className="border-t border-stone-100 px-6 py-5"
                        >
                            <div className="grid grid-cols-[1.5fr_1fr_1fr_1.2fr] items-center">

                                <div>
                                    <p className="font-medium text-stone-800">
                                        {recommendation.name}
                                    </p>

                                    <p className="mt-1 text-xs text-stone-400">
                                        Prepared inventory
                                    </p>
                                </div>


                                <div>
                                    <p className="text-sm text-stone-600">
                                        ~{inventoryItem?.estimated_servings ?? 0} servings
                                    </p>

                                    <p className="mt-1 text-xs text-stone-400">
                                        {Number(
                                            inventoryItem?.inventory ?? 0
                                        ).toFixed(0)}{" "}
                                        {recommendation.base_unit}
                                    </p>
                                </div>


                                <p className="text-sm text-stone-600">
                                    {recommendedQuantity > 0
                                        ? `${Math.ceil(
                                              recommendedQuantity
                                          )} ${recommendation.base_unit}`
                                        : "—"}
                                </p>


                                <div>
                                    {recommendedQuantity > 0 ? (
                                        <>
                                            <span className="rounded-full bg-pink-100 px-3 py-1 text-xs font-semibold text-pink-500">
                                                Prepare more
                                            </span>

                                            <p className="mt-2 text-xs text-stone-400">
                                                {batchSuggestion}
                                            </p>
                                        </>
                                    ) : (
                                        <span className="rounded-full bg-green-100 px-3 py-1 text-xs font-semibold text-green-700">
                                            Enough for now
                                        </span>
                                    )}
                                </div>

                            </div>
                        </div>
                    );
                })}


                {recommendations.length === 0 && (
                    <p className="border-t border-stone-100 px-6 py-6 text-sm text-stone-400">
                        No production recommendations available.
                    </p>
                )}

            </section>


            <div className="grid gap-6 lg:grid-cols-2">

                <section className="rounded-3xl border border-stone-200 bg-[#FFFDF7] p-6">

                    <h2 className="text-lg font-semibold text-stone-800">
                        How recommendations work
                    </h2>

                    <p className="mt-2 text-sm leading-6 text-stone-500">
                        BubbleFlow looks at recent order consumption to
                        estimate short-term demand for each prepared item.
                        It compares that demand with inventory that is ready
                        to use and inventory already being prepared.
                    </p>


                    <div className="mt-6 flex flex-col gap-4">

                        <div className="rounded-2xl bg-stone-50 px-4 py-4">
                            <p className="text-xs font-semibold uppercase tracking-wide text-stone-400">
                                Demand
                            </p>

                            <p className="mt-1 text-sm font-medium text-stone-700">
                                Estimated from recent order consumption
                            </p>
                        </div>


                        <div className="rounded-2xl bg-stone-50 px-4 py-4">
                            <p className="text-xs font-semibold uppercase tracking-wide text-stone-400">
                                Current supply
                            </p>

                            <p className="mt-1 text-sm font-medium text-stone-700">
                                Ready inventory is counted before recommending more
                            </p>
                        </div>


                        <div className="rounded-2xl bg-stone-50 px-4 py-4">
                            <p className="text-xs font-semibold uppercase tracking-wide text-stone-400">
                                Incoming supply
                            </p>

                            <p className="mt-1 text-sm font-medium text-stone-700">
                                Preparing and cooling batches also reduce the recommendation
                            </p>
                        </div>

                    </div>

                </section>


                <section className="rounded-3xl border border-stone-200 bg-[#FFFDF7] p-6">

                    <div className="flex items-center justify-between">
                        <div>
                            <h2 className="text-lg font-semibold text-stone-800">
                                Production queue
                            </h2>

                            <p className="mt-1 text-sm text-stone-400">
                                Items currently recommended for additional production.
                            </p>
                        </div>

                        <a
                            href="/batches"
                            className="text-sm font-semibold text-pink-400 hover:text-pink-500"
                        >
                            View batches
                        </a>
                    </div>


                    <div className="mt-6 flex flex-col gap-3">

                        {productionQueue.map(
                            (recommendation) => {
                                const inventoryItem = inventory.find(
                                    (item) =>
                                        item.id === recommendation.id
                                );

                                const batchSuggestion =
                                    getBatchSuggestion(
                                        recommendation
                                    );

                                return (
                                    <div
                                        key={recommendation.id}
                                        className="flex items-center justify-between rounded-2xl border border-pink-100 bg-pink-50 px-4 py-4"
                                    >
                                        <div>
                                            <p className="font-medium text-stone-800">
                                                {recommendation.name}
                                            </p>

                                            <p className="mt-1 text-xs text-stone-500">
                                                {inventoryItem?.status === "out"
                                                    ? "Currently out of prepared inventory."
                                                    : inventoryItem?.status === "low"
                                                    ? "Inventory is currently low."
                                                    : "Forecasted demand exceeds current and incoming supply."}
                                            </p>

                                            <p className="mt-1 text-xs font-medium text-pink-400">
                                                {Math.ceil(
                                                    Number(
                                                        recommendation.recommended_quantity
                                                    )
                                                )}{" "}
                                                {recommendation.base_unit} needed
                                            </p>

                                            <p className="mt-1 text-xs text-stone-400">
                                                {batchSuggestion}
                                            </p>
                                        </div>

                                        <span className="rounded-full bg-pink-300 px-3 py-1 text-xs font-semibold text-white">
                                            Recommended
                                        </span>
                                    </div>
                                );
                            }
                        )}


                        {productionQueue.length === 0 && (
                            <div className="rounded-2xl border border-stone-200 px-4 py-4">
                                <p className="font-medium text-stone-800">
                                    Production looks good
                                </p>

                                <p className="mt-1 text-xs text-stone-500">
                                    Current and incoming inventory cover
                                    forecasted demand.
                                </p>
                            </div>
                        )}

                    </div>

                </section>

            </div>

        </div>
    );
}


export default Production;