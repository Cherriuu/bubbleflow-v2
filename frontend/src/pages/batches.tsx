import { useEffect, useState } from "react";


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


type StorageLocation = {
    id: number;
    name: string;
};


function Batches() {
    const [batches, setBatches] = useState<Batch[]>([]);
    const [preparedItems, setPreparedItems] = useState<PreparedItem[]>([]);
    const [storageLocations, setStorageLocations] =
        useState<StorageLocation[]>([]);

    const [selectedPreparedItem, setSelectedPreparedItem] = useState("");
    const [batchFraction, setBatchFraction] = useState("");
    const [selectedStorageLocation, setSelectedStorageLocation] = useState("");

    const [isSubmitting, setIsSubmitting] = useState(false);
    const [message, setMessage] = useState("");


    async function getBatches() {
        const response = await fetch(
            "http://localhost:8000/api/batches/"
        );

        const data = await response.json();
        setBatches(data);
    }


    useEffect(() => {
        async function getPreparedItems() {
            const response = await fetch(
                "http://localhost:8000/api/prepared-items/"
            );

            const data = await response.json();
            setPreparedItems(data);
        }


        async function getStorageLocations() {
            const response = await fetch(
                "http://localhost:8000/api/storage-locations/"
            );

            const data = await response.json();
            setStorageLocations(data);
        }


        getBatches();
        getPreparedItems();
        getStorageLocations();
    }, []);


    async function handleStartBatch() {
        if (
            !selectedPreparedItem ||
            !batchFraction ||
            !selectedStorageLocation
        ) {
            setMessage("Please complete all fields.");
            return;
        }

        setIsSubmitting(true);
        setMessage("");

        try {
            const response = await fetch(
                "http://localhost:8000/api/batches/create/",
                {
                    method: "POST",

                    headers: {
                        "Content-Type": "application/json",
                    },

                    body: JSON.stringify({
                        prepared_item_id: Number(selectedPreparedItem),
                        storage_location_id: Number(selectedStorageLocation),
                        batch_fraction: batchFraction,
                        started_at: new Date().toISOString(),
                    }),
                }
            );

            if (!response.ok) {
                throw new Error("Could not start batch.");
            }

            setSelectedPreparedItem("");
            setBatchFraction("");
            setSelectedStorageLocation("");

            setMessage("Batch started!");

            await getBatches();
        } catch (error) {
            console.error(error);
            setMessage("Something went wrong while starting the batch.");
        } finally {
            setIsSubmitting(false);
        }
    }


    function getPreparedItem(batch: Batch) {
        return preparedItems.find(
            (item) => item.id === batch.prepared_item
        );
    }


    function getStorageLocation(batch: Batch) {
        return storageLocations.find(
            (location) => location.id === batch.storage_location
        );
    }


    function getBatchAmount(batch: Batch) {
        const item = getPreparedItem(batch);

        if (!item) {
            return batch.initial_quantity;
        }

        const initialQuantity = Number(batch.initial_quantity);
        const standardQuantity = Number(item.default_batch_quantity);

        if (standardQuantity === 0) {
            return batch.initial_quantity;
        }

        const fraction = initialQuantity / standardQuantity;

        if (fraction === 0.25) {
            return `¼ ${item.batch_label}`;
        }

        if (fraction === 0.5) {
            return `½ ${item.batch_label}`;
        }

        if (fraction === 1) {
            return `1 ${item.batch_label}`;
        }

        return `${fraction.toFixed(2)} ${item.batch_label}`;
    }


    function getTiming(batch: Batch) {
        const now = new Date();

        if (
            (batch.status === "preparing" ||
                batch.status === "cooling") &&
            batch.ready_at
        ) {
            const readyAt = new Date(batch.ready_at);

            const minutes = Math.ceil(
                (readyAt.getTime() - now.getTime()) / 60000
            );

            if (minutes <= 0) {
                return "Ready now";
            }

            return `Ready in ~${minutes} min`;
        }


        if (batch.status === "ready") {
            const expiresAt = new Date(batch.expires_at);

            const hours = Math.ceil(
                (expiresAt.getTime() - now.getTime()) / 3600000
            );

            if (hours <= 0) {
                return "Expired";
            }

            if (hours < 24) {
                return `Expires in ~${hours} hr`;
            }

            const days = Math.ceil(hours / 24);

            return `Expires in ${days} day${days === 1 ? "" : "s"}`;
        }

        return "—";
    }


    function getStatusStyle(status: string) {
        if (status === "ready") {
            return "bg-green-100 text-green-700";
        }

        if (status === "preparing" || status === "cooling") {
            return "bg-[#dcecee] text-stone-700";
        }

        if (status === "expired" || status === "discarded") {
            return "bg-red-100 text-red-700";
        }

        return "bg-stone-100 text-stone-600";
    }


    function formatStatus(status: string) {
        return status
            .replaceAll("_", " ")
            .replace(/\b\w/g, (letter) => letter.toUpperCase());
    }


    const activeBatches = batches.filter(
        (batch) =>
            batch.status === "preparing" ||
            batch.status === "cooling" ||
            batch.status === "ready"
    );


    const preparingCount = batches.filter(
        (batch) =>
            batch.status === "preparing" ||
            batch.status === "cooling"
    ).length;


    const readyCount = batches.filter(
        (batch) => batch.status === "ready"
    ).length;


    const expiringSoonCount = batches.filter((batch) => {
        if (batch.status !== "ready") {
            return false;
        }

        const expiresAt = new Date(batch.expires_at).getTime();
        const now = new Date().getTime();

        const hoursRemaining =
            (expiresAt - now) / 3600000;

        return hoursRemaining > 0 && hoursRemaining <= 24;
    }).length;


    const selectedItem = preparedItems.find(
        (item) => item.id === Number(selectedPreparedItem)
    );


    return (
        <div className="w-full px-8 py-8">

            <div className="mb-10 text-center">
                <p className="mb-2 text-4xl font-semibold text-pink-300">
                    Batches
                </p>

                <h1 className="text-2xl font-bold tracking-tight text-stone-800">
                    What's being prepared?
                </h1>

                <p className="mt-3 text-base text-stone-500">
                    Start new batches and keep track of what's preparing,
                    ready, or nearing expiration.
                </p>
            </div>


            <div className="mb-8 grid gap-4 sm:grid-cols-3">

                <div className="rounded-3xl border border-stone-200 bg-[#FFFDF7] p-6">
                    <p className="text-sm font-medium text-stone-400">
                        Preparing
                    </p>

                    <p className="mt-2 text-3xl font-bold text-stone-800">
                        {preparingCount}
                    </p>
                </div>


                <div className="rounded-3xl border border-stone-200 bg-[#FFFDF7] p-6">
                    <p className="text-sm font-medium text-stone-400">
                        Ready
                    </p>

                    <p className="mt-2 text-3xl font-bold text-stone-800">
                        {readyCount}
                    </p>
                </div>


                <div className="rounded-3xl border border-stone-200 bg-[#FFFDF7] p-6">
                    <p className="text-sm font-medium text-stone-400">
                        Expiring soon
                    </p>

                    <p className="mt-2 text-3xl font-bold text-pink-300">
                        {expiringSoonCount}
                    </p>
                </div>

            </div>


            <div className="grid gap-6 xl:grid-cols-[1fr_2fr]">

                <section className="rounded-3xl border border-stone-200 bg-[#FFFDF7] p-6">

                    <div className="mb-6">
                        <h2 className="text-lg font-semibold text-stone-800">
                            Start a batch
                        </h2>

                        <p className="mt-1 text-sm text-stone-400">
                            Record something that's being prepared.
                        </p>
                    </div>


                    <div className="flex flex-col gap-5">

                        <div>
                            <label className="mb-2 block text-sm font-medium text-stone-600">
                                Prepared item
                            </label>

                            <select
                                className="w-full rounded-2xl border border-stone-200 bg-white px-4 py-3 text-sm text-stone-700 outline-none focus:border-pink-300"
                                value={selectedPreparedItem}
                                onChange={(event) =>
                                    setSelectedPreparedItem(
                                        event.target.value
                                    )
                                }
                            >
                                <option value="" disabled>
                                    Select an item
                                </option>

                                {preparedItems.map((item) => (
                                    <option
                                        key={item.id}
                                        value={item.id}
                                    >
                                        {item.name}
                                    </option>
                                ))}
                            </select>
                        </div>


                        <div>
                            <label className="mb-2 block text-sm font-medium text-stone-600">
                                Batch amount
                            </label>

                            <select
                                className="w-full rounded-2xl border border-stone-200 bg-white px-4 py-3 text-sm text-stone-700 outline-none focus:border-pink-300"
                                value={batchFraction}
                                onChange={(event) =>
                                    setBatchFraction(
                                        event.target.value
                                    )
                                }
                            >
                                <option value="" disabled>
                                    Select an amount
                                </option>

                                <option value="0.25">
                                    ¼ {selectedItem?.batch_label || "batch"}
                                </option>

                                <option value="0.5">
                                    ½ {selectedItem?.batch_label || "batch"}
                                </option>

                                <option value="1">
                                    1 {selectedItem?.batch_label || "batch"}
                                </option>
                            </select>
                        </div>


                        <div>
                            <label className="mb-2 block text-sm font-medium text-stone-600">
                                Storage location
                            </label>

                            <select
                                className="w-full rounded-2xl border border-stone-200 bg-white px-4 py-3 text-sm text-stone-700 outline-none focus:border-pink-300"
                                value={selectedStorageLocation}
                                onChange={(event) =>
                                    setSelectedStorageLocation(
                                        event.target.value
                                    )
                                }
                            >
                                <option value="" disabled>
                                    Select a location
                                </option>

                                {storageLocations.map((location) => (
                                    <option
                                        key={location.id}
                                        value={location.id}
                                    >
                                        {location.name}
                                    </option>
                                ))}
                            </select>
                        </div>


                        {message && (
                            <p className="text-sm text-stone-500">
                                {message}
                            </p>
                        )}


                        <button
                            type="button"
                            onClick={handleStartBatch}
                            disabled={isSubmitting}
                            className="mt-2 rounded-full bg-[#dcecee] px-5 py-3 text-sm font-semibold text-stone-700 transition hover:brightness-95 disabled:cursor-not-allowed disabled:opacity-50"
                        >
                            {isSubmitting
                                ? "Starting..."
                                : "Start batch"}
                        </button>

                    </div>

                </section>


                <section className="overflow-hidden rounded-3xl border border-stone-200 bg-[#FFFDF7]">

                    <div className="border-b border-stone-200 px-6 py-5">
                        <h2 className="text-lg font-semibold text-stone-800">
                            Active batches
                        </h2>

                        <p className="mt-1 text-sm text-stone-400">
                            Batches currently being prepared or available
                            for orders.
                        </p>
                    </div>


                    <div className="grid grid-cols-[1.5fr_1fr_1fr_1fr] px-6 py-3 text-xs font-semibold uppercase tracking-wide text-stone-400">
                        <span>Item</span>
                        <span>Amount</span>
                        <span>Status</span>
                        <span>Timing</span>
                    </div>


                    {activeBatches.length === 0 ? (
                        <div className="border-t border-stone-100 px-6 py-10 text-center">
                            <p className="text-sm font-medium text-stone-500">
                                No active batches yet.
                            </p>

                            <p className="mt-1 text-xs text-stone-400">
                                Start a batch to see it here.
                            </p>
                        </div>
                    ) : (
                        activeBatches.map((batch) => {
                            const item = getPreparedItem(batch);
                            const location = getStorageLocation(batch);

                            return (
                                <div
                                    key={batch.id}
                                    className="border-t border-stone-100 px-6 py-5"
                                >
                                    <div className="grid grid-cols-[1.5fr_1fr_1fr_1fr] items-center">

                                        <div>
                                            <p className="font-medium text-stone-800">
                                                {item?.name || "Unknown item"}
                                            </p>

                                            <p className="mt-1 text-xs text-stone-400">
                                                {location?.name ||
                                                    "Unknown location"}
                                            </p>
                                        </div>


                                        <p className="text-sm text-stone-600">
                                            {getBatchAmount(batch)}
                                        </p>


                                        <div>
                                            <span
                                                className={`rounded-full px-3 py-1 text-xs font-semibold ${getStatusStyle(
                                                    batch.status
                                                )}`}
                                            >
                                                {formatStatus(batch.status)}
                                            </span>
                                        </div>


                                        <p className="text-sm text-stone-500">
                                            {getTiming(batch)}
                                        </p>

                                    </div>
                                </div>
                            );
                        })
                    )}

                </section>

            </div>

        </div>
    );
}


export default Batches;