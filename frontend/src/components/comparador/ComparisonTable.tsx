import { cn } from "@/lib/utils";
import type {
  CultivoComparacion,
  EtiquetaRiesgo,
} from "@/components/ComparadorCultivos";
import { InfoTooltip } from "@/components/ui/info-tooltip";

const ETIQUETA_BADGE: Record<EtiquetaRiesgo, string> = {
  Bajo: "bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-400",
  Medio: "bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-400",
  Alto: "bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-400",
  "Sin datos": "bg-muted text-muted-foreground",
};

const RANK_EMOJI = ["🏆", "🥈", "🥉"];

interface Props {
  data: CultivoComparacion[];
}

function Badge({ etiqueta }: { etiqueta: EtiquetaRiesgo }) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium whitespace-nowrap",
        ETIQUETA_BADGE[etiqueta],
      )}
    >
      {etiqueta}
    </span>
  );
}

function ProbBar({ prob }: { prob: number | null }) {
  if (prob === null)
    return <span className="text-muted-foreground text-xs">—</span>;
  const pct = Math.round(prob * 100);
  const color =
    pct >= 60 ? "bg-red-400" : pct >= 35 ? "bg-amber-400" : "bg-green-500";
  return (
    <div className="flex items-center gap-2">
      <div className="w-20 h-2 rounded-full bg-muted overflow-hidden">
        <div
          className={cn("h-full rounded-full", color)}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-xs tabular-nums">{pct}%</span>
    </div>
  );
}

export default function ComparisonTable({ data }: Props) {
  return (
    <div className="rounded-xl border border-border bg-card overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-border bg-muted/50">
            <th className="text-left px-4 py-3 font-semibold text-xs uppercase tracking-wide text-muted-foreground">
              <span className="inline-flex items-center gap-1.5">
                Cultivo
                <InfoTooltip
                  label="Qué significa cultivo"
                  description="Nombre del cultivo evaluado en la comparación."
                />
              </span>
            </th>
            <th className="text-left px-4 py-3 font-semibold text-xs uppercase tracking-wide text-muted-foreground">
              <span className="inline-flex items-center gap-1.5">
                Nivel de riesgo
                <InfoTooltip
                  label="Qué significa nivel de riesgo"
                  description="Etiqueta resumida del riesgo estimado para el cultivo: bajo, medio o alto."
                />
              </span>
            </th>
            <th className="text-left px-4 py-3 font-semibold text-xs uppercase tracking-wide text-muted-foreground">
              <span className="inline-flex items-center gap-1.5">
                Prob. riesgo alto
                <InfoTooltip
                  label="Qué significa probabilidad de riesgo alto"
                  description="Probabilidad estimada de que el cultivo termine en un escenario de riesgo alto."
                />
              </span>
            </th>
            <th className="text-left px-4 py-3 font-semibold text-xs uppercase tracking-wide text-muted-foreground">
              <span className="inline-flex items-center gap-1.5">
                Rendimiento esp.
                <InfoTooltip
                  label="Qué significa rendimiento esperado"
                  description="Producción estimada del cultivo. Se expresa en toneladas por hectárea (t/ha)."
                />
              </span>
            </th>
            <th className="text-left px-4 py-3 font-semibold text-xs uppercase tracking-wide text-muted-foreground">
              <span className="inline-flex items-center gap-1.5">
                Score
                <InfoTooltip
                  label="Qué significa score"
                  description="Puntaje de 0 a 100 que resume y ordena la recomendación entre cultivos."
                />
              </span>
            </th>
          </tr>
        </thead>
        <tbody>
          {data.map((item, idx) => (
            <tr
              key={item.cultivo}
              className={cn(
                "border-b border-border/60 last:border-0 transition-colors hover:bg-muted/30",
                idx === 0 && "bg-yellow-50/50 dark:bg-yellow-950/10",
              )}
            >
              {/* Cultivo */}
              <td className="px-4 py-3 font-medium">
                <div className="flex items-center gap-2">
                  <span className="text-base">{RANK_EMOJI[idx] ?? ""}</span>
                  <span>{item.cultivo}</span>
                  {item.error_msg && (
                    <span className="text-xs text-muted-foreground italic">
                      — {item.error_msg}
                    </span>
                  )}
                </div>
              </td>

              {/* Nivel riesgo */}
              <td className="px-4 py-3">
                <div className="inline-flex items-center gap-1.5">
                  <Badge etiqueta={item.etiqueta_riesgo} />
                  <InfoTooltip
                    label={`Qué significa ${item.etiqueta_riesgo.toLowerCase()}`}
                    description="Categoría resumida del riesgo calculado para este cultivo."
                  />
                </div>
              </td>

              {/* Prob riesgo alto */}
              <td className="px-4 py-3">
                <div className="inline-flex items-center gap-1.5">
                  <ProbBar prob={item.prob_riesgo_alto} />
                  <InfoTooltip
                    label="Qué significa la probabilidad de riesgo alto"
                    description="Porcentaje estimado de que el cultivo se comporte con riesgo alto."
                  />
                </div>
              </td>

              {/* Rendimiento */}
              <td className="px-4 py-3 tabular-nums">
                <div className="inline-flex items-center gap-1.5">
                  {item.rendimiento_esperado != null ? (
                    `${item.rendimiento_esperado.toFixed(2)} t/ha`
                  ) : (
                    <span className="text-muted-foreground">—</span>
                  )}
                  <InfoTooltip
                    label="Qué significa rendimiento esperado"
                    description="Valor estimado de producción por hectárea. t/ha significa toneladas por hectárea."
                  />
                </div>
              </td>

              {/* Score */}
              <td className="px-4 py-3">
                <div className="inline-flex items-center gap-1.5">
                  {item.estado === "ok" ? (
                    <div className="flex items-center gap-2">
                      <div className="w-16 h-2 rounded-full bg-muted overflow-hidden">
                        <div
                          className="h-full rounded-full bg-primary"
                          style={{ width: `${item.score}%` }}
                        />
                      </div>
                      <span className="text-xs tabular-nums font-semibold">
                        {item.score}
                      </span>
                    </div>
                  ) : (
                    <span className="text-muted-foreground text-xs">N/A</span>
                  )}
                  <InfoTooltip
                    label="Qué significa score"
                    description="Puntaje de 0 a 100 que resume la recomendación general del cultivo."
                  />
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
