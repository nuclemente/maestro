/**
 * Card placeholder com shimmer enquanto a lista carrega. Mantém exatamente as
 * mesmas dimensões do `PersonCard` para evitar layout shift.
 */
export default function SkeletonCard() {
  return (
    <div
      aria-hidden
      className="relative overflow-hidden rounded-lg border border-neutral-200 bg-neutral-0 p-4 shadow-sm"
    >
      <div className="flex items-start gap-3">
        <div className="h-10 w-10 rounded-full bg-neutral-100" />
        <div className="flex-1 space-y-2">
          <div className="h-3.5 w-2/3 rounded bg-neutral-100" />
          <div className="h-3 w-1/2 rounded bg-neutral-100" />
        </div>
      </div>
      <div className="mt-4 flex items-center gap-2">
        <div className="h-5 w-20 rounded-full bg-neutral-100" />
        <div className="h-3 w-8 rounded bg-neutral-100" />
      </div>
      <div className="maestro-shimmer pointer-events-none absolute inset-0" />
    </div>
  );
}
