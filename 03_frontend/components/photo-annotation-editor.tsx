"use client";

import { useEffect, useRef, useState, type ComponentType } from "react";
import { ArrowRight, Circle, Eraser, Image as ImageIcon, Pencil, RectangleHorizontal, Save, SquarePen, Type, X } from "lucide-react";

import { useUsuarioAtual } from "@/lib/use-usuario-atual";
import { LEGENDA_MAX_LENGTH, type StatusValidacaoIA } from "@/lib/types";
import { Badge } from "@/components/ui/badge";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";

/**
 * Contexto de legenda de uma foto já existente (BL-39; RF-15, RN-16, RN-17). Quando presente, o
 * editor mostra o estado da legenda e permite ajustar o texto, mas NUNCA aprova: a aprovação é
 * exclusiva do auditor e acontece no painel «Legenda com IA» (DEC-42).
 */
export interface LegendaContextoEditor {
  legenda: string;
  status: StatusValidacaoIA | null | undefined;
  temSugestaoIA: boolean;
}

interface PhotoAnnotationEditorProps {
  isOpen: boolean;
  imageSource: Blob | File | string | null;
  /** `legenda` só é informada quando há `legendaContexto` (foto existente). */
  onSave: (file: File, legenda?: string) => void;
  onCancel: () => void;
  legendaContexto?: LegendaContextoEditor;
}

type AnnotationTool = "arrow" | "rectangle" | "ellipse" | "text" | "pencil";

type FabricObjectLike = {
  set: (props: Record<string, unknown>) => void;
  setCoords: () => void;
};

type FabricImageLike = FabricObjectLike & {
  width?: number;
  height?: number;
};

type FabricCanvasLike = {
  setDimensions: (dimensions: { width: number; height: number }) => void;
  renderAll: () => void;
  requestRenderAll: () => void;
  getObjects: () => FabricObjectLike[];
  remove: (object: FabricObjectLike) => void;
  dispose: () => void;
  off: (eventName: string, handler: unknown) => void;
  on: (eventName: string, handler: unknown) => void;
  add: (object: FabricObjectLike) => void;
  setActiveObject: (object: FabricObjectLike) => void;
  getPointer: (event: MouseEvent) => { x: number; y: number };
  isDrawingMode: boolean;
  freeDrawingBrush?: { color: string; width: number };
  toDataURL: (options: { format: string; multiplier: number }) => string;
  setBackgroundImage: (image: FabricImageLike, callback: () => void, options: { originX: string; originY: string }) => void;
};

type FabricModuleLike = {
  Canvas: new (canvasElement: HTMLCanvasElement, options: { selection: boolean; preserveObjectStacking: boolean }) => FabricCanvasLike;
  Image: {
    /** Fabric.js v6: `fromURL` retorna uma Promise (não aceita callback como no v5). */
    fromURL: (url: string, options?: { crossOrigin?: string; signal?: AbortSignal }) => Promise<FabricImageLike>;
  };
  Textbox: new (text: string, options: Record<string, unknown>) => FabricObjectLike;
  Rect: new (options: Record<string, unknown>) => FabricObjectLike;
  Ellipse: new (options: Record<string, unknown>) => FabricObjectLike;
  Line: new (points: [number, number, number, number], options: Record<string, unknown>) => FabricObjectLike;
};

type FabricEventLike = {
  e: MouseEvent;
};

const TOOL_OPTIONS: Array<{ value: AnnotationTool; label: string; icon: ComponentType<{ className?: string }> }> = [
  { value: "arrow", label: "Seta", icon: ArrowRight },
  { value: "rectangle", label: "Retângulo", icon: RectangleHorizontal },
  { value: "ellipse", label: "Elipse", icon: Circle },
  { value: "text", label: "Texto", icon: Type },
  { value: "pencil", label: "Traço livre", icon: Pencil },
];

const COLOR_OPTIONS = ["#ef4444", "#f59e0b", "#3b82f6", "#111827", "#16a34a"];

function createImageFileFromBlob(blob: Blob, defaultName: string): File {
  return new File([blob], defaultName, { type: blob.type || "image/png" });
}

