import * as React from "react";

import { cn } from "@/lib/cn";

export type InputProps = React.InputHTMLAttributes<HTMLInputElement>;

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, type = "text", ...props }, ref) => (
    <input
      ref={ref}
      type={type}
      className={cn(
        "h-10 w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-navy placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-navy/20",
        className,
      )}
      {...props}
    />
  ),
);
Input.displayName = "Input";
