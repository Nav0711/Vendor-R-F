import { Newspaper } from 'lucide-react';
import Section from './Section';
import ArticleRow from './ArticleRow';
import Row from './Row';
import FilterNote from './FilterNote';
import { type NewsItem } from './types';

const NewsTab = ({ allNews, showingAll, bucket }: { allNews: NewsItem[]; showingAll?: boolean; bucket?: string }) => (
  <div className="animate-in fade-in duration-200">
    <Section
      title={`${allNews.length} News & Media Result${allNews.length !== 1 ? 's' : ''}`}
      icon={<Newspaper className="w-4 h-4" />}>
      {showingAll && <FilterNote bucket={bucket} />}
      {allNews.length > 0
        ? allNews.map((a, i) => (
            <ArticleRow
              key={i}
              source={a.source}
              title={a.title}
              meta={a.meta}
              url={a.url}
              summary={a.summary}
              relevance={a.relevance}
              criticality={a.criticality}
            />
          ))
        : <Row label="Status" value="No news articles found across all sources" />}
    </Section>
  </div>
);

export default NewsTab;
