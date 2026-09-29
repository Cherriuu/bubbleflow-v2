function Production() {
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
                    Use recent demand and current inventory to stay ahead
                    of the next rush.
                </p>
            </div>

            <div className="mb-8 grid gap-4 sm:grid-cols-3">

                <div className="rounded-3xl border border-stone-200 bg-[#FFFDF7] p-6">
                    <p className="text-sm font-medium text-stone-400">
                        Items to prepare
                    </p>

                    <p className="mt-2 text-3xl font-bold text-pink-300">
                        --
                    </p>
                </div>

                <div className="rounded-3xl border border-stone-200 bg-[#FFFDF7] p-6">
                    <p className="text-sm font-medium text-stone-400">
                        Low stock
                    </p>

                    <p className="mt-2 text-3xl font-bold text-stone-800">
                        --
                    </p>
                </div>

                <div className="rounded-3xl border border-stone-200 bg-[#FFFDF7] p-6">
                    <p className="text-sm font-medium text-stone-400">
                        Forecast window
                    </p>

                    <p className="mt-2 text-3xl font-bold text-stone-800">
                        2 hr
                    </p>
                </div>

            </div>

            <section className="mb-6 overflow-hidden rounded-3xl border border-stone-200 bg-[#FFFDF7]">

                <div className="border-b border-stone-200 px-6 py-5">
                    <h2 className="text-lg font-semibold text-stone-800">
                        Production recommendations
                    </h2>

                    <p className="mt-1 text-sm text-stone-400">
                        Suggested preparation based on recent usage and
                        available inventory.
                    </p>
                </div>

                <div className="grid grid-cols-[1.5fr_1fr_1fr_1.2fr] px-6 py-3 text-xs font-semibold uppercase tracking-wide text-stone-400">
                    <span>Item</span>
                    <span>Available</span>
                    <span>Usage rate</span>
                    <span>Recommendation</span>
                </div>

                <div className="border-t border-stone-100 px-6 py-5">
                    <div className="grid grid-cols-[1.5fr_1fr_1fr_1.2fr] items-center">

                        <div>
                            <p className="font-medium text-stone-800">
                                Boba
                            </p>

                            <p className="mt-1 text-xs text-stone-400">
                                Prepared inventory
                            </p>
                        </div>

                        <p className="text-sm text-stone-600">
                            ~8 drinks
                        </p>

                        <p className="text-sm text-stone-600">
                            ~12 / hr
                        </p>

                        <div>
                            <p className="text-sm font-semibold text-pink-400">
                                Prepare more
                            </p>

                            <p className="mt-1 text-xs text-stone-400">
                                ~½ batch suggested
                            </p>
                        </div>

                    </div>
                </div>

                <div className="border-t border-stone-100 px-6 py-5">
                    <div className="grid grid-cols-[1.5fr_1fr_1fr_1.2fr] items-center">

                        <div>
                            <p className="font-medium text-stone-800">
                                Thai Tea
                            </p>

                            <p className="mt-1 text-xs text-stone-400">
                                Prepared inventory
                            </p>
                        </div>

                        <p className="text-sm text-stone-600">
                            ~31 drinks
                        </p>

                        <p className="text-sm text-stone-600">
                            ~6 / hr
                        </p>

                        <div>
                            <span className="rounded-full bg-green-100 px-3 py-1 text-xs font-semibold text-green-700">
                                Enough for now
                            </span>
                        </div>

                    </div>
                </div>

                <div className="border-t border-stone-100 px-6 py-5">
                    <div className="grid grid-cols-[1.5fr_1fr_1fr_1.2fr] items-center">

                        <div>
                            <p className="font-medium text-stone-800">
                                Coffee
                            </p>

                            <p className="mt-1 text-xs text-stone-400">
                                Prepared inventory
                            </p>
                        </div>

                        <p className="text-sm text-stone-600">
                            ~14 drinks
                        </p>

                        <p className="text-sm text-stone-600">
                            ~4 / hr
                        </p>

                        <div>
                            <span className="rounded-full bg-[#dcecee] px-3 py-1 text-xs font-semibold text-stone-700">
                                Watch
                            </span>
                        </div>

                    </div>
                </div>

            </section>

            <div className="grid gap-6 lg:grid-cols-2">

                <section className="rounded-3xl border border-stone-200 bg-[#FFFDF7] p-6">

                    <h2 className="text-lg font-semibold text-stone-800">
                        How the forecast works
                    </h2>

                    <p className="mt-2 text-sm leading-6 text-stone-500">
                        BubbleFlow looks at recent order consumption to
                        estimate how quickly each prepared item is being used.
                        It compares expected demand with what's currently
                        available and adds a small buffer for uncertainty.
                    </p>

                    <div className="mt-6 flex flex-col gap-4">

                        <div className="rounded-2xl bg-stone-50 px-4 py-4">
                            <p className="text-xs font-semibold uppercase tracking-wide text-stone-400">
                                Recent history
                            </p>

                            <p className="mt-1 text-sm font-medium text-stone-700">
                                Last 4 hours
                            </p>
                        </div>

                        <div className="rounded-2xl bg-stone-50 px-4 py-4">
                            <p className="text-xs font-semibold uppercase tracking-wide text-stone-400">
                                Forecast
                            </p>

                            <p className="mt-1 text-sm font-medium text-stone-700">
                                Next 2 hours
                            </p>
                        </div>

                        <div className="rounded-2xl bg-stone-50 px-4 py-4">
                            <p className="text-xs font-semibold uppercase tracking-wide text-stone-400">
                                Inventory buffer
                            </p>

                            <p className="mt-1 text-sm font-medium text-stone-700">
                                10%
                            </p>
                        </div>

                    </div>

                </section>

                <section className="rounded-3xl border border-stone-200 bg-[#FFFDF7] p-6">

                    <h2 className="text-lg font-semibold text-stone-800">
                        Production queue
                    </h2>

                    <p className="mt-1 text-sm text-stone-400">
                        Items that may need attention next.
                    </p>

                    <div className="mt-6 flex flex-col gap-3">

                        <div className="flex items-center justify-between rounded-2xl border border-pink-100 bg-pink-50 px-4 py-4">
                            <div>
                                <p className="font-medium text-stone-800">
                                    Boba
                                </p>

                                <p className="mt-1 text-xs text-stone-500">
                                    Inventory may not cover forecasted demand.
                                </p>
                            </div>

                            <span className="rounded-full bg-pink-300 px-3 py-1 text-xs font-semibold text-white">
                                High
                            </span>
                        </div>

                        <div className="flex items-center justify-between rounded-2xl border border-stone-200 px-4 py-4">
                            <div>
                                <p className="font-medium text-stone-800">
                                    Coffee
                                </p>

                                <p className="mt-1 text-xs text-stone-500">
                                    Inventory is approaching the low-stock range.
                                </p>
                            </div>

                            <span className="rounded-full bg-[#dcecee] px-3 py-1 text-xs font-semibold text-stone-700">
                                Watch
                            </span>
                        </div>

                    </div>

                </section>

            </div>

        </div>
    );
}

export default Production;