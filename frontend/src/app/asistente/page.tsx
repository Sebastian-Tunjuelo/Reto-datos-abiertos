"use client";

import React, { useState, Suspense } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { ArrowLeft, MessageSquare } from "lucide-react";
import { Button } from "@/components/ui/button";

import SelectorContexto from "@/components/chat/SelectorContexto";
import ChatAsistente from "@/components/chat/ChatAsistente";
import BotonReportePDF from "@/components/chat/BotonReportePDF";

function AsistenteContent() {
  const searchParams = useSearchParams();
  const initMunicipio = searchParams.get("municipio") || "";
  const initCultivo = searchParams.get("cultivo") || "";

  // The state will hold the Display Name for municipio, and we also need codigoDane.
  // The SelectorContexto will figure out the display name and DANE code based on its fetched data.
  const [municipio, setMunicipio] = useState<string>(
    initMunicipio.length === 5 ? "" : initMunicipio
  );
  // We need to keep codigoDane around. If initMunicipio is 5 digits, it's a DANE code.
  const [codigoDane, setCodigoDane] = useState<string>(
    initMunicipio.length === 5 ? initMunicipio : ""
  );
  const [cultivo, setCultivo] = useState<string>(initCultivo);
  const [tono, setTono] = useState<"campesino" | "institucional">("campesino");

  const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL ?? "";

  // Helper inside to handle initial sync when the Selector components load data.
  // But our SelectorContexto handles preselecting if `municipio` prop is set.
  // If `initMunicipio` was a DANE code, we pass it down and the selector could find it.
  // We will pass the `municipio` or `codigoDane` down.
  // For simplicity, we just pass the initialized ones to SelectorContexto. 
  // It handles changes via `onMunicipioChange`.

  return (
    <div className="max-w-7xl mx-auto px-4 py-6">
      <div className="mb-6 p-4 rounded-xl bg-card border border-border shadow-sm">
        <SelectorContexto
          municipio={municipio || codigoDane} // Passes whatever we have. Selector handles finding it.
          cultivo={cultivo}
          tono={tono}
          onMunicipioChange={(m, code) => {
            setMunicipio(m);
            setCodigoDane(code);
          }}
          onCultivoChange={setCultivo}
          onTonoChange={setTono}
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="md:col-span-2">
          <ChatAsistente
            municipio={municipio}
            codigoDane={codigoDane}
            cultivo={cultivo}
            tono={tono}
            apiBase={apiBase}
          />
        </div>
        <div className="md:col-span-1">
          <BotonReportePDF
            municipio={municipio}
            codigoDane={codigoDane}
            cultivo={cultivo}
            apiBase={apiBase}
          />
        </div>
      </div>
    </div>
  );
}

export default function AsistentePage() {
  return (
    <main className="min-h-screen bg-background">
      <header className="px-6 py-4 border-b border-border/60 bg-card/70 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto flex items-center gap-3">
          <Link href="/">
            <Button variant="ghost" size="sm" className="gap-1.5">
              <ArrowLeft className="size-4" />
              Mapa
            </Button>
          </Link>
          <div className="h-5 w-px bg-border" />
          <div className="flex items-center gap-2">
            <MessageSquare className="size-5 text-primary" />
            <h1 className="text-xl font-bold leading-tight tracking-tight">
              Asistente IA
            </h1>
          </div>
        </div>
      </header>
      <Suspense fallback={
        <div className="flex h-[80vh] items-center justify-center text-muted-foreground text-sm animate-pulse">
          Cargando asistente…
        </div>
      }>
        <AsistenteContent />
      </Suspense>
    </main>
  );
}
