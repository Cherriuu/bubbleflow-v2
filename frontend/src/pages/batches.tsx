function Batches() {
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
                        --
                    </p>
                </div>

                <div className="rounded-3xl border border-stone-200 bg-[#FFFDF7] p-6">
                    <p className="text-sm font-medium text-stone-400">
                        Ready
                    </p>

                    <p className="mt-2 text-3xl font-bold text-stone-800">
                        --
                    </p>
                </div>

                <div className="rounded-3xl border border-stone-200 bg-[#FFFDF7] p-6">
                    <p className="text-sm font-medium text-stone-400">
                        Expiring soon
                    </p>

                    <p className="mt-2 text-3xl font-bold text-pink-300">
                        --
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
                                defaultValue=""
                            >
                                <option value="" disabled>
                                    Select an item
                                </option>

                                <option value="boba">
                                    Boba
                                </option>

                                <option value="thai-tea">
                                    Thai Tea
                                </option>

                                <option value="coffee">
                                    Coffee
                                </option>
                            </select>
                        </div>

                        <div>
                            <label className="mb-2 block text-sm font-medium text-stone-600">
                                Batch amount
                            </label>

                            <select
                                className="w-full rounded-2xl border border-stone-200 bg-white px-4 py-3 text-sm text-stone-700 outline-none focus:border-pink-300"
                                defaultValue=""
                            >
                                <option value="" disabled>
                                    Select an amount
                                </option>

                                <option value="0.25">
                                    ¼ batch
                                </option>

                                <option value="0.5">
                                    ½ batch
                                </option>

                                <option value="1">
                                    1 batch
                                </option>
                            </select>
                        </div>

                        <div>
                            <label className="mb-2 block text-sm font-medium text-stone-600">
                                Storage location
                            </label>

                            <select
                                className="w-full rounded-2xl border border-stone-200 bg-white px-4 py-3 text-sm text-stone-700 outline-none focus:border-pink-300"
                                defaultValue=""
                            >
                                <option value="" disabled>
                                    Select a location
                                </option>

                                <option value="prep">
                                    Prep Station
                                </option>

                                <option value="refrigerator">
                                    Refrigerator
                                </option>
                            </select>
                        </div>

                        <button
                            type="button"
                            className="mt-2 rounded-full bg-[#dcecee] px-5 py-3 text-sm font-semibold text-stone-700 transition hover:brightness-95"
                        >
                            Start batch
                        </button>

                    </div>
                </section>

                <section className="overflow-hidden rounded-3xl border border-stone-200 bg-[#FFFDF7]">

                    <div className="border-b border-stone-200 px-6 py-5">
                        <h2 className="text-lg font-semibold text-stone-800">
                            Active batches
                        </h2>

                        <p className="mt-1 text-sm text-stone-400">
                            Batches currently being prepared or available for orders.
                        </p>
                    </div>

                    <div className="grid grid-cols-[1.5fr_1fr_1fr_1fr] px-6 py-3 text-xs font-semibold uppercase tracking-wide text-stone-400">
                        <span>Item</span>
                        <span>Amount</span>
                        <span>Status</span>
                        <span>Timing</span>
                    </div>

                    <div className="border-t border-stone-100 px-6 py-5">
                        <div className="grid grid-cols-[1.5fr_1fr_1fr_1fr] items-center">
                            <div>
                                <p className="font-medium text-stone-800">
                                    Boba
                                </p>

                                <p className="mt-1 text-xs text-stone-400">
                                    Prep Station
                                </p>
                            </div>

                            <p className="text-sm text-stone-600">
                                ½ batch
                            </p>

                            <div>
                                <span className="rounded-full bg-[#dcecee] px-3 py-1 text-xs font-semibold text-stone-700">
                                    Preparing
                                </span>
                            </div>

                            <p className="text-sm text-stone-500">
                                Ready in ~24 min
                            </p>
                        </div>
                    </div>

                    <div className="border-t border-stone-100 px-6 py-5">
                        <div className="grid grid-cols-[1.5fr_1fr_1fr_1fr] items-center">
                            <div>
                                <p className="font-medium text-stone-800">
                                    Thai Tea
                                </p>

                                <p className="mt-1 text-xs text-stone-400">
                                    Refrigerator
                                </p>
                            </div>

                            <p className="text-sm text-stone-600">
                                1 batch
                            </p>

                            <div>
                                <span className="rounded-full bg-green-100 px-3 py-1 text-xs font-semibold text-green-700">
                                    Ready
                                </span>
                            </div>

                            <p className="text-sm text-stone-500">
                                Expires in 2 days
                            </p>
                        </div>
                    </div>

                </section>

            </div>

        </div>
    );
}

export default Batches;