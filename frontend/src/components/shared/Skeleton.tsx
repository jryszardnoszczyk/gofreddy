import { cn } from "@/lib/cn";

export function Skeleton({ className }: { className?: string }) {
  return <div className={cn("skeleton", className)} />;
}

export function SkeletonCard({ lines = 3, count = 1 }: { lines?: number; count?: number }) {
  const card = (key: number) => (
    <div key={key} className="rounded-xl border border-border-subtle bg-surface-raised p-5 space-y-3">
      <Skeleton className="h-4 w-1/3" />
      {Array.from({ length: lines }).map((_, i) => (
        <Skeleton key={i} className={cn("h-3", i === lines - 1 ? "w-2/3" : "w-full")} />
      ))}
    </div>
  );

  if (count <= 1) return card(0);

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
      {Array.from({ length: count }).map((_, i) => card(i))}
    </div>
  );
}
