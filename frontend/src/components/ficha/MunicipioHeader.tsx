import { MapPin } from "lucide-react";

interface Props {
  municipio: string;
  departamento: string;
  cultivo: string;
  anio: number;
}

export default function MunicipioHeader({ municipio, departamento, cultivo, anio }: Props) {
  return (
    <div className="flex items-center gap-2 min-w-0">
      <MapPin className="size-4 text-primary shrink-0" />
      <div className="min-w-0">
        <h1 className="text-base font-bold leading-tight truncate">
          {municipio}
          {departamento && (
            <span className="font-normal text-muted-foreground"> · {departamento}</span>
          )}
        </h1>
        <p className="text-xs text-muted-foreground leading-none">
          {cultivo} · {anio}
        </p>
      </div>
    </div>
  );
}
