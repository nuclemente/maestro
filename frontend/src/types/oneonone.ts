export type SessionStatus = 'planned' | 'done' | 'cancelled';
export type TopicStatus = 'pending' | 'discussed' | 'parked';
export type TopicSource = 'manual' | 'slack_collection' | 'from_transcript';
export type CollectionStatus = 'awaiting' | 'closed';
export type Sentiment = 'positive' | 'neutral' | 'concern';
export type ActionItemOwner = 'em' | 'person' | 'other';
export type ActionItemStatus = 'open' | 'done';

export interface OneOnOneTrack {
  id: string;
  person_id: string;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface OneOnOneSession {
  id: string;
  track_id: string;
  scheduled_at: string | null;
  status: SessionStatus;
  external_event_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface EnrichmentHit {
  source: string;
  title: string;
  url: string | null;
  snippet: string | null;
}

export interface EnrichmentPayload {
  hits: EnrichmentHit[];
  summary: string | null;
  errors: string[];
}

export interface OneOnOneTopic {
  id: string;
  session_id: string;
  title: string;
  body: string | null;
  source: TopicSource;
  status: TopicStatus;
  enrichment: EnrichmentPayload | null;
  enriched_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface OneOnOneActionItem {
  id: string;
  transcript_id: string;
  description: string;
  owner: ActionItemOwner;
  status: ActionItemStatus;
  created_at: string;
  updated_at: string;
}

export interface AnalysisPayload {
  summary: string;
  follow_ups: string[];
  sentiment: Sentiment;
  suggested_topics: string[];
  action_items: { description: string; owner: ActionItemOwner }[];
}

export interface OneOnOneTranscript {
  id: string;
  session_id: string;
  raw_text: string;
  analysis: AnalysisPayload | null;
  analyzed_at: string | null;
  analysis_stale: boolean;
  created_at: string;
  updated_at: string;
  action_items: OneOnOneActionItem[];
}

export interface OneOnOneSessionDetail extends OneOnOneSession {
  topics: OneOnOneTopic[];
  transcript: OneOnOneTranscript | null;
}

export const SENTIMENT_LABEL: Record<Sentiment, string> = {
  positive: 'Positivo',
  neutral: 'Neutro',
  concern: 'Atenção',
};
