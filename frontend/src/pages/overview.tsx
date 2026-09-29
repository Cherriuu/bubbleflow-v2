function Overview() {
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
                        --
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
                        --
                    </p>

                    <p className="mt-2 text-xs text-stone-400">
                        Items needing attention
                    </p>
                </div>

                <div className="rounded-3xl border border-stone-200 bg-[#FFFDF7] p-6">
                    <p className="text-sm font-medium text-stone-400">
                        Active batches
                    </p>

                    <p className="mt-2 text-3xl font-bold text-stone-800">
                        --
                    </p>

                    <p className="mt-2 text-xs text-stone-400">
                        Preparing or ready
                    </p>
                </div>

                <div className="rounded-3xl border border-stone-200 bg-[#FFFDF7] p-6">
                    <p className="text-sm font-medium text-stone-400">
                        Pending orders
                    </p>

                    <p className="mt-2 text-3xl font-bold text-stone-800">
                        --
                    </p>

                    <p className="mt-2 text-xs text-stone-400">
                        Waiting to be completed
                    </p>
                </div>

            </div>

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

                    <div className="flex flex-col">

                        <div className="flex items-center justify-between border-b border-stone-100 px-6 py-5">
                            <div>
                                <p className="font-medium text-stone-800">
                                    Boba
                                </p>

                                <p className="mt-1 text-xs text-stone-400">
                                    ~8 drinks remaining
                                </p>
                            </div>

                            <span className="rounded-full bg-yellow-100 px-3 py-1 text-xs font-semibold text-yellow-700">
                                Low
                            </span>
                        </div>

                        <div className="flex items-center justify-between border-b border-stone-100 px-6 py-5">
                            <div>
                                <p className="font-medium text-stone-800">
                                    Thai Tea
                                </p>

                                <p className="mt-1 text-xs text-stone-400">
                                    ~31 drinks remaining
                                </p>
                            </div>

                            <span className="rounded-full bg-green-100 px-3 py-1 text-xs font-semibold text-green-700">
                                Available
                            </span>
                        </div>

                        <div className="flex items-center justify-between px-6 py-5">
                            <div>
                                <p className="font-medium text-stone-800">
                                    Coffee
                                </p>

                                <p className="mt-1 text-xs text-stone-400">
                                    ~14 drinks remaining
                                </p>
                            </div>

                            <span className="rounded-full bg-yellow-100 px-3 py-1 text-xs font-semibold text-yellow-700">
                                Low
                            </span>
                        </div>

                    </div>

                </section>

                <section className="overflow-hidden rounded-3xl border border-stone-200 bg-[#FFFDF7]">

                    <div className="border-b border-stone-200 px-6 py-5">
                        <div className="flex items-center justify-between">
                            <div>
                                <h2 className="text-lg font-semibold text-stone-800">
                                    Active batches
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

                    <div className="flex flex-col">

                        <div className="flex items-center justify-between border-b border-stone-100 px-6 py-5">
                            <div>
                                <p className="font-medium text-stone-800">
                                    Boba
                                </p>

                                <p className="mt-1 text-xs text-stone-400">
                                    ½ batch · Prep Station
                                </p>
                            </div>

                            <div className="text-right">
                                <span className="rounded-full bg-[#dcecee] px-3 py-1 text-xs font-semibold text-stone-700">
                                    Preparing
                                </span>

                                <p className="mt-2 text-xs text-stone-400">
                                    Ready in ~24 min
                                </p>
                            </div>
                        </div>

                        <div className="flex items-center justify-between px-6 py-5">
                            <div>
                                <p className="font-medium text-stone-800">
                                    Thai Tea
                                </p>

                                <p className="mt-1 text-xs text-stone-400">
                                    1 batch · Refrigerator
                                </p>
                            </div>

                            <div className="text-right">
                                <span className="rounded-full bg-green-100 px-3 py-1 text-xs font-semibold text-green-700">
                                    Ready
                                </span>

                                <p className="mt-2 text-xs text-stone-400">
                                    Expires in 2 days
                                </p>
                            </div>
                        </div>

                    </div>

                </section>

            </div>

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

                    <div className="flex flex-col">

                        <div className="grid grid-cols-[0.6fr_1.5fr_1fr] items-center border-b border-stone-100 px-6 py-5">
                            <p className="text-sm font-semibold text-stone-700">
                                #104
                            </p>

                            <div>
                                <p className="text-sm font-medium text-stone-800">
                                    Thai Milk Tea
                                </p>

                                <p className="mt-1 text-xs text-stone-400">
                                    Medium · 50% sugar · Less ice
                                </p>
                            </div>

                            <div className="text-right">
                                <span className="rounded-full bg-[#dcecee] px-3 py-1 text-xs font-semibold text-stone-700">
                                    Pending
                                </span>
                            </div>
                        </div>

                        <div className="grid grid-cols-[0.6fr_1.5fr_1fr] items-center px-6 py-5">
                            <p className="text-sm font-semibold text-stone-700">
                                #103
                            </p>

                            <div>
                                <p className="text-sm font-medium text-stone-800">
                                    Brown Sugar Boba
                                </p>

                                <p className="mt-1 text-xs text-stone-400">
                                    Large · 100% sugar · Regular ice
                                </p>
                            </div>

                            <div className="text-right">
                                <span className="rounded-full bg-green-100 px-3 py-1 text-xs font-semibold text-green-700">
                                    Completed
                                </span>
                            </div>
                        </div>

                    </div>

                </section>

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

                        <div className="rounded-2xl border border-pink-100 bg-pink-50 px-4 py-4">
                            <div className="flex items-center justify-between">
                                <p className="font-medium text-stone-800">
                                    Boba
                                </p>

                                <span className="rounded-full bg-pink-300 px-3 py-1 text-xs font-semibold text-white">
                                    High
                                </span>
                            </div>

                            <p className="mt-2 text-xs leading-5 text-stone-500">
                                Current inventory may not cover forecasted demand.
                            </p>
                        </div>

                        <div className="rounded-2xl border border-stone-200 px-4 py-4">
                            <div className="flex items-center justify-between">
                                <p className="font-medium text-stone-800">
                                    Coffee
                                </p>

                                <span className="rounded-full bg-[#dcecee] px-3 py-1 text-xs font-semibold text-stone-700">
                                    Watch
                                </span>
                            </div>

                            <p className="mt-2 text-xs leading-5 text-stone-500">
                                Inventory is approaching the low-stock range.
                            </p>
                        </div>

                    </div>

                </section>

            </div>

        </div>
    );
}

export default Overview;