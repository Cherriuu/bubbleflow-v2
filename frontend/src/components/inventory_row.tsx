type InventoryRowProps = {
    name: string;
    estimatedServings: number;
    status: "available" | "low" | "out";
};

function InventoryRow({
    name,
    estimatedServings,
    status,
}: InventoryRowProps) {
    const statusStyles = {
        available: "bg-green-100 text-green-700",
        low: "bg-yellow-100 text-yellow-700",
        out: "bg-red-100 text-red-700",
    };

    const statusLabels = {
        available: "Available",
        low: "Low",
        out: "Out",
    };

    return (
        <div className="grid grid-cols-[2fr_1fr_1fr] items-center rounded-2xl px-4 py-4 hover:bg-stone-50">
            <p className="font-medium text-stone-800">
                {name}
            </p>

            <p className="text-sm text-stone-600">
                ~{estimatedServings} drinks
            </p>

            <div>
                <span
                    className={`inline-flex rounded-full px-3 py-1 text-xs font-semibold ${statusStyles[status]}`}
                >
                    {statusLabels[status]}
                </span>
            </div>
        </div>
    );
}

export default InventoryRow;