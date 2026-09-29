// typescript interface for inventory row props
interface InventoryRowProps {
    name: string;
    quantity: number;
    status: string;
    unit: string;
}

function InventoryRow({ name, quantity, status, unit }: InventoryRowProps) {
    return (
        <div className="grid grid-cols-[2fr_1fr_1fr] items-center rounded-2xl bg-[#dcecee] px-4 py-3">
            <p className="text-sm font-medium text-stone-800">
                {name}
            </p>

            <p className="text-center text-sm text-stone-400">
                {quantity} {unit}
            </p>

            <p className="text-right text-sm text-stone-400">
                {status}
            </p>
        </div>
    )
}

export default InventoryRow