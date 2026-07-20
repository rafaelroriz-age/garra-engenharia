import { AlertCircle } from "lucide-react";

import { ApiError } from "@/lib/api-client";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";

/**
 * Renderiza um erro da API (RFC 7807, DEC-11) de forma consistente:
 * título + detalhe + lista de violações de campo, quando presentes.
 */
export function ApiErrorAlert({ error }: { error: ApiError | Error | null }) {
  if (!error) return null;

  const title = error instanceof ApiError ? error.title : "Erro inesperado";
  const detail = error instanceof ApiError ? error.detail : error.message;
  const fieldErrors = error instanceof ApiError ? error.errors : [];

  return (
    <Alert variant="destructive" role="alert">
      <AlertCircle aria-hidden="true" />
      <AlertTitle>{title}</AlertTitle>
      <AlertDescription>
        {detail ? <p>{detail}</p> : null}
        {fieldErrors.length > 0 ? (
          <ul className="mt-1 list-inside list-disc">
            {fieldErrors.map((fieldError) => (
              <li key={fieldError.field}>
                <span className="font-medium">{fieldError.field}:</span> {fieldError.message}
              </li>
            ))}
          </ul>
        ) : null}
      </AlertDescription>
    </Alert>
  );
}
