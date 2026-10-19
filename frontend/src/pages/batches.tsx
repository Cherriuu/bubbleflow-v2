import { useEffect, useState } from "react";
import { apiFetch } from "../api/client";


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
    is_active: boolean;
    base_unit: string;
    default_batch_quantity: string;
    batch_label: string;
};


{/* One change to a batch's inventory, from /api/batches/<id>/events/ */}
type InventoryEvent = {
    id: number;
    event_type: "batch_created" | "order_consumption" | "waste" | "correction" | "expiry";
    quantity_delta: string;
    reason: string;
    created_at: string;
    order_id: number | null;
};


type BatchHistory = {
    balance: string;
    status: string;
    events: InventoryEvent[];
};


type AdjustmentKind = "waste" | "correction";


type StorageLocation = {
    id: number;
    name: string;
};


function Batches() {
    const [batches, setBatches] = useState<Batch[]>([]);
    const [preparedItems, setPreparedItems] = useState<PreparedItem[]>([]);
    const [storageLocations, setStorageLocations] = useState<StorageLocation[]>([]);

    const [selectedPreparedItem, setSelectedPreparedItem] = useState("");
    const [batchFraction, setBatchFraction] = useState("");
    const [selectedStorageLocation, setSelectedStorageLocation] = useState("");

    const [isSubmitting, setIsSubmitting] = useState(false);
    const [message, setMessage] = useState("");

    {/* The waste or correction form that's open, if any */}
    const [adjustingBatchId, setAdjustingBatchId] = useState<number | null>(null);
    const [adjustmentKind, setAdjustmentKind] = useState<AdjustmentKind>("waste");
    const [adjustmentAmount, setAdjustmentAmount] = useState("");
    const [adjustmentReason, setAdjustmentReason] = useState("");
    const [adjustmentMessage, setAdjustmentMessage] = useState("");
    const [isAdjusting, setIsAdjusting] = useState(false);

    {/* The batch whose history is expanded, if any */}
    const [historyBatchId, setHistoryBatchId] = useState<number | null>(null);
    const [history, setHistory] = useState<BatchHistory | null>(null);


    async function getBatches() {
        const response = await apiFetch(
            "/api/batches/"
        );

        const data = await response.json();
        setBatches(data);
    }


    useEffect(() => {
        async function getPreparedItems() {
            const response = await apiFetch(
                "/api/prepared-items/?include_inactive=true"
            );

            const data = await response.json();
            setPreparedItems(data);
        }


        async function getStorageLocations() {
            const response = await apiFetch(
                "/api/storage-locations/"
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
            const response = await apiFetch(
                "/api/batches/create/",
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

    async function markBatchAsReady(batchId: number) {
        try {
            const response = await apiFetch(
                `/api/batches/${batchId}/ready/`,
                {
                    method: "POST",
                }
            );

            if (!response.ok) {
                throw new Error("Could not mark batch as ready.");
            }

            await getBatches();
        } catch (error) {
            console.error(error);
            setMessage("Something went wrong while marking the batch as ready.");
        }
    }


    {/* Get a batch's inventory events and current balance */}
    async function getHistory(batchId: number) {
        const response = await apiFetch(
            `/api/batches/${batchId}/events/`
        );

        const data = await response.json();
        setHistory(data);
    }


    {/* Show a batch's history, or hide it if it's already open */}
    async function toggleHistory(batchId: number) {
        if (historyBatchId === batchId) {
            setHistoryBatchId(null);
            setHistory(null);
            return;
        }

        setHistoryBatchId(batchId);
        setHistory(null);

        try {
            await getHistory(batchId);
        } catch (error) {
            console.error(error);
        }
    }


    {/* Open the waste or correction form for a batch */}
    function openAdjustment(batchId: number, kind: AdjustmentKind) {
        setAdjustingBatchId(batchId);
        setAdjustmentKind(kind);
        setAdjustmentAmount("");
        setAdjustmentReason("");
        setAdjustmentMessage("");
    }


    {/* Send the waste or correction to the API, then refresh the batches */}
    async function submitAdjustment(batchId: number) {
        if (!adjustmentAmount || !adjustmentReason.trim()) {
            setAdjustmentMessage("Please enter an amount and a reason.");
            return;
        }

        setIsAdjusting(true);
        setAdjustmentMessage("");

        try {
            const response = await apiFetch(
                `/api/batches/${batchId}/${adjustmentKind}/`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type": "application/json",
                    },

                    body: JSON.stringify({
                        quantity: adjustmentAmount,
                        reason: adjustmentReason.trim(),
                    }),
                }
            );

            const data = await response.json();

            if (!response.ok) {
                // Our own errors come as {"error": ...}, field errors as {"quantity": ["..."]}
                const fieldError = Object.values(data).flat()[0];

                setAdjustmentMessage(
                    data.error ||
                    (typeof fieldError === "string" ? fieldError : "") ||
                    "The change could not be saved."
                );
                return;
            }

            setAdjustingBatchId(null);

            await getBatches();

            if (historyBatchId === batchId) {
                await getHistory(batchId);
            }
        } catch (error) {
            console.error(error);
            setAdjustmentMessage("Something went wrong while saving the change.");
        } finally {
            setIsAdjusting(false);
        }
    }


    {/* Readable names for each kind of inventory event */}
    function formatEventType(eventType: InventoryEvent["event_type"]) {
        const labels = {
            batch_created: "Batch created",
            order_consumption: "Order consumption",
            waste: "Waste",
            correction: "Correction",
            expiry: "Expired",
        };

        return labels[eventType] ?? eventType;
    }


    {/* Show an amount with its sign and unit, like +4,000 ml or −500 ml */}
    function formatSignedAmount(quantity: string, unit: string) {
        const amount = Number(quantity);
        const sign = amount < 0 ? "−" : "+";

        return `${sign}${Math.abs(amount).toLocaleString()} ${unit}`;
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

                                {/* Hidden items keep their old batches but can't start new ones */}
                                {preparedItems.filter((item) => item.is_active).map((item) => (
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
                                        
                                        {/* Add a "Ready" button for batches that are preparing or cooling */}

                                        <div className="flex justify-left gap-2">
                                        { (batch.status === "preparing" || batch.status === "cooling") && (
                                            <button onClick={() => markBatchAsReady(batch.id)} className="rounded-full bg-pink-300 px-4 py-2 text-xs font-semibold text-white hover:brightness-95">Ready</button>
                                        ) }

                                        {/* Waste and corrections only make sense while there's stock left */}
                                        { Number(batch.balance) > 0 && (
                                            <>
                                                <button type="button" onClick={() => openAdjustment(batch.id, "waste")} className="rounded-full bg-[#dcecee] px-4 py-2 text-xs font-semibold text-stone-700 hover:brightness-95">Record waste</button>
                                                <button type="button" onClick={() => openAdjustment(batch.id, "correction")} className="rounded-full bg-[#dcecee] px-4 py-2 text-xs font-semibold text-stone-700 hover:brightness-95">Correct</button>
                                            </>
                                        ) }

                                        <button type="button" onClick={() => toggleHistory(batch.id)} className="rounded-full bg-[#dcecee] px-4 py-2 text-xs font-semibold text-stone-700 hover:brightness-95">
                                            {historyBatchId === batch.id ? "Hide history" : "History"}
                                        </button>
                                        </div>

                                    </div>


                                    {/* Inline waste or correction form */}

                                    {adjustingBatchId === batch.id && (
                                        <div className="mt-4 flex flex-col gap-3 rounded-2xl bg-stone-50 px-4 py-4">
                                            <p className="text-xs font-semibold uppercase tracking-wide text-stone-400">
                                                {adjustmentKind === "waste" ? "Record waste" : "Correct inventory"}
                                            </p>

                                            <div className="grid gap-3 sm:grid-cols-[1fr_2fr]">
                                                <div>
                                                    <label className="mb-2 block text-sm font-medium text-stone-600">
                                                        Amount ({item?.base_unit ?? "units"})
                                                    </label>

                                                    <input
                                                        type="number"
                                                        step="any"
                                                        min={adjustmentKind === "waste" ? "0" : undefined}
                                                        value={adjustmentAmount}
                                                        onChange={(event) => setAdjustmentAmount(event.target.value)}
                                                        placeholder={adjustmentKind === "waste" ? "500" : "Use − to remove, e.g. -250"}
                                                        className="w-full rounded-2xl border border-stone-200 bg-white px-4 py-3 text-sm text-stone-700 outline-none focus:border-pink-300"
                                                    />
                                                </div>

                                                <div>
                                                    <label className="mb-2 block text-sm font-medium text-stone-600">
                                                        Reason
                                                    </label>

                                                    <input
                                                        type="text"
                                                        required
                                                        value={adjustmentReason}
                                                        onChange={(event) => setAdjustmentReason(event.target.value)}
                                                        placeholder={adjustmentKind === "waste" ? "Spilled during prep" : "Recounted the pitcher"}
                                                        className="w-full rounded-2xl border border-stone-200 bg-white px-4 py-3 text-sm text-stone-700 outline-none focus:border-pink-300"
                                                    />
                                                </div>
                                            </div>

                                            {adjustmentMessage && (
                                                <p className="text-sm text-stone-500">
                                                    {adjustmentMessage}
                                                </p>
                                            )}

                                            <div className="flex gap-2">
                                                <button
                                                    type="button"
                                                    onClick={() => submitAdjustment(batch.id)}
                                                    disabled={isAdjusting}
                                                    className="rounded-full bg-pink-300 px-4 py-2 text-xs font-semibold text-white hover:brightness-95 disabled:cursor-not-allowed disabled:opacity-50"
                                                >
                                                    {isAdjusting ? "Saving..." : "Save"}
                                                </button>

                                                <button
                                                    type="button"
                                                    onClick={() => setAdjustingBatchId(null)}
                                                    className="rounded-full bg-[#dcecee] px-4 py-2 text-xs font-semibold text-stone-700 hover:brightness-95"
                                                >
                                                    Cancel
                                                </button>
                                            </div>
                                        </div>
                                    )}


                                    {/* Batch history, newest first */}

                                    {historyBatchId === batch.id && (
                                        <div className="mt-4 rounded-2xl bg-stone-50 px-4 py-4">
                                            {history === null ? (
                                                <p className="text-sm text-stone-400">
                                                    Loading history...
                                                </p>
                                            ) : (
                                                <>
                                                    <p className="text-xs font-semibold uppercase tracking-wide text-stone-400">
                                                        Current balance
                                                    </p>

                                                    <p className="mt-1 text-sm font-medium text-stone-700">
                                                        {Number(history.balance).toLocaleString()} {item?.base_unit}
                                                    </p>

                                                    <div className="mt-4 flex flex-col">
                                                        {history.events.map((event) => (
                                                            <div
                                                                key={event.id}
                                                                className="grid grid-cols-[1.2fr_1fr_2fr_1fr] items-center gap-2 border-t border-stone-200 py-3"
                                                            >
                                                                <div>
                                                                    <p className="text-sm font-medium text-stone-800">
                                                                        {formatEventType(event.event_type)}
                                                                    </p>

                                                                    {event.order_id !== null && (
                                                                        <p className="mt-1 text-xs text-stone-400">
                                                                            Order #{event.order_id}
                                                                        </p>
                                                                    )}
                                                                </div>

                                                                <p className={`text-sm font-medium ${Number(event.quantity_delta) < 0 ? "text-pink-500" : "text-green-700"}`}>
                                                                    {formatSignedAmount(event.quantity_delta, item?.base_unit ?? "")}
                                                                </p>

                                                                <p className="text-sm text-stone-500">
                                                                    {event.reason || "—"}
                                                                </p>

                                                                <p className="text-xs text-stone-400">
                                                                    {new Date(event.created_at).toLocaleString()}
                                                                </p>
                                                            </div>
                                                        ))}
                                                    </div>
                                                </>
                                            )}
                                        </div>
                                    )}
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