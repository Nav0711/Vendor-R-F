import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import axios from 'axios';
import { AlertCircle, CheckCircle2, ShieldAlert } from 'lucide-react';

const Dashboard = () => {
  const { scanId } = useParams();
  const [status, setStatus] = useState('PENDING');
  const [report, setReport] = useState<any>(null);

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
      </div>
    );
  }

  if (!report) return null;

  const getRiskColor = (level: string) => {
    switch(level) {
      case 'CRITICAL': return 'bg-red-100 text-red-800 border-red-200';
      case 'HIGH': return 'bg-orange-100 text-orange-800 border-orange-200';
      case 'MEDIUM': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'LOW': return 'bg-blue-100 text-blue-800 border-blue-200';
      default: return 'bg-green-100 text-green-800 border-green-200';
    }
  };

  return (
    <div className="max-w-5xl mx-auto space-y-8">
      <div className="flex items-start justify-between">
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
            {Object.entries(report.risk_summary.findings_by_category).map(([cat, count]: any) => (
              <div key={cat} className="text-center p-3 bg-secondary/50 rounded-lg">
                <div className="text-2xl font-bold text-primary">{count}</div>
                <div className="text-xs text-muted-foreground capitalize">{cat.replace('_', ' ')}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

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
    </div>
  );
};

export default Dashboard;
