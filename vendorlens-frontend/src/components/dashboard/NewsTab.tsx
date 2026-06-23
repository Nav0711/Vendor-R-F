import { Newspaper } from 'lucide-react';
import Section from './Section';
import ArticleRow from './ArticleRow';
import Row from './Row';

type NewsItem = { source: string; title: string; meta: string; url: string };

const NewsTab = ({ allNews }: { allNews: NewsItem[] }) => (
  <div className="animate-in fade-in duration-200">
    <Section
      title={`${allNews.length} News & Media Result${allNews.length !== 1 ? 's' : ''}`}
      icon={<Newspaper className="w-4 h-4" />}>
      {allNews.length > 0
        ? allNews.map((a, i) => (
            <ArticleRow key={i} source={a.source} title={a.title} meta={a.meta} url={a.url} />
          ))
        : <Row label="Status" value="No news articles found across all sources" />}
    </Section>
  </div>
);

export default NewsTab;
