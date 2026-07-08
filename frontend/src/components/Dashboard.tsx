import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { ArrowLeft, XCircle, Building2 } from 'lucide-react';
import { type TabKey, type NewsItem } from './dashboard/types';
import { getRisk, tryHost } from './dashboard/utils';
import OverviewTab from './dashboard/OverviewTab';
import FindingsTab from './dashboard/FindingsTab';
import NewsTab from './dashboard/NewsTab';
import WebTab from './dashboard/WebTab';
import IndiaTab from './dashboard/IndiaTab';
import ScanLoading from './dashboard/ScanLoading';

const Dashboard = () => {
  const { scanId } = useParams();
  const navigate = useNavigate();
  const [status, setStatus]   = useState('PENDING');
  const [report, setReport]   = useState<any>(null);
  const [tab, setTab]         = useState<TabKey>('overview');

  useEffect(() => {
    let interval: ReturnType<typeof setInterval>;
    const TERMINAL = ['COMPLETED', 'ERROR'];
    const check = async () => {
      try {
        const res = await axios.get(`http://localhost:8000/scan/${scanId}/status`);
        const s = res.data.status;
        setStatus(s);
        if (TERMINAL.includes(s)) {
          clearInterval(interval);
          if (s === 'COMPLETED') {
            const rep = await axios.get(`http://localhost:8000/scan/${scanId}/report`);
            setReport(rep.data);
          }
        }
      } catch (err) { console.error(err); }
    };
    check();
    if (!TERMINAL.includes(status)) interval = setInterval(check, 3000);
    return () => clearInterval(interval);
  }, [scanId, status]);

  // ── Error state ────────────────────────────────────────────────────────────
  if (status === 'ERROR') {
    return (
      <div className="max-w-xl mx-auto mt-20 p-8 bg-card border border-destructive/30 rounded-2xl shadow-sm text-center space-y-4">
        <XCircle className="w-10 h-10 text-destructive mx-auto" />
        <div>
          <h2 className="text-xl font-semibold text-foreground">Scan Failed</h2>
          <p className="text-sm text-muted-foreground mt-1">
            The scan could not be completed. Check the backend logs for details.
          </p>
        </div>
        <button onClick={() => navigate('/')}
          className="inline-flex items-center gap-1.5 text-sm px-4 py-2 rounded-lg bg-secondary hover:bg-secondary/80 transition-colors">
          <ArrowLeft className="w-4 h-4" /> Back to Home
        </button>
      </div>
    );
  }

  // ── Loading state ──────────────────────────────────────────────────────────
  if (status !== 'COMPLETED') {
    return <ScanLoading onCancel={() => navigate('/')} />;
  }

  if (!report) return null;

  // ── Derived data ───────────────────────────────────────────────────────────
  const ss            = report.sources_summary ?? {};
  const riskLevel     = report.risk_summary?.overall_risk_level ?? 'UNKNOWN';
  const riskStyles    = getRisk(riskLevel);
  const findingsCount = report.adverse_findings?.length ?? 0;
  const hasAuthBridge = !!(ss.authbridge_tsp || ss.authbridge_intel || ss.sandbox_tsp || ss.sandbox_intel);

  // Use backend-combined list (with AI insight) if available; fall back to client-side aggregation
  const allNews: NewsItem[] = (ss.news_combined?.length ?? 0) > 0
    ? (ss.news_combined as NewsItem[])
    : [
        ...(ss.gdelt              ?? []).map((a: any) => ({ source: 'GDELT',      title: a.title, meta: a.domain,       url: a.url  })),
        ...(ss.newsapi            ?? []).map((a: any) => ({ source: 'NewsAPI',    title: a.title, meta: a.source,       url: a.url  })),
        ...(ss.newsapi_regulatory ?? []).map((a: any) => ({ source: 'Regulatory', title: a.title, meta: a.source,       url: a.url  })),
        ...(ss.serper_news        ?? []).map((a: any) => ({ source: 'Google',     title: a.title, meta: tryHost(a.link), url: a.link })),
      ].filter((a): a is NewsItem => !!a.title);

  // Append enrichment GDELT items (always without AI insight — India-only enrichment path)
  for (const [name, data] of Object.entries(
    ((ss.authbridge_enrichment ?? ss.sandbox_enrichment)?.alternate_names_searched ?? {}) as Record<string, any>
  )) {
    for (const item of (data as any).gdelt_results ?? []) {
      if (item.title) allNews.push({
        source: `GDELT·${name.split(' ')[0]}`, title: item.title, meta: item.domain, url: item.url,
      });
    }
  }

  const tabs: { key: TabKey; label: string; count?: number }[] = [
    { key: 'overview',  label: 'Overview' },
    { key: 'findings',  label: 'Findings',    count: findingsCount },
    { key: 'news',      label: 'News & Media', count: allNews.length },
    { key: 'web',       label: 'Web & Reviews' },
    ...(hasAuthBridge ? [{ key: 'india' as TabKey, label: 'AuthBridge Checks' }] : []),
  ];

  // ── Render ─────────────────────────────────────────────────────────────────
  return (
    <div className="max-w-5xl mx-auto space-y-4 pb-12">
      {/* Back */}
      <button onClick={() => navigate('/')}
        className="inline-flex items-center text-sm text-muted-foreground hover:text-primary transition-colors">
        <ArrowLeft className="w-4 h-4 mr-1" /> Back
      </button>

      {/* ── Header ──────────────────────────────────────────────────────────── */}
      <div className="bg-card border rounded-xl px-5 py-4 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground">
            {report.subject.legal_name ?? 'Unknown Entity'}
          </h1>
          <p className="text-xs text-muted-foreground mt-0.5 flex items-center gap-2">
            <Building2 className="w-3.5 h-3.5" />
            {report.subject.scan_type?.toUpperCase()} SCAN
            {report.subject.domain && (
              <span className="border rounded px-1.5 py-0.5 font-mono text-[10px]">
                {report.subject.domain}
              </span>
            )}
          </p>
        </div>

        <div className="flex items-center gap-4">
          <div className={`px-3 py-1.5 rounded-lg border font-bold text-sm flex items-center gap-2 ${riskStyles.badge}`}>
            <div className={`w-2 h-2 rounded-full animate-pulse ${riskStyles.dot}`} />
            {riskLevel} RISK
          </div>
          {[
            { label: 'Findings',    value: findingsCount },
            { label: 'Tokens Used', value: (report.tokens_used      ?? 0).toLocaleString() },
            { label: 'Balance',     value: (report.tokens_remaining  ?? 0).toLocaleString() },
          ].map(s => (
            <div key={s.label} className="text-center hidden sm:block">
              <div className="text-base font-bold text-foreground">{s.value}</div>
              <div className="text-[10px] text-muted-foreground uppercase tracking-wider">{s.label}</div>
            </div>
          ))}
        </div>
      </div>

      {/* ── Tab bar ─────────────────────────────────────────────────────────── */}
      <div className="flex gap-0 border-b border-border overflow-x-auto">
        {tabs.map(t => (
          <button key={t.key} onClick={() => setTab(t.key)}
            className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-all whitespace-nowrap flex items-center gap-1.5 ${
              tab === t.key
                ? 'border-primary text-foreground'
                : 'border-transparent text-muted-foreground hover:text-foreground'
            }`}>
            {t.label}
            {(t.count ?? 0) > 0 && (
              <span className={`text-[10px] px-1.5 py-0.5 rounded-full font-bold ${
                t.key === 'findings'
                  ? 'bg-destructive text-destructive-foreground'
                  : 'bg-secondary text-secondary-foreground'
              }`}>
                {t.count}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* ── Tab panels ──────────────────────────────────────────────────────── */}
      {tab === 'overview' && <OverviewTab  ss={ss} report={report} />}
      {tab === 'findings' && <FindingsTab  findings={report.adverse_findings ?? []} findingsCount={findingsCount} />}
      {tab === 'news'     && <NewsTab      allNews={allNews} />}
      {tab === 'web'      && <WebTab       ss={ss} report={report} />}
      {tab === 'india'    && <IndiaTab     ss={ss} />}
    </div>
  );
};

export default Dashboard;
