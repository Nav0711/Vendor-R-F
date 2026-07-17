import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { ShieldCheck, ArrowLeft, AlertCircle } from 'lucide-react';
import { api } from '../lib/api';

const ScanSelector = () => {
  const { inputId } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const startScan = async () => {
    setLoading(true);
    setErrorMsg(null);
    try {
      const res = await axios.post(api('/scan'), {
        input_id: inputId,
        scan_type: 'deep',
      });
      navigate(`/dashboard/${res.data.scan_id}`);
    } catch (err: any) {
      console.error(err);
      if (err.response?.status === 402) {
        setErrorMsg('API Token Limit Exceeded. You do not have enough tokens to perform this scan.');
      } else {
        setErrorMsg(err.response?.data?.detail || 'Error starting scan');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-md mx-auto space-y-6 mt-12 relative">
      <button
        onClick={() => navigate(-1)}
        disabled={loading}
        className="absolute -top-12 left-0 inline-flex items-center text-sm font-medium text-muted-foreground hover:text-primary transition-colors disabled:opacity-50"
      >
        <ArrowLeft className="w-4 h-4 mr-1" /> Go Back
      </button>

      <div className="text-center space-y-1">
        <h2 className="text-2xl font-semibold tracking-tight">Ready to Screen</h2>
        <p className="text-sm text-muted-foreground">Vendor data saved. Launch a full diligence scan.</p>
      </div>

      {errorMsg && (
        <div className="bg-red-50 text-red-700 p-4 rounded-xl border border-red-200 flex items-start gap-3">
          <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
          <span className="text-sm font-medium">{errorMsg}</span>
        </div>
      )}

      <div
        className="bg-card border-2 border-primary rounded-xl p-8 shadow-sm flex flex-col items-center text-center space-y-4 hover:bg-primary/5 cursor-pointer transition"
        onClick={startScan}
      >
        <div className="p-4 bg-primary/10 rounded-full text-primary">
          <ShieldCheck className="w-10 h-10" />
        </div>
        <div>
          <h3 className="text-xl font-semibold">Deep Diligence</h3>
          <p className="text-sm text-muted-foreground mt-1 leading-relaxed">
            Full screening — entity integrity, sanctions, UBO &amp; director checks,
            tax/registration verification, domain intelligence, adverse media, and
            address/digital footprint analysis.
          </p>
        </div>
        <button
          disabled={loading}
          className="w-full bg-primary text-primary-foreground hover:bg-primary/90 h-10 px-4 py-2 rounded-md font-medium disabled:opacity-50 transition-colors"
        >
          {loading ? 'Starting…' : 'Run Deep Diligence'}
        </button>
      </div>
    </div>
  );
};

export default ScanSelector;
