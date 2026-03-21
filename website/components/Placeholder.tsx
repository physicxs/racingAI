export function Placeholder({
  label,
  className = "",
}: {
  label: string;
  className?: string;
}) {
  return (
    <div
      className={`flex items-center justify-center rounded-lg border border-dashed border-zinc-700 bg-zinc-900/30 text-sm text-zinc-500 ${className}`}
    >
      {label}
    </div>
  );
}
