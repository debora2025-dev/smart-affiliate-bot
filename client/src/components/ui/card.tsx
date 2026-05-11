import { cn } from '@/lib/utils';
import { HTMLAttributes } from 'react';

function Card({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn('bg-card text-card-foreground flex flex-col gap-6 rounded-xl border py-6 shadow-sm', className)}
      {...props}
    />
  );
}

function CardHeader({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return <div className={cn('px-6', className)} {...props} />;
}

function CardTitle({ className, ...props }: HTMLAttributes<HTMLHeadingElement>) {
  return <h3 className={cn('font-semibold leading-none', className)} {...props} />;
}

function CardDescription({ className, ...props }: HTMLAttributes<HTMLParagraphElement>) {
  return <p className={cn('text-sm text-muted-foreground', className)} {...props} />;
}

function CardContent({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return <div className={cn('px-6', className)} {...props} />;
}

export { Card, CardHeader, CardTitle, CardDescription, CardContent };
