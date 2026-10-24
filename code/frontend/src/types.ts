export type LensKey = 'stoic' | 'existential' | 'taoist'

export interface SourceItem {
  doc_id: string
  title: string
  school: string
  thinker: string
  snippet: string
  score: number
}

export interface Lens {
  key: LensKey
  name: string
  en: string
  icon: string
  accent: string
  soft: string
  line: string
  tagline: string
  core_ask: string
  headline: string
  description: string
  quote: string
  thinker: string
  fit_for: string
  thinkers: string[]
  prompts: string[]
  opening: string
  retrieved: string[]
}

export interface Message {
  id: string
  role: 'user' | 'agent'
  content: string
  turn_index: number
  seq: number
  created_at?: string | null
  sources: SourceItem[]
}

export interface SessionDetail {
  id: string
  question: string
  lens: LensKey | null
  lens_name: string | null
  core_ask: string | null
  status: string
  created_at?: string | null
  updated_at?: string | null
  turn_count: number
  summary_count: number
  perspectives: Lens[]
  messages: Message[]
  latest_summary_id: string | null
  reading: string
}

export interface SessionBrief {
  id: string
  question: string
  lens: LensKey | null
  lens_name: string | null
  core_ask: string | null
  status: string
  created_at?: string | null
  updated_at?: string | null
  turn_count: number
  summary_count: number
}

export interface Summary {
  id: string
  session_id: string
  version: number
  question: string
  lens: string
  lens_name: string
  core_ask: string
  tagline: string
  turns: number
  takeaway: string
  insights: string[]
  tensions: string[]
  practices: string[]
  keywords: string[]
  excerpts: { role: string; text: string; created_at?: string | null }[]
  sources: SourceItem[]
  created_at?: string | null
}

export interface FaqAnswer {
  question: string
  answer: string
  matched: string | null
  sources: SourceItem[]
  mode: string
}

export interface FaqEntry {
  faq_id: string
  question: string
  answer: string
  school: string
  tags: string[]
}

export interface HealthInfo {
  status: string
  database: string
  agent: {
    llm_mode: string
    llm_model: string
    llm_base_url?: string | null
    embedding_provider?: string
    vectorstore: string
    pinecone_index: string | null
    top_k: number
  }
}
