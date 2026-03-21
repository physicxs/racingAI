export function PipelineStep({
  label,
  sub,
  isLast,
}: {
  label: string;
  sub: string;
  isLast: boolean;
}) {
  return (
    <>
      <div className="flex flex-col items-center rounded-lg border border-zinc-800 bg-zinc-900/60 px-5 py-4 text-center">
        <span className="text-sm font-semibold text-white">{label}</span>
        <span className="mt-1 text-xs text-zinc-500">{sub}</span>
      </div>
      {!isLast && (
        <span className="hidden text-zinc-600 sm:block">→</span>
      )}
    </>
  );
}
