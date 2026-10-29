import type { ReactNode } from "react";

export function SectionHeader({
  id,
  title,
  description,
  action,
}: {
  id: string;
  title: string;
  description: string;
  action?: ReactNode;
}) {
  return (
    <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
      <div className="space-y-1">
        <h2 id={id} className="text-xl font-semibold tracking-tight text-balance">
          {title}
        </h2>
        <p className="max-w-prose text-sm text-pretty text-muted-foreground">{description}</p>
      </div>
      {action}
    </div>
  );
}
