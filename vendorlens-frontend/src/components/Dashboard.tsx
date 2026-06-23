import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { AlertCircle, CheckCircle2, ShieldAlert, ArrowLeft, RefreshCw, XCircle, Newspaper, Globe, ExternalLink, Landmark, ShieldCheck } from 'lucide-react';

const Dashboard = () => {
  const { scanId } = useParams();
  const navigate = useNavigate();
  const [status, setStatus] = useState('PENDING');
  const [report, setReport] = useState<any>(null);
  const [activeTab, setActiveTab] = useState('news');

  useEffect(() => {
    let interval: ReturnType<typeof setInterval>;

    const checkStatus = async () => {
      try {
        const res = await axios.get(`http://localhost:8000/scan/${scanId}/status`);
        setStatus(res.data.status);
        if (res.data.status === 'COMPLETED') {
          clearInterval(interval);
          const rep = await axios.get(`http://localhost:8000/scan/${scanId}/report`);
          setReport(rep.data);
        }
      } catch (err) {
        console.error(err);
      }
    };

    checkStatus();
    if (status !== 'COMPLETED') {
      interval = setInterval(checkStatus, 3000);
    }
    return () => clearInterval(interval);
  }, [scanId, status]);

  if (status !== 'COMPLETED') {
    return (
      <div className="max-w-2xl mx-auto mt-20 text-center space-y-6">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
        <h2 className="text-2xl font-semibold">Scan in Progress...</h2>
        <p className="text-muted-foreground">Our AI agents are analyzing multiple data sources. This may take a few minutes.</p>
        <div className="w-full bg-secondary rounded-full h-2">
          <div className="bg-primary h-2 rounded-full animate-pulse" style={{ width: '60%' }}></div>
        </div>
        <button
          onClick={() => navigate('/')}
          className="mt-8 inline-flex items-center text-sm font-medium text-muted-foreground hover:text-destructive transition-colors"
        >
          <XCircle className="w-4 h-4 mr-2" /> Cancel and Return Home
        </button>
      </div>
    );
  }

  if (!report) return null;

  const getRiskColor = (level: string) => {
    switch (level) {
      case 'CRITICAL': return 'bg-red-100 text-red-800 border-red-200';
      case 'HIGH': return 'bg-orange-100 text-orange-800 border-orange-200';
      case 'MEDIUM': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'LOW': return 'bg-blue-100 text-blue-800 border-blue-200';
      default: return 'bg-green-100 text-green-800 border-green-200';
    }
  };

  return (
    <div className="max-w-5xl mx-auto space-y-8">
      <div className="flex items-center justify-between">
        <button
          onClick={() => navigate('/')}
          className="inline-flex items-center text-sm font-medium text-muted-foreground hover:text-primary transition-colors"
        >
          <ArrowLeft className="w-4 h-4 mr-1" /> New Scan
        </button>
      </div>

      <div className="flex items-start justify-between border-b pb-6">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">{report.subject.legal_name}</h2>
          <p className="text-muted-foreground">{report.subject.domain} • {report.subject.scan_type.toUpperCase()} SCAN</p>
        </div>
        <div className={`px-4 py-2 rounded-full border font-bold text-lg ${getRiskColor(report.risk_summary.overall_risk_level)}`}>
          {report.risk_summary.overall_risk_level} RISK
        </div>
      </div>

      <div className="grid md:grid-cols-3 gap-6">
        <div className="bg-card border rounded-xl p-6 shadow-sm">
          <div className="text-sm font-medium text-muted-foreground mb-2">Total Adverse Findings</div>
          <div className="text-4xl font-bold">{report.risk_summary.total_adverse_findings}</div>
        </div>
        <div className="bg-card border rounded-xl p-6 shadow-sm md:col-span-2">
          <div className="text-sm font-medium text-muted-foreground mb-4">Findings Breakdown</div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {Object.entries(report.risk_summary.findings_by_category || {}).map(([cat, count]: any) => (
              <div key={cat} className="text-center p-3 bg-secondary/50 rounded-lg">
                <div className="text-2xl font-bold text-primary">{count}</div>
                <div className="text-xs text-muted-foreground capitalize">{cat.replace('_', ' ')}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* New Token Display Section */}
      {(report.tokens_used !== undefined || report.tokens_remaining !== undefined) && (
        <div className="grid md:grid-cols-2 gap-6">
          <div className="bg-secondary/20 border border-secondary rounded-xl p-5 flex items-center justify-between">
            <div>
              <div className="text-sm font-medium text-muted-foreground">Tokens Consumed</div>
              <div className="text-2xl font-bold text-foreground mt-1">{report.tokens_used?.toLocaleString() || 0}</div>
            </div>
            <RefreshCw className="w-8 h-8 text-muted-foreground opacity-50" />
          </div>
          <div className="bg-secondary/20 border border-secondary rounded-xl p-5 flex items-center justify-between">
            <div>
              <div className="text-sm font-medium text-muted-foreground">Remaining API Balance</div>
              <div className="text-2xl font-bold text-foreground mt-1">{report.tokens_remaining?.toLocaleString() || 0}</div>
            </div>
            <CheckCircle2 className="w-8 h-8 text-green-500 opacity-50" />
          </div>
        </div>
      )}

      {report.adverse_findings.length > 0 && (
        <div className="space-y-4">
          <h3 className="text-xl font-semibold">Adverse Findings</h3>
          <div className="space-y-4">
            {report.adverse_findings.map((finding: any) => (
              <div key={finding.finding_id} className="bg-card border rounded-xl p-6 shadow-sm flex space-x-4">
                <div className="mt-1">
                  {finding.severity === 'CRITICAL' ? <ShieldAlert className="text-red-500 w-6 h-6" /> : <AlertCircle className="text-orange-500 w-6 h-6" />}
                </div>
                <div className="flex-1 space-y-2">
                  <div className="flex items-center justify-between">
                    <h4 className="font-bold text-lg">{finding.title}</h4>
                    <span className={`text-xs px-2 py-1 rounded-full font-semibold ${getRiskColor(finding.severity)}`}>
                      {finding.severity}
                    </span>
                  </div>
                  <p className="text-sm text-muted-foreground">{finding.detail}</p>
                  <div className="text-xs bg-secondary/50 p-3 rounded mt-2 font-mono break-all">
                    Evidence: {finding.evidence.source_name} - {finding.evidence.raw_excerpt}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {report.adverse_findings.length === 0 && (
        <div className="bg-green-50 border border-green-200 rounded-xl p-8 text-center space-y-3">
          <CheckCircle2 className="w-12 h-12 text-green-500 mx-auto" />
          <h3 className="text-xl font-bold text-green-800">No Adverse Findings</h3>
          <p className="text-green-700">The vendor passed all checks included in this scan depth.</p>
        </div>
      )}

      {/* Sources of News & Analysis Reference Section */}
      {report.sources_summary && Object.keys(report.sources_summary).length > 0 && (
        <div className="space-y-6 bg-card border rounded-xl p-6 shadow-sm">
          <div className="border-b pb-4">
            <h3 className="text-xl font-bold tracking-tight">Sources of News & Analysis</h3>
            <p className="text-sm text-muted-foreground">Detailed records of external data feeds and queries performed during this scan.</p>
          </div>

          {/* Tab Headers */}
          <div className="flex space-x-2 border-b overflow-x-auto pb-px">
            <button
              onClick={() => setActiveTab('news')}
              className={`px-4 py-2 text-sm font-semibold border-b-2 transition-all whitespace-nowrap ${activeTab === 'news'
                  ? 'border-primary text-primary border-primary'
                  : 'border-transparent text-muted-foreground hover:text-foreground'
                }`}
            >
              Adverse News & Web Search
            </button>
            <button
              onClick={() => setActiveTab('registries')}
              className={`px-4 py-2 text-sm font-semibold border-b-2 transition-all whitespace-nowrap ${activeTab === 'registries'
                  ? 'border-primary text-primary border-primary'
                  : 'border-transparent text-muted-foreground hover:text-foreground'
                }`}
            >
              Corporate Registries & Domains
            </button>
            <button
              onClick={() => setActiveTab('compliance')}
              className={`px-4 py-2 text-sm font-semibold border-b-2 transition-all whitespace-nowrap ${activeTab === 'compliance'
                  ? 'border-primary text-primary border-primary'
                  : 'border-transparent text-muted-foreground hover:text-foreground'
                }`}
            >
              Indian Tax compliance (TSP)
            </button>
            <button
              onClick={() => setActiveTab('other')}
              className={`px-4 py-2 text-sm font-semibold border-b-2 transition-all whitespace-nowrap ${activeTab === 'other'
                  ? 'border-primary text-primary border-primary'
                  : 'border-transparent text-muted-foreground hover:text-foreground'
                }`}
            >
              Watchlists & Addresses
            </button>
          </div>

          {/* Tab Content */}
          <div className="pt-2">
            {activeTab === 'news' && (
              <div className="space-y-6">
                {/* NewsAPI / GDELT */}
                <div>
                  <h4 className="font-semibold text-sm text-muted-foreground mb-3 uppercase tracking-wider">GDELT & NewsAPI Feeds</h4>
                  <div className="grid md:grid-cols-2 gap-4">
                    {/* GDELT */}
                    <div className="bg-secondary/20 p-4 rounded-lg border space-y-3">
                      <div className="flex items-center space-x-2 font-bold text-sm text-primary">
                        <Newspaper className="w-4 h-4" />
                        <span>GDELT Adverse Events Feed</span>
                      </div>
                      <div className="space-y-3">
                        {report.sources_summary.gdelt?.map((item: any, idx: number) => (
                          <div key={idx} className="text-xs space-y-1">
                            <a href={item.url} target="_blank" rel="noopener noreferrer" className="font-semibold text-foreground hover:underline flex items-center">
                              {item.title} <ExternalLink className="w-3 h-3 ml-1 text-muted-foreground" />
                            </a>
                            <span className="text-muted-foreground block">Domain: {item.domain}</span>
                          </div>
                        )) || <span className="text-xs text-muted-foreground">No news articles found.</span>}
                      </div>
                    </div>

                    {/* NewsAPI */}
                    <div className="bg-secondary/20 p-4 rounded-lg border space-y-3">
                      <div className="flex items-center space-x-2 font-bold text-sm text-primary">
                        <Globe className="w-4 h-4" />
                        <span>NewsAPI Worldwide Search</span>
                      </div>
                      <div className="space-y-3">
                        {report.sources_summary.newsapi?.map((item: any, idx: number) => (
                          <div key={idx} className="text-xs space-y-1">
                            <a href={item.url} target="_blank" rel="noopener noreferrer" className="font-semibold text-foreground hover:underline flex items-center">
                              {item.title} <ExternalLink className="w-3 h-3 ml-1 text-muted-foreground" />
                            </a>
                            <p className="text-muted-foreground line-clamp-2">{item.description}</p>
                            <span className="text-[10px] text-muted-foreground block mt-1">Source: {item.source} • {new Date(item.publishedAt).toLocaleDateString()}</span>
                          </div>
                        )) || <span className="text-xs text-muted-foreground">No news articles found.</span>}
                      </div>
                    </div>
                  </div>
                </div>

                {/* Serper */}
                <div>
                  <h4 className="font-semibold text-sm text-muted-foreground mb-3 uppercase tracking-wider">Web Search Reviews & Anomalies (Serper)</h4>
                  <div className="space-y-3">
                    {report.sources_summary.serper?.map((item: any, idx: number) => (
                      <div key={idx} className="bg-secondary/10 p-3 rounded-lg border text-xs space-y-1">
                        <a href={item.link} target="_blank" rel="noopener noreferrer" className="font-semibold text-foreground hover:underline flex items-center text-sm">
                          {item.title} <ExternalLink className="w-3 h-3 ml-1 text-muted-foreground" />
                        </a>
                        <p className="text-muted-foreground">{item.snippet}</p>
                      </div>
                    )) || <span className="text-xs text-muted-foreground">No search anomalies found.</span>}
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'registries' && (
              <div className="grid md:grid-cols-3 gap-6">
                {/* OpenCorporates */}
                <div className="bg-secondary/20 p-4 rounded-lg border space-y-3 text-xs">
                  <div className="flex items-center space-x-2 font-bold text-sm text-primary">
                    <Landmark className="w-4 h-4" />
                    <span>OpenCorporates Registry</span>
                  </div>
                  <div className="space-y-2">
                    {report.sources_summary.opencorporates?.map((comp: any, idx: number) => (
                      <div key={idx} className="border-b pb-2 last:border-0 last:pb-0 space-y-1">
                        <a href={`https://opencorporates.com/companies/${comp.jurisdiction_code?.toLowerCase()}/${comp.company_number}`} target="_blank" rel="noopener noreferrer" className="font-bold text-foreground hover:underline flex items-center">
                          {comp.name} <ExternalLink className="w-3 h-3 ml-1 text-muted-foreground" />
                        </a>
                        <div>No: {comp.company_number}</div>
                        <div>Jurisdiction: {comp.jurisdiction_code?.toUpperCase()}</div>
                        <div className="flex items-center space-x-1 mt-1">
                          <span className={`w-2 h-2 rounded-full ${comp.current_status === 'Active' ? 'bg-green-500' : 'bg-red-500'}`}></span>
                          <span className="font-medium text-muted-foreground">{comp.current_status || 'Unknown'}</span>
                        </div>
                      </div>
                    )) || <div className="text-muted-foreground">No registry entries found.</div>}
                  </div>
                </div>

                {/* WHOIS */}
                <div className="bg-secondary/20 p-4 rounded-lg border space-y-3 text-xs">
                  <div className="flex items-center space-x-2 font-bold text-sm text-primary">
                    <Globe className="w-4 h-4" />
                    <span>WHOIS Domain Registry</span>
                  </div>
                  {report.sources_summary.whois ? (
                    <div className="space-y-1">
                      <div>
                        <span className="text-muted-foreground">Domain:</span>{' '}
                        <a href={`https://whois.domaintools.com/${report.sources_summary.whois.domain_name}`} target="_blank" rel="noopener noreferrer" className="font-bold text-foreground hover:underline inline-flex items-center">
                          {report.sources_summary.whois.domain_name} <ExternalLink className="w-3 h-3 ml-1 text-muted-foreground" />
                        </a>
                      </div>
                      <div><span className="text-muted-foreground">Registrar:</span> {report.sources_summary.whois.registrar}</div>
                      <div><span className="text-muted-foreground">Created:</span> {report.sources_summary.whois.creation_date ? new Date(report.sources_summary.whois.creation_date).toLocaleDateString() : 'N/A'}</div>
                      <div><span className="text-muted-foreground">Status:</span> {report.sources_summary.whois.status || 'Active'}</div>
                    </div>
                  ) : (
                    <div className="text-muted-foreground">No WHOIS data available.</div>
                  )}
                </div>

                {/* SSL Certificate Check */}
                <div className="bg-secondary/20 p-4 rounded-lg border space-y-3 text-xs">
                  <div className="flex items-center space-x-2 font-bold text-sm text-primary">
                    <ShieldCheck className="w-4 h-4" />
                    <span>SSL Certificate Validity</span>
                  </div>
                  {report.sources_summary.ssl ? (
                    <div className="space-y-2">
                      <div className="flex items-center space-x-2">
                        <a href={`https://www.ssllabs.com/ssltest/analyze.html?d=${report.subject.domain}`} target="_blank" rel="noopener noreferrer" className={`px-2 py-0.5 rounded text-[10px] font-bold hover:underline inline-flex items-center ${report.sources_summary.ssl.has_ssl ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                          {report.sources_summary.ssl.has_ssl ? 'VALID SSL' : 'NO SSL'} <ExternalLink className="w-3 h-3 ml-1" />
                        </a>
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${!report.sources_summary.ssl.is_expired ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                          {!report.sources_summary.ssl.is_expired ? 'ACTIVE' : 'EXPIRED'}
                        </span>
                      </div>
                      <div><span className="text-muted-foreground">Issuer:</span> {report.sources_summary.ssl.issuer || 'N/A'}</div>
                    </div>
                  ) : (
                    <div className="text-muted-foreground">No SSL data available.</div>
                  )}
                </div>
              </div>
            )}

            {activeTab === 'compliance' && (
              <div className="bg-secondary/20 p-5 rounded-lg border space-y-4 text-xs">
                <div className="flex items-center space-x-2 font-bold text-sm text-primary">
                  <ShieldCheck className="w-4 h-4" />
                  <span>Sandbox TSP Tax Registry Verifications</span>
                </div>
                <div className="grid md:grid-cols-2 gap-6">
                  {/* GSTIN */}
                  {report.sources_summary.sandbox_tsp?.gstin && (
                    <div className="bg-card p-4 rounded-lg border space-y-2">
                      <a href="https://services.gst.gov.in/services/searchtp" target="_blank" rel="noopener noreferrer" className="font-bold text-foreground border-b pb-1 hover:underline flex items-center">
                        GSTIN Registry Details <ExternalLink className="w-3 h-3 ml-1 text-muted-foreground" />
                      </a>
                      <div><span className="text-muted-foreground">Status:</span> <span className="font-bold text-green-600">{report.sources_summary.sandbox_tsp.gstin.status || 'Active'}</span></div>
                      <div><span className="text-muted-foreground">Verification:</span> <span className="font-bold text-green-600">{report.sources_summary.sandbox_tsp.gstin.valid ? 'VALID' : 'INVALID'}</span></div>
                      {report.sources_summary.sandbox_tsp.gstin.name && (
                        <div><span className="text-muted-foreground">Registered Entity:</span> {report.sources_summary.sandbox_tsp.gstin.name}</div>
                      )}
                    </div>
                  )}

                  {/* PAN */}
                  {report.sources_summary.sandbox_tsp?.pan && (
                    <div className="bg-card p-4 rounded-lg border space-y-2">
                      <a href="https://eportal.incometax.gov.in/iec/foservices/#/pre-login/verifyYourPAN" target="_blank" rel="noopener noreferrer" className="font-bold text-foreground border-b pb-1 hover:underline flex items-center">
                        PAN Registry Details <ExternalLink className="w-3 h-3 ml-1 text-muted-foreground" />
                      </a>
                      <div><span className="text-muted-foreground">Status:</span> <span className="font-bold text-green-600">{report.sources_summary.sandbox_tsp.pan.status || 'Active'}</span></div>
                      <div><span className="text-muted-foreground">Verification:</span> <span className="font-bold text-green-600">{report.sources_summary.sandbox_tsp.pan.valid ? 'VALID' : 'INVALID'}</span></div>
                      {report.sources_summary.sandbox_tsp.pan.name && (
                        <div><span className="text-muted-foreground">Cardholder Name:</span> {report.sources_summary.sandbox_tsp.pan.name}</div>
                      )}
                    </div>
                  )}

                  {!report.sources_summary.sandbox_tsp?.gstin && !report.sources_summary.sandbox_tsp?.pan && (
                    <div className="text-muted-foreground col-span-2">No GSTIN/PAN data checked for this vendor.</div>
                  )}
                </div>
              </div>
            )}

            {activeTab === 'other' && (
              <div className="grid md:grid-cols-2 gap-6 text-xs">
                {/* OpenSanctions */}
                <div className="bg-secondary/20 p-4 rounded-lg border space-y-3">
                  <div className="flex items-center space-x-2 font-bold text-sm text-primary">
                    <ShieldAlert className="w-4 h-4" />
                    <span>Watchlists & Sanctions (OpenSanctions)</span>
                  </div>
                  <div className="space-y-2">
                    {report.sources_summary.opensanctions?.map((sanc: any, idx: number) => (
                      <div key={idx} className="border-b pb-2 last:border-0 last:pb-0 space-y-1">
                        {sanc.caption ? (
                          <>
                            <a href={`https://www.opensanctions.org/search/?q=${encodeURIComponent(sanc.caption)}`} target="_blank" rel="noopener noreferrer" className="font-bold text-foreground hover:underline flex items-center">
                              {sanc.caption} ({sanc.schema}) <ExternalLink className="w-3 h-3 ml-1 text-muted-foreground" />
                            </a>
                            {sanc.properties?.country && <div>Country: {sanc.properties.country.join(', ')}</div>}
                            {sanc.properties?.status && <div>Status: {sanc.properties.status.join(', ')}</div>}
                          </>
                        ) : (
                          <div className="text-muted-foreground">{sanc.status || 'No match'}</div>
                        )}
                      </div>
                    )) || <div className="text-muted-foreground">No watchlists queried.</div>}
                  </div>
                </div>

                {/* Google Places & Microlink */}
                <div className="bg-secondary/20 p-4 rounded-lg border space-y-4">
                  <div className="space-y-2">
                    <div className="flex items-center space-x-2 font-bold text-sm text-primary">
                      <Globe className="w-4 h-4" />
                      <span>Address Presence (Google Places)</span>
                    </div>
                    {report.sources_summary.google_places?.map((place: any, idx: number) => (
                      <div key={idx} className="space-y-1">
                        <a href={`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(place.name + ' ' + place.formatted_address)}`} target="_blank" rel="noopener noreferrer" className="font-bold text-foreground hover:underline flex items-center">
                          {place.name} <ExternalLink className="w-3 h-3 ml-1 text-muted-foreground" />
                        </a>
                        <div className="text-muted-foreground">{place.formatted_address}</div>
                        <div>Status: <span className="font-bold text-green-600">{place.business_status}</span></div>
                      </div>
                    )) || <div className="text-muted-foreground">No address data found.</div>}
                  </div>

                  {report.sources_summary.microlink && (
                    <div className="border-t pt-3 space-y-2">
                      <div className="flex items-center space-x-2 font-bold text-sm text-primary">
                        <Globe className="w-4 h-4" />
                        <span>Website Content Metadata (Microlink)</span>
                      </div>
                      <div>
                        <a href={report.subject.domain?.startsWith('http') ? report.subject.domain : `https://${report.subject.domain}`} target="_blank" rel="noopener noreferrer" className="font-bold text-foreground hover:underline flex items-center">
                          {report.sources_summary.microlink.title} <ExternalLink className="w-3 h-3 ml-1 text-muted-foreground" />
                        </a>
                        <div className="text-muted-foreground">Publisher: {report.sources_summary.microlink.publisher || 'N/A'}</div>
                      </div>
                    </div>
                  )}
                </div>

                {/* Wikipedia */}
                {report.sources_summary.wikipedia?.found && (
                  <div className="bg-secondary/20 p-4 rounded-lg border space-y-3 col-span-1 md:col-span-2">
                    <div className="flex items-center space-x-2 font-bold text-sm text-primary">
                      <Globe className="w-4 h-4" />
                      <span>Wikipedia Summary</span>
                    </div>
                    <div className="space-y-1 text-xs">
                      <a href={report.sources_summary.wikipedia.page_url} target="_blank" rel="noopener noreferrer" className="font-bold text-foreground hover:underline flex items-center">
                        {report.sources_summary.wikipedia.title} <ExternalLink className="w-3 h-3 ml-1 text-muted-foreground" />
                      </a>
                      <div className="text-muted-foreground mt-1">{report.sources_summary.wikipedia.summary}</div>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default Dashboard;
