// Mirrors the backend's Pydantic schemas (backend/app/schemas).

export type AspectRatio = "portrait" | "square" | "story";
export type Align = "left" | "center" | "right";
export type Tone =
  | "Inspirational"
  | "Stoic"
  | "Bold"
  | "Poetic"
  | "Calm"
  | "Playful"
  | "Melancholic"
  | "Witty";

export interface Page<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}

export interface Quote {
  id: number;
  text: string;
  author: string | null;
  tone: string | null;
  keywords: string[];
  hashtags: string[];
  reflection: string | null;
  source: "seed" | "user" | "ai";
  quality_score: number | null;
  run_id: string | null;
  created_at: string;
}

export interface QuoteCreate {
  text: string;
  author?: string | null;
  tone?: string | null;
  keywords?: string[];
  hashtags?: string[];
  reflection?: string | null;
  source?: "user" | "ai";
  quality_score?: number | null;
  run_id?: string | null;
}

export interface SystemInfo {
  app: string;
  version: string;
  environment: string;
  llm: { enabled: boolean; detail: string };
  images: { enabled: boolean; detail: string };
  model: string | null;
  prompt_version: string;
  min_quality_score: number;
  max_rewrite_rounds: number;
  max_quotes_per_request: number;
  tones: Tone[];
  aspect_ratios: AspectRatio[];
  palettes: string[];
  counts: { quotes: number; posts: number; runs: number };
}

export interface GenerationRequest {
  topic: string;
  tone: Tone;
  count: number;
}

export interface GeneratedQuote {
  text: string;
  author: string | null;
  tone: string | null;
  angle: string | null;
  keywords: string[];
  hashtags: string[];
  reflection: string | null;
  score: number | null;
  scores: Record<string, number> | null;
  library_id: number | null;
}

export interface GenerationResponse {
  run_id: string;
  status: "success" | "partial" | "fallback" | "error";
  source: "llm" | "library";
  model: string | null;
  prompt_version: string;
  quotes: GeneratedQuote[];
  visual_mood: string[];
  rounds: number;
  latency_ms: number;
  usage: { input_tokens: number; output_tokens: number; llm_calls: number };
  note: string | null;
}

// --- streaming events ---------------------------------------------------
export interface RunStartedEvent {
  run_id: string;
  topic: string;
  tone: string;
  count: number;
  mode: "llm" | "library";
  model: string | null;
  prompt_version: string;
}

export interface StepEvent {
  node: "plan" | "write" | "review" | "finalize" | "library";
  label: string;
  round: number | null;
  status: "running" | "done" | "error";
  detail: string;
  duration_ms: number;
}

export interface CandidateEvent {
  round: number;
  text: string;
  status: "accepted" | "rejected";
  score: number | null;
  scores: Record<string, number> | null;
  reasons: string[];
  stage: "rules" | "judge" | null;
}

export type GenerationEvent =
  | { event: "run"; data: RunStartedEvent }
  | { event: "step"; data: StepEvent }
  | { event: "candidate"; data: CandidateEvent }
  | { event: "result"; data: GenerationResponse }
  | { event: "error"; data: { message: string } };

// --- media ----------------------------------------------------------------
export interface Background {
  id: string;
  source: "unsplash" | "gradient";
  aspect_ratio: AspectRatio;
  width: number;
  height: number;
  palette: string | null;
  keywords: string[];
  url: string;
  credit: { name: string; profile_url: string | null; photo_url: string | null } | null;
}

export interface PostStyle {
  aspect_ratio: AspectRatio;
  font_size: number;
  text_color: string;
  accent_color: string;
  align: Align;
  overlay_opacity: number;
  watermark: string | null;
  show_author: boolean;
  show_logo: boolean;
  show_quote_mark: boolean;
}

export interface PostQuote {
  text: string;
  author?: string | null;
  keywords?: string[];
  hashtags?: string[];
  reflection?: string | null;
}

export interface Post {
  id: string;
  filename: string;
  aspect_ratio: AspectRatio;
  width: number;
  height: number;
  quote_text: string;
  quote_author: string | null;
  caption: string;
  background_source: string;
  photographer_name: string | null;
  photographer_url: string | null;
  created_at: string;
  url: string;
  download_url: string;
}

export interface RunSummary {
  id: string;
  topic: string;
  tone: string;
  requested_count: number;
  status: GenerationResponse["status"];
  source: "llm" | "library";
  model: string | null;
  prompt_version: string;
  rounds: number;
  llm_calls: number;
  input_tokens: number;
  output_tokens: number;
  latency_ms: number;
  avg_score: number | null;
  accepted_count: number;
  rejected_count: number;
  error: string | null;
  created_at: string;
}

export interface RunDetail extends RunSummary {
  steps: StepEvent[];
  results: GeneratedQuote[];
}

export interface RunStats {
  total_runs: number;
  by_status: Record<string, number>;
  avg_latency_ms: number | null;
  avg_score: number | null;
  total_input_tokens: number;
  total_output_tokens: number;
  acceptance_rate: number | null;
}
