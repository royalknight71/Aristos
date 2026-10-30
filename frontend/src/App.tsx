const capabilities = [
  {
    number: '01',
    title: 'Find the signal',
    description:
      'Search across engineering documents with questions phrased in the language your team uses.',
  },
  {
    number: '02',
    title: 'See the evidence',
    description:
      'Trace every answer back to the passages and pages that support it.',
  },
  {
    number: '03',
    title: 'Know when to pause',
    description:
      'Get a clear abstention when the available material cannot support a reliable answer.',
  },
]

function App() {
  return (
    <main className="min-h-screen overflow-hidden bg-[#f6f7f4] text-[#17231f]">
      <div className="mx-auto flex min-h-screen max-w-7xl flex-col px-6 sm:px-10">
        <header className="flex items-center justify-between border-b border-[#dce2dc] py-6">
          <a className="flex items-center gap-3" href="#home" aria-label="Aristos home">
            <span className="grid size-9 place-items-center rounded-xl bg-[#193d34] text-sm font-semibold text-white">
              A
            </span>
            <span className="text-sm font-semibold tracking-[0.12em]">ARISTOS</span>
          </a>
          <span className="rounded-full border border-[#cbd6ce] px-3 py-1.5 text-xs font-medium text-[#53675e]">
            Early development
          </span>
        </header>

        <section
          id="home"
          className="relative grid flex-1 items-center gap-16 py-20 lg:grid-cols-[1.1fr_0.9fr] lg:py-28"
        >
          <div className="relative z-10 max-w-2xl">
            <p className="mb-7 flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.2em] text-[#52766a]">
              <span className="size-1.5 rounded-full bg-[#78a68f]" />
              Engineering knowledge, connected
            </p>
            <h1 className="text-5xl font-medium leading-[1.08] tracking-[-0.055em] sm:text-6xl lg:text-7xl">
              Answers grounded in <span className="text-[#648274]">your work.</span>
            </h1>
            <p className="mt-7 max-w-xl text-base leading-7 text-[#58665f] sm:text-lg sm:leading-8">
              Aristos is being built to help engineering teams find trusted answers in their
              technical knowledge, with sources close at hand.
            </p>
            <a
              className="mt-10 inline-flex items-center gap-3 rounded-lg bg-[#193d34] px-5 py-3.5 text-sm font-medium text-white transition hover:bg-[#285748] focus:outline-none focus:ring-2 focus:ring-[#78a68f] focus:ring-offset-2"
              href="#how-it-works"
            >
              Explore the approach
              <span aria-hidden="true">↗</span>
            </a>
            <p className="mt-5 text-xs text-[#7a8981]">A project in active development</p>
          </div>

          <div className="relative mx-auto w-full max-w-md lg:mr-5">
            <div className="absolute -inset-8 rounded-full bg-[#dfe9e1] blur-3xl" />
            <div className="relative rounded-2xl border border-[#dce3dc] bg-white/90 p-5 shadow-[0_24px_70px_-36px_rgba(28,55,43,0.32)] sm:p-7">
              <div className="flex items-center justify-between border-b border-[#edf0ec] pb-4">
                <div>
                  <p className="text-xs font-medium text-[#7e8a83]">ENGINEERING LIBRARY</p>
                  <p className="mt-1 text-sm font-semibold">A question, with context</p>
                </div>
                <span className="grid size-9 place-items-center rounded-full bg-[#edf4ef] text-[#52766a]" aria-hidden="true">
                  ✳
                </span>
              </div>
              <div className="mt-6 rounded-xl bg-[#f4f7f3] p-4 text-sm leading-6 text-[#31423a]">
                What should we check before a service rollout?
              </div>
              <div className="mt-5 flex gap-3">
                <span className="mt-1 size-2 shrink-0 rounded-full bg-[#78a68f]" />
                <div>
                  <p className="text-sm leading-6 text-[#526158]">
                    A grounded answer can bring the relevant runbook steps together and show
                    where each detail came from.
                  </p>
                  <div className="mt-4 rounded-lg border border-[#dce7df] bg-[#fbfcfa] p-3">
                    <p className="text-[10px] font-semibold uppercase tracking-[0.15em] text-[#668473]">
                      Example source
                    </p>
                    <p className="mt-1.5 text-xs font-medium text-[#344b40]">
                      Release readiness runbook <span className="text-[#84958b]">· p. 12</span>
                    </p>
                  </div>
                </div>
              </div>
              <p className="mt-5 border-t border-[#edf0ec] pt-4 text-[11px] text-[#88938d]">
                Illustrative preview · not a live product
              </p>
            </div>
          </div>
        </section>

        <section id="how-it-works" className="border-t border-[#dce2dc] py-12 sm:py-14">
          <div className="grid gap-8 sm:grid-cols-3 sm:gap-10">
            {capabilities.map((item) => (
              <article key={item.number}>
                <p className="text-xs font-semibold tracking-[0.14em] text-[#82968a]">{item.number}</p>
                <h2 className="mt-3 text-base font-semibold">{item.title}</h2>
                <p className="mt-2 max-w-sm text-sm leading-6 text-[#68756e]">{item.description}</p>
              </article>
            ))}
          </div>
        </section>

        <footer className="flex flex-col gap-2 border-t border-[#dce2dc] py-5 text-xs text-[#849087] sm:flex-row sm:items-center sm:justify-between">
          <span>Aristos — Engineering Knowledge Copilot</span>
          <span>Planned capabilities · implementation in progress</span>
        </footer>
      </div>
    </main>
  )
}

export default App
