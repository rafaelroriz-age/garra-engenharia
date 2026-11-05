"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Clipboard, GripVertical, ImageUp, Loader2, Sparkles, Trash2 } from "lucide-react";

import { api, ApiError } from "@/lib/api-client";
import type { Foto, FotoUploadResult, OrigemFoto } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ApiErrorAlert } from "@/components/api-error-alert";
import { PhotoAnnotationEditor } from "@/components/photo-annotation-editor";
import { LegendaIAPainel } from "@/components/legenda-ia-painel";
import { useUsuarioAtual } from "@/lib/use-usuario-atual";

const MAX_FILE_SIZE_BYTES = 15 * 1024 * 1024; // 15MB — alinhado ao limite validado no backend (BL-11)
const ACCEPTED_MIME_TYPES = ["image/png", "image/jpeg", "image/webp"];

interface FotoUploadProps {
  /** Vincula as fotos a uma Visita de fiscalização (`POST /visitas/{id}/fotos`, RF-05, BL-11). */
  visitaId?: string;
  /** Vincula as fotos a uma Ocorrência do LTIP (`POST /ocorrencias/{id}/fotos`, RF-04, RN-03, BL-14). */
  ocorrenciaId?: string | null;
  fotos: Foto[];
  onChange: (fotos: Foto[]) => void;
}

function validateFile(file: File): string | null {
  if (!ACCEPTED_MIME_TYPES.includes(file.type)) {
    return "Formato de imagem não suportado. Envie um arquivo PNG, JPEG ou WEBP.";
  }
  if (file.size > MAX_FILE_SIZE_BYTES) {
    return "Arquivo maior que o limite de 15MB por foto.";
  }
  return null;
}

/**
 * Componente reutilizável de upload de fotos (BL-11, RF-05; reaproveitado pela
 * BL-14 para Ocorrências do LTIP, ver RN-03):
 * - "Colar da área de transferência" — captura Lightshot via `navigator.clipboard.read()`
 *   e envia como base64 (`POST /fotos/upload-clipboard`), Opção A da Seção 6.
 * - "Enviar arquivo" — upload manual multipart, com suporte a múltiplos arquivos e
 *   drag-and-drop (`POST /fotos/upload`), Opção B da Seção 6.
 *
 * Após o upload bruto, a foto é vinculada à Visita (`POST /visitas/{id}/fotos`)
 * ou à Ocorrência (`POST /ocorrencias/{id}/fotos`), conforme a prop informada.
 * Validação de mime-type/tamanho e reprocessamento da imagem (Pillow) são
 * responsabilidade do backend (A08 OWASP) — aqui apenas pré-validamos no cliente
 * para dar feedback rápido ao usuário.
 */
