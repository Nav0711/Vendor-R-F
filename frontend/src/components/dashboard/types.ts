export type TabKey = 'overview' | 'findings' | 'news' | 'web' | 'india';

export type NewsItem = {
  source: string;
  title: string;
  meta: string;
  url: string;
  summary?: string;
  relevance?: number;
  criticality?: number;
};
