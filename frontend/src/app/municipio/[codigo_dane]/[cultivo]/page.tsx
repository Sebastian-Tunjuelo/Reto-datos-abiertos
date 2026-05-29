import { Suspense } from "react";
import FichaMunicipal from "@/components/FichaMunicipal";

interface PageProps {
  params: { codigo_dane: string; cultivo: string };
  searchParams: { anio?: string };
}

export default function MunicipioPage({ params, searchParams }: PageProps) {
  const { codigo_dane, cultivo } = params;
  const anioParam = searchParams.anio ? Number(searchParams.anio) : undefined;

  return (
    <Suspense
      fallback={
        <div className="flex h-screen items-center justify-center text-muted-foreground animate-pulse">
          Cargando ficha…
        </div>
      }
    >
      <FichaMunicipal
        codigo_dane={decodeURIComponent(codigo_dane)}
        cultivo={decodeURIComponent(cultivo)}
        anioParam={anioParam}
      />
    </Suspense>
  );
}
