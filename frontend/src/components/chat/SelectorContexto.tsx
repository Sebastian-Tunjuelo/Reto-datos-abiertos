"use client";

import React, { useEffect, useState } from "react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { AlertTriangle } from "lucide-react";

interface Municipio {
  codigo_dane: string;
  municipio: string;
  departamento: string;
}

interface SelectorContextoProps {
  municipio: string;
  cultivo: string;
  tono: "campesino" | "institucional";
  onMunicipioChange: (municipio: string, codigoDane: string) => void;
  onCultivoChange: (cultivo: string) => void;
  onTonoChange: (tono: "campesino" | "institucional") => void;
  disabled?: boolean;
}

export default function SelectorContexto({
  municipio,
  cultivo,
  tono,
  onMunicipioChange,
  onCultivoChange,
  onTonoChange,
  disabled = false,
}: SelectorContextoProps) {
  const [municipios, setMunicipios] = useState<Municipio[]>([]);
  const [cultivos, setCultivos] = useState<string[]>([]);
  const [errorMunicipios, setErrorMunicipios] = useState(false);

  const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL ?? "";
  const selectedMunicipio = municipios.find(
    (m) => m.codigo_dane === municipio || m.municipio === municipio,
  );
  const municipioVisible = selectedMunicipio?.municipio ?? municipio;

  // Cargar municipios al montar
  useEffect(() => {
    if (!apiBase) return;

    fetch(`${apiBase}/municipios`)
      .then((res) => {
        if (!res.ok) throw new Error("Error loading municipios");
        return res.json();
      })
      .then((data) => {
        // El API devuelve un array directo o un objeto con clave 'municipios'
        const lista = Array.isArray(data) ? data : (data.municipios ?? []);
        if (lista.length > 0) {
          setMunicipios(lista);
        }
      })
      .catch(() => {
        setErrorMunicipios(true);
      });
  }, [apiBase]);

  // Cargar cultivos cuando cambia el municipio seleccionado (usamos el código DANE para la llamada o el nombre)
  // Pero necesitamos el codigoDane. Lo buscaremos en la lista.
  useEffect(() => {
    if (!apiBase || !municipio) return;

    const codigoDane = selectedMunicipio
      ? selectedMunicipio.codigo_dane
      : municipio;

    fetch(`${apiBase}/cultivos/${codigoDane}`)
      .then((res) => {
        if (!res.ok) throw new Error("Error loading cultivos");
        return res.json();
      })
      .then((data) => {
        if (data.cultivos && data.cultivos.length > 0) {
          setCultivos(data.cultivos);
        } else {
          setCultivos(["Café", "Cacao", "Maíz"]);
        }
      })
      .catch(() => {
        setCultivos(["Café", "Cacao", "Maíz"]);
      });
  }, [apiBase, municipio, municipios, selectedMunicipio]);

  useEffect(() => {
    if (!selectedMunicipio) return;
    if (municipio !== selectedMunicipio.municipio) {
      onMunicipioChange(
        selectedMunicipio.municipio,
        selectedMunicipio.codigo_dane,
      );
    }
  }, [municipio, onMunicipioChange, selectedMunicipio]);

  if (!apiBase) {
    return (
      <div className="rounded-lg border border-amber-400/40 bg-amber-50 dark:bg-amber-950/30 px-4 py-3 text-sm text-amber-700 dark:text-amber-400 flex items-center gap-2 mb-4">
        <AlertTriangle className="size-4 shrink-0" />
        <span>
          API no configurada. Configura NEXT_PUBLIC_API_BASE_URL en .env.local
        </span>
      </div>
    );
  }

  const handleMunicipioChange = (val: string) => {
    const selectedMuni = municipios.find((m) => m.municipio === val);
    if (selectedMuni) {
      onMunicipioChange(selectedMuni.municipio, selectedMuni.codigo_dane);
    }
  };

  return (
    <div className="flex flex-col sm:flex-row gap-4 w-full">
      <div className="flex-1 space-y-1">
        <label className="text-xs font-medium text-muted-foreground">
          Municipio
        </label>
        <Select
          value={municipioVisible}
          onValueChange={handleMunicipioChange}
          disabled={disabled || municipios.length === 0}
        >
          <SelectTrigger className="w-full">
            <SelectValue
              placeholder={
                errorMunicipios
                  ? "No se pudieron cargar los municipios"
                  : "Selecciona un municipio"
              }
            />
          </SelectTrigger>
          <SelectContent>
            {municipios.map((m) => (
              <SelectItem key={m.codigo_dane} value={m.municipio}>
                {m.municipio} ({m.departamento})
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="flex-1 space-y-1">
        <label className="text-xs font-medium text-muted-foreground">
          Cultivo
        </label>
        <Select
          value={cultivo}
          onValueChange={onCultivoChange}
          disabled={disabled || !municipio || cultivos.length === 0}
        >
          <SelectTrigger className="w-full">
            <SelectValue placeholder="Selecciona un cultivo" />
          </SelectTrigger>
          <SelectContent>
            {cultivos.map((c) => (
              <SelectItem key={c} value={c}>
                {c}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="flex-1 space-y-1">
        <label className="text-xs font-medium text-muted-foreground">
          Tono de respuesta
        </label>
        <Select
          value={tono}
          onValueChange={(val: "campesino" | "institucional") =>
            onTonoChange(val)
          }
          disabled={disabled}
        >
          <SelectTrigger className="w-full">
            <SelectValue placeholder="Selecciona tono" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="campesino">Lenguaje campesino</SelectItem>
            <SelectItem value="institucional">Institucional (UMATA)</SelectItem>
          </SelectContent>
        </Select>
      </div>
    </div>
  );
}
