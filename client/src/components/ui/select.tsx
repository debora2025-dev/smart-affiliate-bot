import { cn } from '@/lib/utils';
import { SelectHTMLAttributes, forwardRef } from 'react';

interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  onValueChange?: (value: string) => void;
}

const Select = forwardRef<HTMLSelectElement, SelectProps>(
  ({ className, onValueChange, onChange, children, ...props }, ref) => (
    <select
      ref={ref}
      className={cn(
        'border-input bg-transparent h-9 w-fit rounded-md border px-3 py-1 text-sm shadow-xs outline-none focus-visible:border-ring focus-visible:ring-2 focus-visible:ring-ring/30 disabled:cursor-not-allowed disabled:opacity-50',
        className,
      )}
      onChange={(e) => {
        onChange?.(e);
        onValueChange?.(e.target.value);
      }}
      {...props}
    >
      {children}
    </select>
  ),
);
Select.displayName = 'Select';

function SelectItem({ value, children }: { value: string; children: React.ReactNode }) {
  return <option value={value}>{children}</option>;
}

export { Select, SelectItem };
