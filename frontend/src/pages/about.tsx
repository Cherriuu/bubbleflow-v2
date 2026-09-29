function About() {
  return (
    <div className="mx-auto max-w-5xl px-6 py-8">

      {/* Header */}
      <div className="mb-12">
        <p className="mb-2 text-2xl font-semibold text-pink-300">
          About BubbleFlow
        </p>

        <h1 className="max-w-3xl text-4xl font-bold tracking-tight text-stone-800">
          Made for the rhythm of a busy boba shop.
        </h1>

        <p className="mt-4 max-w-2xl text-base leading-7 text-stone-500">
          BubbleFlow brings production, inventory, and orders together so
          teams can spend less time guessing what needs to be made and more
          time keeping the shop moving.
        </p>
      </div>

      {/* About */}
      <section className="mb-8 rounded-3xl border border-stone-200 bg-[#FFFDF7] p-7">
        <h2 className="text-xl font-semibold text-stone-800">
          What is BubbleFlow?
        </h2>

        <p className="mt-3 max-w-3xl leading-7 text-stone-500">
          BubbleFlow is a production, inventory, and order coordination
          system designed for high-volume boba shops. It tracks prepared
          ingredients as batches, follows inventory as it is produced,
          consumed, wasted, or corrected, and helps teams understand what
          should be prepared next.
        </p>
      </section>

      {/* Workflow */}
      <section className="mb-8">
        <h2 className="mb-4 text-xl font-semibold text-stone-800">
          How it works
        </h2>

        <div className="grid gap-4 md:grid-cols-4">

          <div className="rounded-3xl border border-stone-200 bg-[#FFFDF7] p-5">
            <div className="mb-4 flex h-9 w-9 items-center justify-center rounded-full bg-[#dcecee] text-sm font-semibold text-stone-600">
              01
            </div>

            <h3 className="font-semibold text-stone-800">
              Produce
            </h3>

            <p className="mt-2 text-sm leading-6 text-stone-500">
              Create and track batches of prepared ingredients.
            </p>
          </div>

          <div className="rounded-3xl border border-stone-200 bg-[#FFFDF7] p-5">
            <div className="mb-4 flex h-9 w-9 items-center justify-center rounded-full bg-[#dcecee] text-sm font-semibold text-stone-600">
              02
            </div>

            <h3 className="font-semibold text-stone-800">
              Track
            </h3>

            <p className="mt-2 text-sm leading-6 text-stone-500">
              Follow available inventory, expiration, waste, and corrections.
            </p>
          </div>

          <div className="rounded-3xl border border-stone-200 bg-[#FFFDF7] p-5">
            <div className="mb-4 flex h-9 w-9 items-center justify-center rounded-full bg-[#dcecee] text-sm font-semibold text-stone-600">
              03
            </div>

            <h3 className="font-semibold text-stone-800">
              Serve
            </h3>

            <p className="mt-2 text-sm leading-6 text-stone-500">
              Connect customer orders to the ingredients they consume.
            </p>
          </div>

          <div className="rounded-3xl border border-stone-200 bg-[#FFFDF7] p-5">
            <div className="mb-4 flex h-9 w-9 items-center justify-center rounded-full bg-[#dcecee] text-sm font-semibold text-stone-600">
              04
            </div>

            <h3 className="font-semibold text-stone-800">
              Plan
            </h3>

            <p className="mt-2 text-sm leading-6 text-stone-500">
              Use current inventory and demand to guide what should be made
              next.
            </p>
          </div>

        </div>
      </section>

      {/* Technology */}
      <section className="rounded-3xl border border-stone-200 bg-[#FFFDF7] p-7">
        <h2 className="text-xl font-semibold text-stone-800">
          Built with
        </h2>

        <p className="mt-2 text-sm text-stone-500">
          The tools behind BubbleFlow.
        </p>

        <div className="mt-5 flex flex-wrap gap-2">
          {[
            "React",
            "TypeScript",
            "Tailwind CSS",
            "Django",
            "Django REST Framework",
            "PostgreSQL",
          ].map((technology) => (
            <span
              key={technology}
              className="rounded-full bg-[#dcecee] px-4 py-2 text-sm font-medium text-stone-600"
            >
              {technology}
            </span>
          ))}
        </div>
      </section>

      {/* Footer */}
      <p className="mt-10 text-center text-sm text-stone-400">
        Designed and developed by Jesica ♡
      </p>

    </div>
  );
}

export default About;