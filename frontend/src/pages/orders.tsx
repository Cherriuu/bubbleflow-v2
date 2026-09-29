function Orders() {
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
                        --
                    </p>
                </div>

                <div className="rounded-3xl border border-stone-200 bg-[#FFFDF7] p-6">
                    <p className="text-sm font-medium text-stone-400">
                        Completed today
                    </p>

                    <p className="mt-2 text-3xl font-bold text-stone-800">
                        --
                    </p>
                </div>

                <div className="rounded-3xl border border-stone-200 bg-[#FFFDF7] p-6">
                    <p className="text-sm font-medium text-stone-400">
                        Drinks today
                    </p>

                    <p className="mt-2 text-3xl font-bold text-pink-300">
                        --
                    </p>
                </div>

            </div>

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
                                defaultValue=""
                                className="w-full rounded-2xl border border-stone-200 bg-white px-4 py-3 text-sm text-stone-700 outline-none focus:border-pink-300"
                            >
                                <option value="" disabled>
                                    Select a drink
                                </option>

                                <option value="thai-milk-tea">
                                    Thai Milk Tea
                                </option>

                                <option value="brown-sugar-boba">
                                    Brown Sugar Boba
                                </option>

                                <option value="coffee-milk-tea">
                                    Coffee Milk Tea
                                </option>
                            </select>
                        </div>

                        <div>
                            <label className="mb-2 block text-sm font-medium text-stone-600">
                                Size
                            </label>

                            <div className="grid grid-cols-3 gap-2">
                                <button
                                    type="button"
                                    className="rounded-full border border-stone-200 bg-white px-4 py-2 text-sm font-medium text-stone-600 hover:border-pink-300"
                                >
                                    Small
                                </button>

                                <button
                                    type="button"
                                    className="rounded-full border border-stone-200 bg-white px-4 py-2 text-sm font-medium text-stone-600 hover:border-pink-300"
                                >
                                    Medium
                                </button>

                                <button
                                    type="button"
                                    className="rounded-full border border-stone-200 bg-white px-4 py-2 text-sm font-medium text-stone-600 hover:border-pink-300"
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
                                defaultValue="regular"
                                className="w-full rounded-2xl border border-stone-200 bg-white px-4 py-3 text-sm text-stone-700 outline-none focus:border-pink-300"
                            >
                                <option value="no">No ice</option>
                                <option value="less">Less ice</option>
                                <option value="regular">Regular ice</option>
                                <option value="extra">Extra ice</option>
                            </select>
                        </div>

                        <div>
                            <label className="mb-2 block text-sm font-medium text-stone-600">
                                Extra boba
                            </label>

                            <select
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
                                className="w-full rounded-2xl border border-stone-200 bg-white px-4 py-3 text-sm text-stone-700 outline-none focus:border-pink-300"
                            />
                        </div>

                        <button
                            type="button"
                            className="mt-2 rounded-full bg-[#dcecee] px-5 py-3 text-sm font-semibold text-stone-700 transition hover:brightness-95"
                        >
                            Create order
                        </button>

                    </div>

                </section>

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

                    <div className="border-t border-stone-100 px-6 py-5">
                        <div className="grid grid-cols-[0.7fr_1.6fr_1fr_1fr] items-center">

                            <p className="text-sm font-semibold text-stone-700">
                                #104
                            </p>

                            <div>
                                <p className="font-medium text-stone-800">
                                    Thai Milk Tea
                                </p>

                                <p className="mt-1 text-xs text-stone-400">
                                    Medium · 50% sugar · Less ice
                                </p>
                            </div>

                            <div>
                                <span className="rounded-full bg-[#dcecee] px-3 py-1 text-xs font-semibold text-stone-700">
                                    Pending
                                </span>
                            </div>

                            <p className="text-sm text-stone-500">
                                2 min ago
                            </p>

                        </div>

                        <div className="mt-4 flex justify-end gap-2">
                            <button
                                type="button"
                                className="rounded-full border border-stone-200 px-4 py-2 text-xs font-semibold text-stone-500 hover:bg-stone-50"
                            >
                                Cancel
                            </button>

                            <button
                                type="button"
                                className="rounded-full bg-pink-300 px-4 py-2 text-xs font-semibold text-white hover:brightness-95"
                            >
                                Complete
                            </button>
                        </div>
                    </div>

                    <div className="border-t border-stone-100 px-6 py-5">
                        <div className="grid grid-cols-[0.7fr_1.6fr_1fr_1fr] items-center">

                            <p className="text-sm font-semibold text-stone-700">
                                #103
                            </p>

                            <div>
                                <p className="font-medium text-stone-800">
                                    Brown Sugar Boba
                                </p>

                                <p className="mt-1 text-xs text-stone-400">
                                    Large · 100% sugar · Regular ice · +1 boba
                                </p>
                            </div>

                            <div>
                                <span className="rounded-full bg-green-100 px-3 py-1 text-xs font-semibold text-green-700">
                                    Completed
                                </span>
                            </div>

                            <p className="text-sm text-stone-500">
                                8 min ago
                            </p>

                        </div>
                    </div>

                </section>

            </div>

        </div>
    );
}

export default Orders;