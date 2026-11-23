/**
 * TEMPLATE: Contratos TypeScript alineados con los Schemas Pydantic del Backend
 * Ubicación: frontend/src/types/analysis.types.ts
 *
 * Propósito:
 *   Tipar fuertemente las respuestas de `/api/analyze`, `/api/analyze/image` y `/api/compare`.
 */

// TODO (Fase 1): Completar interfaces cuando se definan los campos exactos en `backend/app/schemas/analysis.py`

export interface BiasProbabilities {
  leftPercentage: number;   // Izquierda %
  centerPercentage: number; // Centro %
  rightPercentage: number;  // Derecha %
  dominantFraming: 'LEFT' | 'CENTER' | 'RIGHT';
}

export interface QuoteEvidence {
  exactQuote: string;
  framingIndicator: string;
  explanation: string;
}

export interface StructuralMetrics {
  // TODO (Fase 2 - Contador Objetivo):
  // Conteo de citas directas entre comillas por actor, carga adjetiva y cifras sin fuente
  directQuotesByActor: Record<string, number>;
  paraphrasesByActor: Record<string, number>;
  qualifyingAdjectivesRatio: number;
  unattributedClaims: string[];
}

export interface CriticalAnalysisReport {
  summaryVerdict: string;
  supportingQuotes: QuoteEvidence[]; // Mínimo 2 citas textuales
  missingPerspectives: string[];
  localContextNotes?: string[];      // Fase 2: Memoria de Contexto Chileno
}

export interface SingleArticleAnalysisResponse {
  articleMetadata: {
    title: string;
    lead?: string;
    sourceDomain?: string;
  };
  anonymizedPreview: string;
  probabilities: BiasProbabilities;
  structuralMetrics?: StructuralMetrics;
  criticalAnalysis: CriticalAnalysisReport;
}

export interface SideBySideComparisonResponse {
  // TODO (Fase 3 - Comparador Lado a Lado):
  individualReports: SingleArticleAnalysisResponse[];
  headlineEmphasisContrast: Record<string, string>;
  interviewedActorsMatrix: Record<string, string[]>;
  crossOmissions: string[];
}
