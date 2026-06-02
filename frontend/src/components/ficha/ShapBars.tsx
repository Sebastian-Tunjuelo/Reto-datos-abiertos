import { cn } from "@/lib/utils";
import type { ShapItem } from "@/components/FichaMunicipal";

interface Props {
  items: ShapItem[];
}

export default function ShapBars({ items }: Props) {
  // Take top 5
  const top = items.slice(0, 5);

  // Compute max abs value for scaling
  const maxAbs = Math.max(
    ...top.map((i) => Math.abs(i.value ?? 0)),
    0.001
  );

  return (
    <div className="rounded-xl border border-border bg-card p-5">
      <h2 className="text-sm font-semibold mb-1">Factores determinantes</h2>
      <p className="text-xs text-muted-foreground mb-4">
        Variables con mayor influencia en la predicción de riesgo (SHAP)
      </p>
      <div className="space-y-3">
        {top.map((item, idx) => {
          const pct =
            item.value != null
              ? Math.round((Math.abs(item.value) / maxAbs) * 100)
              : Math.round(100 - idx * 20); // fallback ranking

          const isPositive =
            item.direction?.toLowerCase().includes("sube") ||
            item.direction?.toLowerCase().includes("aumenta") ||
            item.direction?.toLowerCase().includes("eleva") ||
            (item.value != null && item.value > 0);

          return (
            <div key={idx} className="flex items-center gap-3">
              {/* Rank */}
              <span className="text-xs text-muted-foreground w-4 shrink-0 text-right">
                {idx + 1}
              </span>

              {/* Label */}
              <span className="text-xs font-medium w-40 shrink-0 truncate" title={item.label}>
                {item.label}
              </span>

              {/* Bar */}
              <div className="flex-1 h-5 bg-muted rounded-full overflow-hidden">
                <div
                  className={cn(
                    "h-full rounded-full transition-all duration-500",
                    isPositive ? "bg-red-400" : "bg-green-500"
                  )}
                  style={{ width: `${pct}%` }}
                />
              </div>

              {/* Value / direction */}
              <span className="text-xs text-muted-foreground w-20 shrink-0 text-right">
                {item.value != null
                  ? item.value.toFixed(3)
                  : item.direction ?? "—"}
              </span>
            </div>
          );
        })}
      </div>
      <p className="text-xs text-muted-foreground mt-3">
        Rojo = eleva el riesgo · Verde = reduce el riesgo
      </p>
    </div>
  );
}
