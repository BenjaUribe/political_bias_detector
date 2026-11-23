/**
 * TEMPLATE: Cliente HTTP hacia el Backend FastAPI
 * Ubicación: frontend/src/services/apiClient.ts
 *
 * Propósito:
 *   Centralizar las llamadas HTTP (`fetch` o `axios`) hacia la API REST del backend:
 *   - `POST /api/analyze`       (Fase 1: URL o texto plano)
 *   - `POST /api/analyze/image` (Fase 2: Captura de pantalla móvil para OCR multimodal)
 *   - `POST /api/compare`       (Fase 3: Comparador lado a lado de múltiples URLs)
 */

// TODO (Fase 1): Configurar variable de entorno `VITE_API_BASE_URL` (por defecto http://localhost:8000/api)

export async function analyzeArticleByUrlOrText(_payload: {
  url?: string;
  rawText?: string;
}): Promise<unknown> {
  // TODO (Fase 1): Implementar llamada POST a `/api/analyze`
  throw new Error('Pendiente de implementar en Fase 1.');
}

export async function analyzeArticleScreenshot(_imageFile: File): Promise<unknown> {
  // TODO (Fase 2): Enviar `FormData` con la captura móvil a `/api/analyze/image`
  throw new Error('Pendiente de implementar en Fase 2.');
}

export async function compareMultipleArticles(_urls: string[]): Promise<unknown> {
  // TODO (Fase 3): Implementar llamada POST a `/api/compare` para 2 o más enlaces
  throw new Error('Pendiente de implementar en Fase 3.');
}