export function PhotoAnnotationEditor({ isOpen, imageSource, onSave, onCancel, legendaContexto }: PhotoAnnotationEditorProps) {
  const { isAuditor, isLoading: carregandoPerfil } = useUsuarioAtual();
  const [legendaTexto, setLegendaTexto] = useState(legendaContexto?.legenda ?? "");
  const legendaOriginal = legendaContexto?.legenda ?? "";
  const aprovada = legendaContexto?.status === "aprovada";
  const legendaAlterada = legendaTexto.trim() !== legendaOriginal.trim();

  useEffect(() => {
    if (isOpen) {
      setLegendaTexto(legendaOriginal);
    }
  }, [isOpen, legendaOriginal]);

  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const fabricCanvasRef = useRef<FabricCanvasLike | null>(null);
  const drawingStateRef = useRef<{ object: FabricObjectLike; start: { x: number; y: number } } | null>(null);
  const activeToolRef = useRef<AnnotationTool>("arrow");
  const colorRef = useRef(COLOR_OPTIONS[0]);
  const [fabricLib, setFabricLib] = useState<FabricModuleLike | null>(null);
  const [activeTool, setActiveTool] = useState<AnnotationTool>("arrow");
  const [color, setColor] = useState(COLOR_OPTIONS[0]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    activeToolRef.current = activeTool;
  }, [activeTool]);

  useEffect(() => {
    colorRef.current = color;
  }, [color]);

  useEffect(() => {
    if (!isOpen) {
      return;
    }

    let canceled = false;
    void (async () => {
      try {
        const fabricModule = await import("fabric");
        const fabric = (fabricModule as { fabric?: FabricModuleLike }).fabric ?? (fabricModule as unknown as FabricModuleLike);
        if (!canceled) {
          setFabricLib(fabric);
        }
      } catch {
        if (!canceled) {
          setError("Não foi possível carregar o editor de marcação. Tente novamente.");
          setIsLoading(false);
        }
      }
    })();

    return () => {
      canceled = true;
    };
  }, [isOpen]);

  useEffect(() => {
    if (!isOpen || !fabricLib || !canvasRef.current || !imageSource) {
      return;
    }

    let disposed = false;
    const canvasElement = canvasRef.current;

    const loadImageIntoCanvas = async () => {
      try {
        setIsLoading(true);
        setError(null);

        const canvas = new fabricLib.Canvas(canvasElement, {
          selection: false,
          preserveObjectStacking: true,
        });
        fabricCanvasRef.current = canvas;

        const imageUrl = typeof imageSource === "string" ? imageSource : URL.createObjectURL(imageSource);

        const image = await fabricLib.Image.fromURL(imageUrl, { crossOrigin: "anonymous" });
        if (!image) {
          throw new Error("Não foi possível carregar a imagem.");
        }

        if (disposed) {
          return;
        }

        const width = Math.max(320, image.width ?? 800);
        const height = Math.max(240, image.height ?? 600);
        canvas.setDimensions({ width, height });
        image.set({ left: 0, top: 0, selectable: false, evented: false });
        canvas.setBackgroundImage(image, () => {
          if (!disposed) {
            canvas.renderAll();
            setIsLoading(false);
          }
        }, { originX: "left", originY: "top" });

        const handleMouseDown = (event: FabricEventLike) => {
          if (!canvas || !fabricCanvasRef.current) {
            return;
          }
          const pointer = canvas.getPointer(event.e);

          if (activeToolRef.current === "text") {
            const textbox = new fabricLib.Textbox("Texto", {
              left: pointer.x,
              top: pointer.y,
              fontSize: 24,
              fill: colorRef.current,
              strokeWidth: 0,
              backgroundColor: "rgba(255,255,255,0.5)",
              editable: true,
              selectable: true,
            });
            canvas.add(textbox);
            canvas.setActiveObject(textbox);
            canvas.renderAll();
            return;
          }

          if (activeToolRef.current === "pencil") {
            canvas.isDrawingMode = true;
            if (canvas.freeDrawingBrush) {
              canvas.freeDrawingBrush.color = colorRef.current;
              canvas.freeDrawingBrush.width = 3;
            }
            return;
          }

          const start = { x: pointer.x, y: pointer.y };
          let object: FabricObjectLike;
          switch (activeToolRef.current) {
            case "rectangle":
              object = new fabricLib.Rect({
                left: start.x,
                top: start.y,
                width: 1,
                height: 1,
                fill: "transparent",
                stroke: colorRef.current,
                strokeWidth: 3,
                selectable: true,
              });
              break;
            case "ellipse":
              object = new fabricLib.Ellipse({
                left: start.x,
                top: start.y,
                originX: "center",
                originY: "center",
                rx: 1,
                ry: 1,
                fill: "transparent",
                stroke: colorRef.current,
                strokeWidth: 3,
                selectable: true,
              });
              break;
            case "arrow":
              object = new fabricLib.Line([start.x, start.y, start.x, start.y], {
                stroke: colorRef.current,
                strokeWidth: 3,
                fill: colorRef.current,
                selectable: true,
              });
              break;
            default:
              return;
          }

          canvas.add(object);
          canvas.setActiveObject(object);
          drawingStateRef.current = { object, start };
        };

        const handleMouseMove = (event: FabricEventLike) => {
          if (!drawingStateRef.current || !canvas) {
            return;
          }
          const pointer = canvas.getPointer(event.e);
          const { object, start } = drawingStateRef.current;
          if (activeToolRef.current === "rectangle") {
            object.set({
              width: Math.max(1, pointer.x - start.x),
              height: Math.max(1, pointer.y - start.y),
            });
          } else if (activeToolRef.current === "ellipse") {
            const rx = Math.max(1, Math.abs(pointer.x - start.x) / 2);
            const ry = Math.max(1, Math.abs(pointer.y - start.y) / 2);
            object.set({
              rx,
              ry,
              left: start.x + (pointer.x - start.x) / 2,
              top: start.y + (pointer.y - start.y) / 2,
            });
          } else if (activeToolRef.current === "arrow") {
            object.set({ x2: pointer.x, y2: pointer.y });
          }
          canvas.requestRenderAll();
        };

        const handleMouseUp = () => {
          if (drawingStateRef.current) {
            drawingStateRef.current.object.setCoords();
            drawingStateRef.current = null;
            canvas.requestRenderAll();
          }
          if (activeToolRef.current !== "pencil") {
            canvas.isDrawingMode = false;
          }
        };

        canvas.on("mouse:down", handleMouseDown as unknown);
        canvas.on("mouse:move", handleMouseMove as unknown);
        canvas.on("mouse:up", handleMouseUp as unknown);

        const cleanup = () => {
          canvas.off("mouse:down", handleMouseDown as unknown);
          canvas.off("mouse:move", handleMouseMove as unknown);
          canvas.off("mouse:up", handleMouseUp as unknown);
          canvas.dispose();
          if (typeof imageSource !== "string") {
            URL.revokeObjectURL(imageUrl);
          }
        };

        if (!disposed) {
          const currentCanvas = fabricCanvasRef.current;
          if (currentCanvas && currentCanvas !== canvas) {
            currentCanvas.dispose();
          }
          fabricCanvasRef.current = canvas;
        }

        return cleanup;
      } catch (err) {
        if (!disposed) {
          setError(err instanceof Error ? err.message : "Não foi possível abrir o editor.");
          setIsLoading(false);
        }
      }
    };

    const cleanupPromise = loadImageIntoCanvas();
    return () => {
      disposed = true;
      void cleanupPromise.then((cleanup) => cleanup?.());
    };
  }, [fabricLib, imageSource, isOpen]);

  useEffect(() => {
    if (!fabricCanvasRef.current) {
      return;
    }
    const canvas = fabricCanvasRef.current;
    if (activeToolRef.current === "pencil") {
      canvas.isDrawingMode = true;
      if (canvas.freeDrawingBrush) {
        canvas.freeDrawingBrush.color = colorRef.current;
        canvas.freeDrawingBrush.width = 3;
      }
    } else {
      canvas.isDrawingMode = false;
    }
  }, [activeTool, color]);

  const handleUndo = () => {
    const canvas = fabricCanvasRef.current;
    if (!canvas) {
      return;
    }
    const objects = canvas.getObjects();
    if (objects.length > 0) {
      const lastObject = objects[objects.length - 1];
      canvas.remove(lastObject);
      canvas.renderAll();
    }
  };

  const handleSave = async () => {
    const canvas = fabricCanvasRef.current;
    if (!canvas) {
      return;
    }

    setIsSaving(true);
    try {
      const dataUrl = canvas.toDataURL({ format: "png", multiplier: 1 });
      const response = await fetch(dataUrl);
      const blob = await response.blob();
      const annotatedFile = createImageFileFromBlob(blob, "foto-anotada.png");
      onSave(annotatedFile, legendaContexto ? legendaTexto.trim() : undefined);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao salvar a imagem anotada.");
    } finally {
      setIsSaving(false);
    }
  };

  if (!isOpen) {
    return null;
  }

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onCancel()}>
      <DialogContent className="max-w-6xl overflow-hidden p-0 sm:rounded-xl">
        <div className="flex flex-col gap-4 p-4 sm:p-6">
          <DialogHeader className="text-left">
            <DialogTitle className="flex items-center gap-2 text-lg">
              <SquarePen className="h-5 w-5" aria-hidden="true" />
              Editar e marcar foto
            </DialogTitle>
            <DialogDescription>
              Use as ferramentas abaixo para desenhar setas, formas, texto ou traço livre antes de enviar a imagem ao sistema.
            </DialogDescription>
          </DialogHeader>

          <div className="flex flex-col gap-3">
            <div className="flex flex-wrap items-center gap-2 rounded-md border border-border bg-muted/40 p-2">
              {TOOL_OPTIONS.map((tool) => {
                const Icon = tool.icon;
                const isActive = activeTool === tool.value;
                return (
                  <Button
                    key={tool.value}
                    type="button"
                    variant={isActive ? "default" : "outline"}
                    size="sm"
                    className="gap-1.5"
                    onClick={() => setActiveTool(tool.value)}
                    aria-pressed={isActive}
                  >
                    <Icon className="h-4 w-4" aria-hidden="true" />
                    {tool.label}
                  </Button>
                );
              })}
              <Button type="button" variant="outline" size="sm" className="gap-1.5" onClick={handleUndo}>
                <Eraser className="h-4 w-4" aria-hidden="true" />
                Desfazer
              </Button>
            </div>

            <div className="flex flex-wrap items-center gap-2">
              {COLOR_OPTIONS.map((option) => (
                <button
                  key={option}
                  type="button"
                  aria-label={`Selecionar cor ${option}`}
                  className={`h-7 w-7 rounded-full border-2 ${color === option ? "border-primary" : "border-transparent"}`}
                  style={{ backgroundColor: option }}
                  onClick={() => setColor(option)}
                />
              ))}
            </div>
          </div>

          <div className="relative overflow-auto rounded-lg border border-border bg-background/80 p-2">
            {/* O <canvas> precisa continuar montado mesmo durante o carregamento — o
                efeito que anexa o Fabric.Canvas depende de `canvasRef.current` já
                existir (ver useEffect abaixo). Escondê-lo via `hidden` (sem remover
                do DOM) evita o deadlock de "Preparando editor..." para sempre que
                existia quando o `<canvas>` só era renderizado após `isLoading` virar
                falso — mas nada define `isLoading = false` sem o canvas já existir. */}
            {isLoading ? (
              <div className="flex min-h-[280px] items-center justify-center rounded-md border border-dashed border-muted-foreground/30 bg-muted/20 text-sm text-muted-foreground">
                <div className="flex items-center gap-2">
                  <ImageIcon className="h-4 w-4" aria-hidden="true" />
                  Preparando editor...
                </div>
              </div>
            ) : null}
            {/* A classe de visibilidade fica no wrapper, não no <canvas> em si: o
                Fabric.js clona o className original do elemento para a camada de
                interação ("upper-canvas") apenas na inicialização — se a classe
                mudasse depois no próprio <canvas>, a upper-canvas ficaria com
                `hidden` "grudado" para sempre, quebrando os eventos de desenho. */}
            <div className={isLoading ? "hidden" : undefined}>
              <canvas ref={canvasRef} className="mx-auto max-w-full" />
            </div>
            {error ? <p className="mt-3 text-sm text-destructive">{error}</p> : null}
          </div>

          {legendaContexto ? (
            <section aria-label="Legenda da foto" className="space-y-2 rounded-md border bg-muted/30 p-3">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <Label htmlFor="anotacao-legenda">Legenda da foto</Label>
                {legendaContexto.status === "aprovada" ? (
                  <Badge>Legenda IA aprovada</Badge>
                ) : legendaContexto.status === "rascunho" ? (
                  <Badge variant="secondary">Legenda IA pendente de aprovação</Badge>
                ) : null}
              </div>
              <Textarea
                id="anotacao-legenda"
                value={legendaTexto}
                onChange={(event) => setLegendaTexto(event.target.value)}
                maxLength={LEGENDA_MAX_LENGTH}
                className="min-h-[60px] text-sm"
              />
              {aprovada && legendaAlterada ? (
                <p role="status" className="text-xs text-destructive">
                  Alterar a legenda aprovada desfaz a aprovação: ela voltará a pendente e só entra no
                  relatório depois de nova aprovação do auditor.
                </p>
              ) : null}
              {legendaContexto.temSugestaoIA ? (
                <p className="text-xs text-muted-foreground">
                  {!isAuditor && !carregandoPerfil
                    ? "A aprovação da legenda é feita pelo auditor responsável, no painel «Legenda com IA»."
                    : "Para aprovar a legenda, use o painel «Legenda com IA» da foto."}
                </p>
              ) : null}
            </section>
          ) : null}

          <DialogFooter className="flex-col-reverse sm:flex-row sm:justify-end">
            <Button type="button" variant="outline" onClick={onCancel}>
              <X className="mr-2 h-4 w-4" aria-hidden="true" />
              Cancelar
            </Button>
            <Button type="button" onClick={() => void handleSave()} disabled={isSaving}>
              <Save className="mr-2 h-4 w-4" aria-hidden="true" />
              {isSaving ? "Salvando..." : "Salvar marcação"}
            </Button>
          </DialogFooter>
        </div>
      </DialogContent>
    </Dialog>
  );
}
