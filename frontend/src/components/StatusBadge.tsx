"use client";
export default function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    queued: "bg-zinc-700 text-zinc-300",
    running: "bg-blue-900/50 text-blue-300 border border-blue-700",
    complete: "bg-emerald-900/50 text-emerald-300 border border-emerald-700",
    failed: "bg-red-900/50 text-red-300 border border-red-700",
  };
  return (
    <span
      className={`text-xs px-2 py-0.5 rounded-full font-medium ${colors[status] || colors.queued}`}
    >
      {status}
    </span>
  );
}
