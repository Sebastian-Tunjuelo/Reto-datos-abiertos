import { cn } from "@/lib/utils";
import type { EtiquetaRiesgo } from "@/components/FichaMunicipal";

interface Props {
  etiqueta: EtiquetaRiesgo;
  rendimiento: number | null;
  probRiesgoAlto: number | null;
  anio: number;
  cultivo: string;
}

const ETIQUETA_CONFIG: Record<
  EtiquetaRiesgo,
  { bg: string; border: string; dot: string; label: string }
> = {
  Bajo: {
    bg: "bg-green-50 dark:bg-green-950/30",
    border: "border-green-300 dark:border-green-700",
    dot: "bg-green-500",
    label: "Riesgo Bajo",
  },
  Medio: {
    bg: "bg-amber-50 dark:bg-amber-950/30",
    border: "border-amber-300 dark:border-amber-700",
    dot: "bg-amber-500",
    label: "Riesgo Medio",
  },
  Alto: {
    bg: "bg-red-50 dark:bg-red-950/30",
    border: "border-red-300 dark:border-red-700",
    dot: "bg-red-500",
    label: "Riesgo Alto",
  },
  "Sin datos": {
    bg: "bg-muted",
    border: "border-border",
    dot: "bg-muted-foreground",
    label: "Sin datos",
  },
};

export default function RiesgoSemaforo({
  etiqueta,
  rendimiento,
  probRiesgoAlto,
  anio,
  cultivo,
}: Props) {
  const cfg = ETIQUETA_CONFIG[etiqueta];

  return (
    <div
      className={cn(
        "rounded-xl border p-5 flex flex-col sm:flex-row sm:items-center gap-4",
        cfg.bg,
        cfg.border
      )}
    >
      {/* Semáforo dot */}
      <div className="flex items-center gap-3 sm:flex-col sm:items-center sm:gap-2">
        <span
          className={cn(
            "inline-flex size-12 rounded-full items-center justify-center shrink-0",
            cfg.dot,
            "shadow-md"
          )}
        >
          <span className="size-5 rounded-full bg-white/30" />
        </span>
        <span className="text-sm font-semibold sm:text-center">{cfg.label}</span>
      </div>

      <div className="h-px sm:h-12 sm:w-px bg-border/60 shrink-0" />

      {/* Métricas */}
      <div className="flex flex-wrap gap-6 flex-1">
        <Metric
          label="Rendimiento esperado"
          value={rendimiento != null ? `${rendimiento.toFixed(2)} t/ha` : "—"}
        />
        <Metric
          label="Prob. riesgo alto"
          value={probRiesgoAlto != null ? `${(probRiesgoAlto * 100).toFixed(0)}%` : "—"}
        />
        <Metric label="Año proyectado" value={String(anio)} />
        <Metric label="Cultivo" value={cultivo} />
      </div>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-col gap-0.5">
      <span className="text-xs text-muted-foreground uppercase tracking-wide">{label}</span>
      <span className="text-lg font-bold leading-tight">{value}</span>
    </div>
  );
}
