"use client";

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

interface Municipio {
  codigo_dane: string;
  municipio: string;
  departamento: string;
}

interface Props {
  municipios: Municipio[];
  municipio: string;
  anio: number;
  aniosDisponibles: number[];
  onMunicipioChange: (v: string) => void;
  onAnioChange: (v: number) => void;
}

export default function MunicipioSelector({
  municipios,
  municipio,
  anio,
  aniosDisponibles,
  onMunicipioChange,
  onAnioChange,
}: Props) {
  return (
    <div className="flex flex-wrap gap-4 items-end">
      <div className="flex flex-col gap-1">
        <label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
          Municipio
        </label>
        <Select value={municipio} onValueChange={onMunicipioChange} disabled={municipios.length === 0}>
          <SelectTrigger className="w-56">
            <SelectValue placeholder="Seleccionar municipio…" />
          </SelectTrigger>
          <SelectContent>
            {municipios.map((m) => (
              <SelectItem key={m.codigo_dane} value={m.codigo_dane}>
                {m.municipio}
                <span className="text-muted-foreground ml-1 text-xs">· {m.departamento}</span>
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="flex flex-col gap-1">
        <label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
          Año objetivo
        </label>
        <Select value={String(anio)} onValueChange={(v) => onAnioChange(Number(v))}>
          <SelectTrigger className="w-28">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {aniosDisponibles.map((y) => (
              <SelectItem key={y} value={String(y)}>
                {y}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
    </div>
  );
}
