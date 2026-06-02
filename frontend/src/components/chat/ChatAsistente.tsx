"use client";

import React, { useState, useRef, useEffect } from "react";
import { Send, User, Bot, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";

interface Mensaje {
  id: string;
  role: "user" | "assistant";
  content: string;
  fuentes?: string[];
  tokensUsados?: number;
  proveedorLlm?: string;
  timestamp: Date;
  isError?: boolean;
}

interface ChatAsistenteProps {
  municipio: string;
  codigoDane: string;
  cultivo: string;
  tono: "campesino" | "institucional";
  anio?: number;
  apiBase: string;
}

export default function ChatAsistente({
  municipio,
  codigoDane,
  cultivo,
  tono,
  anio,
  apiBase,
}: ChatAsistenteProps) {
  const [mensajes, setMensajes] = useState<Mensaje[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const endOfMessagesRef = useRef<HTMLDivElement>(null);

  const contextSelected = Boolean(municipio && codigoDane && cultivo);

  const scrollToBottom = () => {
    endOfMessagesRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [mensajes, isLoading]);

  const handleSend = async () => {
    if (!input.trim() || !contextSelected || isLoading) return;

    const userMsg: Mensaje = {
      id: crypto.randomUUID(),
      role: "user",
      content: input.trim(),
      timestamp: new Date(),
    };

    setMensajes((prev) => [...prev, userMsg]);
    setInput("");
    setIsLoading(true);

    try {
      const currentYear = anio || new Date().getFullYear();
      const res = await fetch(`${apiBase}/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          pregunta: userMsg.content,
          municipio: codigoDane,
          cultivo,
          año: currentYear,
          tono,
        }),
      });

      if (!res.ok) {
        throw new Error("Error en la respuesta de la API");
      }

      const data = await res.json();
      const assistantMsg: Mensaje = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: data.respuesta,
        fuentes: data.fuentes,
        tokensUsados: data.tokens_usados,
        proveedorLlm: data.proveedor_llm,
        timestamp: new Date(),
      };
      setMensajes((prev) => [...prev, assistantMsg]);
    } catch (error) {
      const errorMsg: Mensaje = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: "Lo siento, no pude procesar tu pregunta. Intenta de nuevo.",
        timestamp: new Date(),
        isError: true,
      };
      setMensajes((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleClear = () => {
    setMensajes([]);
  };

  return (
    <div className="flex flex-col h-[500px] sm:h-[600px] border border-border rounded-xl bg-card overflow-hidden">
      {/* Header del chat */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-border bg-muted/40">
        <div className="flex items-center gap-2">
          <Bot className="size-5 text-primary" />
          <h2 className="font-semibold text-sm">Asistente IA</h2>
        </div>
        <Button variant="ghost" size="sm" onClick={handleClear} className="h-8 text-xs text-muted-foreground hover:text-foreground">
          Limpiar conversación
        </Button>
      </div>

      {/* Historial de mensajes */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {mensajes.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center space-y-3 text-muted-foreground">
            <Bot className="size-10 text-muted-foreground/50" />
            <div className="max-w-[300px] text-sm">
              <p>Hola. Soy el asistente de SiembraSegura IA.</p>
              {contextSelected ? (
                <p className="mt-2">Puedes preguntarme sobre el riesgo agrícola, rendimiento esperado o recomendaciones para {municipio} · {cultivo}.</p>
              ) : (
                <p className="mt-2">Selecciona un municipio y cultivo para comenzar.</p>
              )}
            </div>
          </div>
        ) : (
          mensajes.map((msg) => (
            <div key={msg.id} className={`flex gap-3 ${msg.role === "user" ? "flex-row-reverse" : "flex-row"}`}>
              <div className={`flex items-center justify-center size-8 rounded-full shrink-0 ${msg.role === "user" ? "bg-primary text-primary-foreground" : "bg-muted"}`}>
                {msg.role === "user" ? <User className="size-4" /> : <Bot className="size-4" />}
              </div>
              <div className={`flex flex-col max-w-[80%] ${msg.role === "user" ? "items-end" : "items-start"}`}>
                <div
                  className={`rounded-2xl px-4 py-2.5 text-sm whitespace-pre-wrap shadow-sm
                    ${msg.role === "user" 
                      ? "bg-primary text-primary-foreground rounded-tr-sm" 
                      : msg.isError
                        ? "bg-destructive/10 text-destructive border border-destructive/20 rounded-tl-sm"
                        : "bg-muted/50 border border-border rounded-tl-sm"
                    }`}
                >
                  {msg.content}
                </div>
                {msg.role === "assistant" && msg.fuentes && msg.fuentes.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-1">
                    {msg.fuentes.map((fuente, i) => (
                      <Badge key={i} variant="outline" className="text-[10px] text-muted-foreground bg-background">
                        {fuente}
                      </Badge>
                    ))}
                  </div>
                )}
                {msg.role === "assistant" && !msg.isError && (msg.tokensUsados !== undefined || msg.proveedorLlm) && (
                  <div className="mt-1 flex flex-wrap gap-1 items-center">
                    {msg.proveedorLlm && (
                      <Badge variant="outline" className="text-[10px] text-primary/70 bg-primary/5 border-primary/20 gap-1">
                        <span className="size-1.5 rounded-full bg-primary/50 inline-block" />
                        {msg.proveedorLlm}
                      </Badge>
                    )}
                    {msg.tokensUsados !== undefined && msg.tokensUsados > 0 && (
                      <Badge variant="outline" className="text-[10px] text-muted-foreground bg-background border-border/60">
                        {msg.tokensUsados.toLocaleString()} tokens
                      </Badge>
                    )}
                    {msg.tokensUsados === 0 && (
                      <Badge variant="outline" className="text-[10px] text-muted-foreground bg-background border-border/60">
                        RAG local
                      </Badge>
                    )}
                  </div>
                )}
              </div>
            </div>
          ))
        )}
        
        {isLoading && (
          <div className="flex gap-3 flex-row">
            <div className="flex items-center justify-center size-8 rounded-full shrink-0 bg-muted">
              <Bot className="size-4" />
            </div>
            <div className="flex items-center bg-muted/50 border border-border rounded-2xl rounded-tl-sm px-4 py-3">
              <div className="flex gap-1">
                <span className="size-1.5 rounded-full bg-muted-foreground/60 animate-bounce" style={{ animationDelay: "0ms" }} />
                <span className="size-1.5 rounded-full bg-muted-foreground/60 animate-bounce" style={{ animationDelay: "150ms" }} />
                <span className="size-1.5 rounded-full bg-muted-foreground/60 animate-bounce" style={{ animationDelay: "300ms" }} />
              </div>
            </div>
          </div>
        )}
        <div ref={endOfMessagesRef} />
      </div>

      {/* Input */}
      <div className="p-3 bg-background border-t border-border">
        <div className="relative flex items-center">
          <Textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={contextSelected ? "Escribe tu pregunta..." : "Selecciona municipio y cultivo para comenzar"}
            disabled={!contextSelected || isLoading}
            className="min-h-[52px] max-h-[150px] pr-12 py-3 resize-none bg-muted/30 border-transparent focus-visible:bg-background focus-visible:ring-1 focus-visible:border-border"
            rows={1}
            aria-label="Mensaje para el asistente"
          />
          <Button
            size="icon"
            onClick={handleSend}
            disabled={!input.trim() || !contextSelected || isLoading}
            className="absolute right-2 bottom-1.5 size-8 rounded-lg"
          >
            {isLoading ? <Loader2 className="size-4 animate-spin" /> : <Send className="size-4" />}
          </Button>
        </div>
        <div className="text-[10px] text-center text-muted-foreground mt-2">
          La IA puede cometer errores. Verifica la información.
        </div>
      </div>
    </div>
  );
}
