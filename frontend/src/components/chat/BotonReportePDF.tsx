"use client";

import React, { useState } from "react";
import { FileDown, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";

interface BotonReportePDFProps {
  municipio: string;
  codigoDane: string;
  cultivo: string;
  apiBase: string;
  disabled?: boolean;
}

function normalizarNombreArchivo(texto: string): string {
  return texto
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/\s+/g, "_")
    .replace(/[^a-z0-9_]/g, "");
}

export default function BotonReportePDF({
  municipio,
  codigoDane,
  cultivo,
  apiBase,
  disabled = false,
}: BotonReportePDFProps) {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const isMissingContext = !codigoDane || !cultivo;
  const isDisabled = disabled || isMissingContext;

  const handleDownload = async () => {
    if (isDisabled || isLoading) return;

    setIsLoading(true);
    setError(null);

    try {
      const res = await fetch(`${apiBase}/reporte/${codigoDane}/${encodeURIComponent(cultivo)}?formato=pdf`);

      if (!res.ok) {
        if (res.status === 404) {
          throw new Error(`No hay reporte disponible para ${municipio}/${cultivo}.`);
        } else if (res.status >= 500) {
          throw new Error("Error al generar el reporte. Intenta de nuevo.");
        } else {
          throw new Error("Error de conexión. Verifica que la API esté disponible.");
        }
      }

      const contentType = res.headers.get("Content-Type");
      if (contentType !== "application/pdf") {
        throw new Error("El servidor no retornó un PDF válido.");
      }

      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      
      const fecha = new Date().toISOString().split("T")[0];
      const muniNorm = normalizarNombreArchivo(municipio || codigoDane);
      const cultivoNorm = normalizarNombreArchivo(cultivo);
      
      const a = document.createElement("a");
      a.href = url;
      a.download = `reporte_${muniNorm}_${cultivoNorm}_${fecha}.pdf`;
      document.body.appendChild(a);
      a.click();
      
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err: any) {
      setError(err.message || "Ocurrió un error inesperado.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col border border-border rounded-xl bg-card p-5">
      <div className="flex items-center gap-2 mb-2">
        <FileDown className="size-5 text-primary" />
        <h3 className="font-semibold text-base">Reporte institucional</h3>
      </div>
      <div className="text-sm text-muted-foreground mb-5">
        Descarga el reporte completo en PDF para{" "}
        {codigoDane && cultivo ? (
          <span className="font-medium text-foreground">{municipio} · {cultivo}</span>
        ) : (
          "el municipio y cultivo seleccionados"
        )}
      </div>

      <Button
        onClick={handleDownload}
        disabled={isDisabled || isLoading}
        className="w-full gap-2 transition-all"
        title={isDisabled ? "Selecciona municipio y cultivo" : "Descargar reporte institucional en PDF"}
      >
        {isLoading ? (
          <>
            <Loader2 className="size-4 animate-spin" />
            Generando...
          </>
        ) : (
          <>
            <FileDown className="size-4" />
            Generar reporte PDF
          </>
        )}
      </Button>

      {error && (
        <div className="mt-3 text-xs text-destructive bg-destructive/10 border border-destructive/20 p-2 rounded-md">
          {error}
        </div>
      )}
    </div>
  );
}
