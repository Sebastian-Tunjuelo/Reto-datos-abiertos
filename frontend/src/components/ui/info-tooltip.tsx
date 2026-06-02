import { CircleHelp } from "lucide-react";

import { cn } from "@/lib/utils";

interface InfoTooltipProps {
  label: string;
  description: string;
  className?: string;
}

export function InfoTooltip({
  label,
  description,
  className,
}: InfoTooltipProps) {
  return (
    <span
      className={cn(
        "group relative inline-flex items-center align-middle",
        className,
      )}
    >
      <button
        type="button"
        aria-label={label}
        className="inline-flex size-4 items-center justify-center rounded-full text-muted-foreground transition-colors hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
      >
        <CircleHelp className="size-3.5" aria-hidden="true" />
      </button>
      <span className="pointer-events-none invisible absolute left-1/2 top-full z-20 mt-2 w-56 -translate-x-1/2 rounded-lg border border-border bg-popover px-3 py-2 text-left text-xs text-popover-foreground opacity-0 shadow-lg transition-all duration-150 group-hover:visible group-hover:opacity-100 group-focus-within:visible group-focus-within:opacity-100">
        {description}
      </span>
    </span>
  );
}
