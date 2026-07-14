import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { ArrowLeft, XCircle, Building2, Download, Share2 } from 'lucide-react';
import { type TabKey, type NewsItem } from './dashboard/types';
import { getRisk, tryHost } from './dashboard/utils';
import OverviewTab from './dashboard/OverviewTab';
import FindingsTab from './dashboard/FindingsTab';
import NewsTab from './dashboard/NewsTab';
import WebTab from './dashboard/WebTab';
import IndiaTab from './dashboard/IndiaTab';
import ScanLoading from './dashboard/ScanLoading';

const useScanReport = (scanId?: string) => {
  const [status, setStatus] = useState('PENDING');
  const [report, setReport] = useState<any>(null);
  useEffect(() => {
    const TERMINAL = ['COMPLETED', 'ERROR'];
    let stopped = false;
    const check = async () => {
      if (stopped) return;
      try {
        const res = await axios.get(`http://localhost:8000/scan/${scanId}/status`);
        const s = res.data.status;
        setStatus(s);
        if (TERMINAL.includes(s)) {
          stopped = true;
          if (s === 'COMPLETED') {
            const rep = await axios.get(`http://localhost:8000/scan/${scanId}/report`);
            setReport(rep.data);
          }
        }
      } catch (err) { console.error(err); }
    };
    check();
    const id = setInterval(check, 3000);
    return () => { stopped = true; clearInterval(id); };
  }, [scanId]);
  return { status, report };
};

const Dashboard = () => {
  const { scanId } = useParams();
  const navigate = useNavigate();
  const { status, report } = useScanReport(scanId);
  const [tab, setTab] = useState<TabKey>('overview');

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
  const isMock        = report.data_mode === 'mock';
  const isHeuristic   = report.section_analysis?._heuristic === true;
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
  // ── Render ─────────────────────────────────────────────────────────────────
  return (
    <div className="max-w-5xl mx-auto space-y-6 pb-12 animate-in fade-in duration-500">
      {/* Back & Actions */}
      <div className="flex items-center justify-between">
        <button onClick={() => navigate('/')}
          className="inline-flex items-center text-sm font-medium text-muted-foreground hover:text-foreground transition-colors">
          <ArrowLeft className="w-4 h-4 mr-1.5" /> Back to Search
        </button>
        <div className="flex items-center gap-2">
          <button
            onClick={() => window.print()}
            className="inline-flex items-center gap-2 px-3 py-1.5 text-sm font-medium rounded-lg border bg-background hover:bg-muted transition-colors shadow-sm"
          >
            <Download className="w-4 h-4" />
            <span className="hidden sm:inline">Export PDF</span>
          </button>
          <button
            className="inline-flex items-center gap-2 px-3 py-1.5 text-sm font-medium rounded-lg border bg-background hover:bg-muted transition-colors shadow-sm"
          >
            <Share2 className="w-4 h-4" />
            <span className="hidden sm:inline">Share</span>
          </button>
        </div>
      </div>

      {/* ── Header ──────────────────────────────────────────────────────────── */}
      <div className="bg-card border-2 rounded-2xl p-6 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-6 relative overflow-hidden">
        {/* Subtle background flair */}
        <div className="absolute -top-10 -right-10 w-40 h-40 bg-primary/5 rounded-full blur-3xl pointer-events-none" />

        <div className="relative z-10 space-y-1.5">
          <div className="flex items-center gap-2">
            <h1 className="text-3xl font-bold tracking-tight text-foreground">
              {report.subject.legal_name ?? 'Unknown Entity'}
            </h1>
            <div className={`px-2.5 py-0.5 rounded-full border text-xs font-bold tracking-widest flex items-center gap-1.5 ${riskStyles.badge}`}>
              <div className={`w-1.5 h-1.5 rounded-full animate-pulse ${riskStyles.dot}`} />
              {riskLevel} RISK
            </div>
          </div>
          <p className="text-sm font-medium text-muted-foreground flex items-center gap-2">
            <Building2 className="w-4 h-4" />
            {report.subject.scan_type?.toUpperCase()} SCAN
            {report.subject.domain && (
              <>
                <span className="w-1 h-1 bg-border rounded-full" />
                <span className="font-mono text-xs">{report.subject.domain}</span>
              </>
            )}
          </p>
        </div>

        <div className="relative z-10 flex items-center gap-3 md:gap-6 bg-muted/30 p-3 rounded-xl border border-muted">
          {[
            { label: 'Findings',    value: findingsCount },
            { label: 'Tokens Used', value: (report.tokens_used      ?? 0).toLocaleString() },
            { label: 'Balance',     value: (report.tokens_remaining  ?? 0).toLocaleString() },
          ].map((s, i) => (
            <div key={s.label} className={`text-center px-2 md:px-4 ${i !== 0 ? 'border-l border-border/50' : ''}`}>
              <div className="text-xl md:text-2xl font-bold text-foreground">{s.value}</div>
              <div className="text-[10px] md:text-xs font-semibold text-muted-foreground uppercase tracking-wider mt-0.5">{s.label}</div>
            </div>
          ))}
        </div>
      </div>

      {/* ── Tab bar ─────────────────────────────────────────────────────────── */}
      <div className="bg-muted/40 p-1 rounded-xl border flex overflow-x-auto hide-scrollbar">
        {tabs.map(t => (
          <button key={t.key} onClick={() => setTab(t.key)}
            className={`flex-1 min-w-[120px] px-4 py-2 text-sm font-semibold rounded-lg transition-all whitespace-nowrap flex items-center justify-center gap-2 ${
              tab === t.key
                ? 'bg-background text-foreground shadow-sm'
                : 'text-muted-foreground hover:text-foreground hover:bg-background/50'
            }`}>
            {t.label}
            {(t.count ?? 0) > 0 && (
              <span className={`text-[10px] px-1.5 py-0.5 rounded-full font-bold leading-none ${
                t.key === 'findings'
                  ? 'bg-destructive/10 text-destructive'
                  : 'bg-primary/10 text-primary'
              }`}>
                {t.count}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* ── Tab panels ──────────────────────────────────────────────────────── */}
      <div className="animate-in fade-in slide-in-from-bottom-2 duration-300">
        {tab === 'overview' && <OverviewTab  ss={ss} report={report} />}
        {tab === 'findings' && <FindingsTab  findings={report.adverse_findings ?? []} findingsCount={findingsCount} />}
        {tab === 'news'     && <NewsTab      allNews={allNews} />}
        {tab === 'web'      && <WebTab       ss={ss} report={report} />}
        {tab === 'india'    && <IndiaTab     ss={ss} />}
      </div>
    </div>
  );
};

export default Dashboard;
