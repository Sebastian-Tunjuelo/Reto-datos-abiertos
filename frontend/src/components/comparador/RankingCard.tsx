import Link from "next/link";
import { cn } from "@/lib/utils";
import type {
  CultivoComparacion,
  EtiquetaRiesgo,
} from "@/components/ComparadorCultivos";
import { InfoTooltip } from "@/components/ui/info-tooltip";

const RANK_CONFIG = [
  {
    emoji: "🏆",
    label: "1er lugar",
    ring: "ring-yellow-400",
    bg: "bg-yellow-50 dark:bg-yellow-950/20",
  },
  {
    emoji: "🥈",
    label: "2do lugar",
    ring: "ring-slate-400",
    bg: "bg-slate-50 dark:bg-slate-900/30",
  },
  {
    emoji: "🥉",
    label: "3er lugar",
    ring: "ring-amber-700/60",
    bg: "bg-orange-50 dark:bg-orange-950/20",
  },
];

const ETIQUETA_BADGE: Record<EtiquetaRiesgo, string> = {
  Bajo: "bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-400",
  Medio: "bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-400",
  Alto: "bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-400",
  "Sin datos": "bg-muted text-muted-foreground",
};

interface Props {
  rank: number;
  item: CultivoComparacion;
  municipio: string;
  anio: number;
}

export default function RankingCard({ rank, item, municipio, anio }: Props) {
  const cfg = RANK_CONFIG[rank - 1] ?? RANK_CONFIG[2];
  const hasData = item.estado === "ok";

  return (
    <div
      className={cn(
        "rounded-xl border ring-2 p-5 flex flex-col gap-3 transition-shadow hover:shadow-md",
        cfg.bg,
        cfg.ring,
      )}
    >
      {/* Rank header */}
      <div className="flex items-center justify-between">
        <span className="text-2xl">{cfg.emoji}</span>
        <span className="text-xs font-semibold text-muted-foreground">
          {cfg.label}
        </span>
      </div>

      {/* Cultivo name */}
      <div>
        <h3 className="text-lg font-bold leading-tight">{item.cultivo}</h3>
        {item.error_msg && (
          <p className="text-xs text-muted-foreground mt-0.5">
            {item.error_msg}
          </p>
        )}
      </div>

      {/* Score */}
      <div className="flex items-end gap-2">
        <span className="text-3xl font-extrabold leading-none">
          {hasData ? item.score : "N/A"}
        </span>
        {hasData && (
          <span className="inline-flex items-center gap-1 text-xs text-muted-foreground mb-1">
            / 100 pts
            <InfoTooltip
              label="Qué significa score"
              description="Puntaje de 0 a 100 que resume la recomendación del cultivo."
            />
          </span>
        )}
      </div>

      {/* Score bar */}
      {hasData && (
        <div className="h-2 rounded-full bg-muted overflow-hidden">
          <div
            className="h-full rounded-full bg-primary transition-all duration-700"
            style={{ width: `${item.score}%` }}
          />
        </div>
      )}

      {/* Metrics */}
      <div className="flex flex-wrap gap-2 mt-1">
        <span className="inline-flex items-center gap-1">
          <span
            className={cn(
              "inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium",
              ETIQUETA_BADGE[item.etiqueta_riesgo],
            )}
          >
            {item.etiqueta_riesgo}
          </span>
          <InfoTooltip
            label="Qué significa el nivel de riesgo"
            description="Etiqueta resumida que clasifica el riesgo del cultivo."
          />
        </span>
        {item.rendimiento_esperado != null && (
          <span className="inline-flex items-center gap-1">
            <span className="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium bg-muted text-muted-foreground">
              {item.rendimiento_esperado.toFixed(2)} t/ha
            </span>
            <InfoTooltip
              label="Qué significa rendimiento esperado"
              description="Producción estimada por hectárea. t/ha significa toneladas por hectárea."
            />
          </span>
        )}
      </div>

      {/* Link to ficha */}
      {municipio && (
        <Link
          href={`/municipio/${municipio}/${encodeURIComponent(item.cultivo)}?anio=${anio}`}
          className="text-xs text-primary underline-offset-2 hover:underline mt-auto"
        >
          Ver ficha detallada →
        </Link>
      )}
    </div>
  );
}
