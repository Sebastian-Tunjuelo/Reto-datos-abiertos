import dynamic from "next/dynamic";
import Link from "next/link";
import { Sprout, BarChart3 } from "lucide-react";

const MapaColombia = dynamic(() => import("../components/MapaColombia"), {
  ssr: false,
  loading: () => (
    <div className="flex h-[80vh] items-center justify-center text-muted-foreground text-sm animate-pulse">
      Cargando mapa…
    </div>
  ),
});

export default function Home() {
  return (
    <main className="min-h-screen">
      <header className="px-6 py-4 border-b border-border/60 bg-card/70 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto flex items-center gap-3">
          <Sprout className="text-primary size-6 shrink-0" />
          <div className="flex-1">
            <h1 className="text-xl font-bold leading-tight tracking-tight">
              SiembraSegura IA
            </h1>
            <p className="text-xs text-muted-foreground leading-none">
              Riesgo agrícola por municipio · Colombia
            </p>
          </div>
          <Link
            href="/comparador"
            className="flex items-center gap-1.5 text-sm text-primary hover:underline underline-offset-2"
          >
            <BarChart3 className="size-4" />
            Comparador
          </Link>
        </div>
      </header>
      <section className="max-w-7xl mx-auto px-4 py-6">
        <MapaColombia />
      </section>
    </main>
  );
}
