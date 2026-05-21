import { Loader2 } from 'lucide-react';

interface SpinnerProps {
  size?: number;
  label?: string;
}

export default function Spinner({ size = 18, label }: SpinnerProps) {
  return (
    <div className="inline-flex items-center gap-2 text-neutral-500">
      <Loader2 size={size} className="animate-spin" />
      {label && <span className="text-sm">{label}</span>}
    </div>
  );
}
