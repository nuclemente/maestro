import { HTMLAttributes } from 'react';

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  padded?: boolean;
}

export default function Card({ padded = true, className = '', children, ...rest }: CardProps) {
  return (
    <div
      className={`rounded-lg border border-neutral-200 bg-neutral-0 shadow-sm ${
        padded ? 'p-6' : ''
      } ${className}`}
      {...rest}
    >
      {children}
    </div>
  );
}
