import { Lightbulb } from "lucide-react";
import { cn } from "@/lib/utils";
import type { EtiquetaRiesgo } from "@/components/FichaMunicipal";

interface Props {
  texto: string;
  etiqueta: EtiquetaRiesgo;
}

const ETIQUETA_STYLE: Record<EtiquetaRiesgo, string> = {
  Bajo: "border-green-300 bg-green-50 dark:bg-green-950/30 dark:border-green-700",
  Medio: "border-amber-300 bg-amber-50 dark:bg-amber-950/30 dark:border-amber-700",
  Alto: "border-red-300 bg-red-50 dark:bg-red-950/30 dark:border-red-700",
  "Sin datos": "border-border bg-muted",
};

const ICON_STYLE: Record<EtiquetaRiesgo, string> = {
  Bajo: "text-green-600",
  Medio: "text-amber-600",
  Alto: "text-red-600",
  "Sin datos": "text-muted-foreground",
};

export default function RecomendacionCard({ texto, etiqueta }: Props) {
  return (
    <div className={cn("rounded-xl border p-5", ETIQUETA_STYLE[etiqueta])}>
      <div className="flex items-start gap-3">
        <Lightbulb className={cn("size-5 mt-0.5 shrink-0", ICON_STYLE[etiqueta])} />
        <div>
          <h2 className="text-sm font-semibold mb-1">Recomendación</h2>
          <p className="text-sm leading-relaxed">{texto}</p>
        </div>
      </div>
    </div>
  );
}
