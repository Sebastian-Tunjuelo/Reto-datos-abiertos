import { Suspense } from "react";
import ComparadorCultivos from "@/components/ComparadorCultivos";

interface PageProps {
  searchParams: { municipio?: string; anio?: string };
}

export default function ComparadorPage({ searchParams }: PageProps) {
  const municipio = searchParams.municipio ?? "";
  const anio = searchParams.anio ? Number(searchParams.anio) : 2025;

  return (
    <Suspense
      fallback={
        <div className="flex h-screen items-center justify-center text-muted-foreground animate-pulse">
          Cargando comparador…
        </div>
      }
    >
      <ComparadorCultivos municipioParam={municipio} anioParam={anio} />
    </Suspense>
  );
}
