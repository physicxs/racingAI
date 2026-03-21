import { Section } from "@/components/Section";
import { PipelineStep } from "@/components/PipelineStep";
import { FeatureCard } from "@/components/FeatureCard";
import { Placeholder } from "@/components/Placeholder";

export default function Home() {
  return (
    <main className="min-h-screen">
      {/* ── Hero ──────────────────────────────────────────────── */}
      <section className="flex flex-col items-center justify-center px-6 pt-32 pb-20 text-center">
        <p className="mb-4 text-sm font-medium uppercase tracking-widest text-red-500">
          F1 2025 Telemetry
        </p>
        <h1 className="max-w-3xl text-4xl font-bold leading-tight tracking-tight text-white sm:text-5xl md:text-6xl">
          F1 Telemetry Intelligence System
        </h1>
        <p className="mt-6 max-w-xl text-lg text-zinc-400">
          Real-time race analysis focused on overtaking, defense, and driver
          decision-making.
        </p>

        <Placeholder
          label="Demo Video"
          className="mt-12 aspect-video w-full max-w-3xl"
        />
      </section>

      {/* ── What It Does ─────────────────────────────────────── */}
      <Section title="What It Does">
        <ul className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {[
            "30 Hz telemetry ingestion from F1 2025 UDP",
            "Real-time JSON pipeline",
            "Accurate track maps built from telemetry (not racing line)",
            "Nearby car tracking (top 6 within 1.5s)",
            "Corner-based driver analysis (entry, apex, exit)",
            "Coaching output per corner",
          ].map((item) => (
            <li
              key={item}
              className="rounded-lg border border-zinc-800 bg-zinc-900/50 px-5 py-4 text-sm text-zinc-300"
            >
              {item}
            </li>
          ))}
        </ul>
      </Section>

      {/* ── Demo ─────────────────────────────────────────────── */}
      <Section title="Demo">
        <Placeholder
          label="Demo Video"
          className="aspect-video w-full max-w-3xl mx-auto"
        />

        <div className="mt-10 grid gap-6 sm:grid-cols-3">
          <Placeholder label="Track Map" className="aspect-[4/3]" />
          <Placeholder label="Side-by-Side Cars" className="aspect-[4/3]" />
          <Placeholder label="Telemetry Panel" className="aspect-[4/3]" />
        </div>
      </Section>

      {/* ── How It Works ─────────────────────────────────────── */}
      <Section title="How It Works">
        <div className="flex flex-wrap items-center justify-center gap-3">
          {[
            { label: "F1 Game", sub: "UDP telemetry" },
            { label: "Java Decoder", sub: "Packet parsing" },
            { label: "JSON Stream", sub: "30 Hz JSONL" },
            { label: "Python Analysis", sub: "Corner scoring" },
            { label: "Coaching", sub: "Per-corner feedback" },
            { label: "Visualization", sub: "Track map GUI" },
          ].map((step, i, arr) => (
            <PipelineStep
              key={step.label}
              label={step.label}
              sub={step.sub}
              isLast={i === arr.length - 1}
            />
          ))}
        </div>
      </Section>

      {/* ── Key Features ─────────────────────────────────────── */}
      <Section title="Key Features">
        <div className="grid gap-6 sm:grid-cols-2">
          <FeatureCard
            title="True Track Geometry"
            description="Full-width track maps built from multi-lap edge detection — not a simple racing line."
          />
          <FeatureCard
            title="Lateral Positioning"
            description="Accurate side-by-side battle visualization using world coordinates and segment projection."
          />
          <FeatureCard
            title="Phase-Based Analysis"
            description="Entry, apex, and exit phases detected from real brake/throttle/speed inputs — not geometry alone."
          />
          <FeatureCard
            title="~500× Real-Time"
            description="Full analysis pipeline processes telemetry at ~17,000 FPS. Ready for live coaching at 30 Hz."
          />
        </div>
      </Section>

      {/* ── Example Output ───────────────────────────────────── */}
      <Section title="Example Output">
        <div className="mx-auto max-w-lg rounded-lg border border-zinc-800 bg-zinc-950 p-6 font-mono text-sm leading-relaxed">
          <pre className="text-zinc-300">
            {`{
  "corner": 6,
  "issue": "Braking too late",
  "delta": +6.2
}`}
          </pre>
        </div>
        <p className="mt-4 text-center text-sm text-zinc-500">
          Per-corner coaching feedback generated from telemetry-driven phase
          segmentation and data-driven reference speeds.
        </p>
      </Section>

      {/* ── Future Work ──────────────────────────────────────── */}
      <Section title="Future Work">
        <ul className="mx-auto max-w-md space-y-3">
          {[
            "Overtake detection",
            "Battle intelligence",
            "Web-based live dashboard",
          ].map((item) => (
            <li
              key={item}
              className="flex items-center gap-3 text-zinc-400"
            >
              <span className="h-1.5 w-1.5 rounded-full bg-red-500" />
              {item}
            </li>
          ))}
        </ul>
      </Section>

      {/* ── Footer ───────────────────────────────────────────── */}
      <footer className="border-t border-zinc-800 py-10 text-center text-sm text-zinc-600">
        F1 Telemetry Intelligence System — Built with Java, Python, and
        Next.js
      </footer>
    </main>
  );
}