export function FotoUpload({ visitaId, ocorrenciaId, fotos, onChange }: FotoUploadProps) {
  const [isUploading, setIsUploading] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const [error, setError] = useState<ApiError | Error | null>(null);
  const [clipboardUnsupported, setClipboardUnsupported] = useState(false);
  const [annotationState, setAnnotationState] = useState<{ isOpen: boolean; source: Blob | File | null; origin: "upload" | "clipboard" | null }>({
    isOpen: false,
    source: null,
    origin: null,
  });
  const fileInputRef = useRef<HTMLInputElement>(null);
  const fotosRef = useRef(fotos);
  // Legenda por IA (BL-35, RF-15): só a equipe (auditor/auxiliar) gera e aprova, como no backend
  // (`require_equipe`). Enquanto o perfil carrega, o painel fica oculto (ver `useUsuarioAtual`).
  const { isAuditor, isAuxiliar } = useUsuarioAtual();
  const podeUsarLegendaIA = isAuditor || isAuxiliar;
  const [fotoLegendaIAId, setFotoLegendaIAId] = useState<string | null>(null);

  useEffect(() => {
    fotosRef.current = fotos;
  }, [fotos]);

  const targetId = ocorrenciaId ?? visitaId;
  const linkEndpoint = ocorrenciaId ? `/ocorrencias/${ocorrenciaId}/fotos` : `/visitas/${visitaId}/fotos`;

  const linkFoto = useCallback(
    async (upload: FotoUploadResult, origem: OrigemFoto) => {
      const foto = await api.post<Foto>(linkEndpoint, {
        storage_key: upload.storage_key,
        url_publica: upload.url,
        legenda: "",
        origem,
      });
      const nextFotos = [...fotosRef.current, foto];
      fotosRef.current = nextFotos;
      onChange(nextFotos);
    },
    [onChange, linkEndpoint]
  );

  const uploadAnnotatedFile = useCallback(
    async (file: File, origin: "upload" | "clipboard") => {
      setError(null);
      setIsUploading(true);
      try {
        const formData = new FormData();
        formData.append("arquivo", file);
        const upload = await api.post<FotoUploadResult>("/fotos/upload", formData, { raw: true });
        // Origem do editor → valor aceito pelo backend. Clipboard = captura Lightshot (integração da Opção A).
        const origemBackend: OrigemFoto = origin === "clipboard" ? "lightshot" : "upload_manual";
        await linkFoto(upload, origemBackend);
      } catch (err) {
        setError(err instanceof Error ? err : new Error("Falha ao enviar arquivo."));
      } finally {
        setIsUploading(false);
      }
    },
    [linkFoto]
  );

  const openAnnotationEditor = useCallback((source: Blob | File, origin: "upload" | "clipboard") => {
    setAnnotationState({ isOpen: true, source, origin });
  }, []);

  const uploadFiles = useCallback(
    async (files: FileList | File[]) => {
      setError(null);
      const fileArray = Array.from(files);
      for (const file of fileArray) {
        const validationError = validateFile(file);
        if (validationError) {
          setError(new Error(validationError));
          continue;
        }
        openAnnotationEditor(file, "upload");
        return;
      }
    },
    [openAnnotationEditor]
  );

  const handleClipboardPaste = useCallback(async () => {
    setError(null);
    if (typeof window !== "undefined" && !window.isSecureContext) {
      setClipboardUnsupported(true);
      return;
    }
    if (!navigator.clipboard || !("read" in navigator.clipboard)) {
      setClipboardUnsupported(true);
      return;
    }
    setIsUploading(true);
    try {
      const clipboardItems = await navigator.clipboard.read();
      const imageItem = clipboardItems.find((item) =>
        item.types.some((type) => ACCEPTED_MIME_TYPES.includes(type))
      );
      if (!imageItem) {
        setError(new Error("Nenhuma imagem encontrada na área de transferência. Capture a tela com o Lightshot e tente novamente."));
        return;
      }
      const mimetype = imageItem.types.find((type) => ACCEPTED_MIME_TYPES.includes(type))!;
      const blob = await imageItem.getType(mimetype);
      if (blob.size > MAX_FILE_SIZE_BYTES) {
        setError(new Error("Imagem colada maior que o limite de 15MB."));
        return;
      }
      openAnnotationEditor(blob, "clipboard");
    } catch (err) {
      if (err instanceof DOMException && (err.name === "NotAllowedError" || err.name === "SecurityError")) {
        setClipboardUnsupported(true);
      } else {
        setError(err instanceof Error ? err : new Error("Falha ao colar imagem da área de transferência."));
      }
    } finally {
      setIsUploading(false);
    }
  }, [openAnnotationEditor]);

  const handleDrop = useCallback(
    (event: React.DragEvent<HTMLDivElement>) => {
      event.preventDefault();
      setIsDragging(false);
      if (event.dataTransfer.files?.length) {
        void uploadFiles(event.dataTransfer.files);
      }
    },
    [uploadFiles]
  );

  const updateLegenda = useCallback(
    async (foto: Foto, legenda: string) => {
      try {
        const updated = await api.put<Foto>(`/fotos/${foto.id}`, { legenda });
        const nextFotos = fotosRef.current.map((item) => (item.id === foto.id ? updated : item));
        fotosRef.current = nextFotos;
        onChange(nextFotos);
      } catch (err) {
        setError(err instanceof Error ? err : new Error("Falha ao atualizar legenda."));
      }
    },
    [onChange]
  );

  const substituirFoto = useCallback(
    (updated: Foto) => {
      const nextFotos = fotosRef.current.map((item) => (item.id === updated.id ? updated : item));
      fotosRef.current = nextFotos;
      onChange(nextFotos);
    },
    [onChange]
  );

  const removeFoto = useCallback(
    async (foto: Foto) => {
      try {
        await api.delete(`/fotos/${foto.id}`);
        const nextFotos = fotosRef.current.filter((item) => item.id !== foto.id);
        fotosRef.current = nextFotos;
        onChange(nextFotos);
      } catch (err) {
        setError(err instanceof Error ? err : new Error("Falha ao remover foto."));
      }
    },
    [onChange]
  );

  const moveFoto = useCallback(
    async (index: number, direction: -1 | 1) => {
      const targetIndex = index + direction;
      if (targetIndex < 0 || targetIndex >= fotosRef.current.length) return;
      const reordered = [...fotosRef.current];
      [reordered[index], reordered[targetIndex]] = [reordered[targetIndex], reordered[index]];
      fotosRef.current = reordered;
      onChange(reordered);
      try {
        await Promise.all(
          reordered.map((foto, ordem) => api.put<Foto>(`/fotos/${foto.id}`, { ordem }))
        );
      } catch (err) {
        setError(err instanceof Error ? err : new Error("Falha ao reordenar fotos."));
      }
    },
    [onChange]
  );

  const fotoLegendaIA = podeUsarLegendaIA ? fotos.find((item) => item.id === fotoLegendaIAId) : undefined;

  if (!targetId) {
    return (
      <p className="rounded-md border border-dashed p-3 text-sm text-muted-foreground">
        Salve o registro para anexar fotos. Ao menos uma foto é exigida antes da emissão do
        relatório para ocorrências Não Conformes (RN-03).
      </p>
    );
  }

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap gap-2">
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={handleClipboardPaste}
          disabled={isUploading}
          className="gap-1.5"
        >
          {isUploading ? (
            <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
          ) : (
            <Clipboard className="h-4 w-4" aria-hidden="true" />
          )}
          Colar da área de transferência
        </Button>
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={() => fileInputRef.current?.click()}
          disabled={isUploading}
          className="gap-1.5"
        >
          <ImageUp className="h-4 w-4" aria-hidden="true" />
          Enviar arquivo
        </Button>
        <Input
          ref={fileInputRef}
          type="file"
          accept="image/png,image/jpeg,image/webp"
          multiple
          className="hidden"
          aria-label="Selecionar arquivos de imagem para upload"
          onChange={(event) => {
            if (event.target.files?.length) {
              void uploadFiles(event.target.files);
            }
            event.target.value = "";
          }}
        />
      </div>

      {clipboardUnsupported ? (
        <p className="text-xs text-muted-foreground">
          Este navegador ou contexto não suporta colar da área de transferência (é necessário
          HTTPS). Use o botão &quot;Enviar arquivo&quot; para fazer upload manual da captura do
          Lightshot.
        </p>
      ) : null}

      <div
        onDragOver={(event) => {
          event.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        className={`rounded-md border border-dashed p-4 text-center text-xs text-muted-foreground transition-colors ${
          isDragging ? "border-primary bg-accent" : "border-input"
        }`}
      >
        Arraste e solte imagens aqui, ou use os botões acima.
      </div>

      <ApiErrorAlert error={error} />

      <PhotoAnnotationEditor
        isOpen={annotationState.isOpen}
        imageSource={annotationState.source}
        onSave={(file) => {
          setAnnotationState({ isOpen: false, source: null, origin: null });
          void uploadAnnotatedFile(file, annotationState.origin ?? "upload");
        }}
        onCancel={() => {
          setAnnotationState({ isOpen: false, source: null, origin: null });
        }}
      />

      {fotos.length > 0 ? (
        <ul className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4">
          {fotos
            .slice()
            .sort((a, b) => (a.ordem ?? 0) - (b.ordem ?? 0))
            .map((foto, index) => (
              <li key={foto.id} className="space-y-1.5 rounded-md border p-2">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={foto.url_publica ?? undefined}
                  alt={foto.legenda || "Foto vinculada à visita"}
                  className="h-24 w-full rounded object-cover"
                />
                <label className="sr-only" htmlFor={`legenda-${foto.id}`}>
                  Legenda da foto
                </label>
                <Input
                  key={`legenda-${foto.id}-${foto.legenda ?? ""}`}
                  id={`legenda-${foto.id}`}
                  defaultValue={foto.legenda ?? ""}
                  placeholder="Legenda técnica"
                  className="h-7 text-xs"
                  onBlur={(event) => {
                    if (event.target.value !== (foto.legenda ?? "")) {
                      void updateLegenda(foto, event.target.value);
                    }
                  }}
                />
                <div className="flex items-center justify-between">
                  <div className="flex gap-0.5">
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon"
                      className="h-6 w-6"
                      onClick={() => void moveFoto(index, -1)}
                      disabled={index === 0}
                      aria-label="Mover foto para cima na ordem"
                    >
                      <GripVertical className="h-3.5 w-3.5 rotate-90" aria-hidden="true" />
                    </Button>
                  </div>
                  {podeUsarLegendaIA ? (
                    <Button
                      type="button"
                      variant={fotoLegendaIAId === foto.id ? "secondary" : "ghost"}
                      size="icon"
                      className="h-6 w-6"
                      onClick={() => setFotoLegendaIAId((atual) => (atual === foto.id ? null : foto.id))}
                      aria-label="Legenda com IA"
                      aria-pressed={fotoLegendaIAId === foto.id}
                      title="Legenda com IA"
                    >
                      <Sparkles className="h-3.5 w-3.5" aria-hidden="true" />
                    </Button>
                  ) : null}
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    className="h-6 w-6 text-destructive hover:text-destructive"
                    onClick={() => void removeFoto(foto)}
                    aria-label="Remover foto"
                  >
                    <Trash2 className="h-3.5 w-3.5" aria-hidden="true" />
                  </Button>
                </div>
              </li>
            ))}
        </ul>
      ) : (
        <p className="text-xs text-muted-foreground">Nenhuma foto vinculada ainda.</p>
      )}

      {fotoLegendaIA ? <LegendaIAPainel foto={fotoLegendaIA} onFotoAtualizada={substituirFoto} /> : null}
    </div>
  );
}
