import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { ShieldCheck, ArrowLeft, AlertCircle } from 'lucide-react';

const ScanSelector = () => {
  const { inputId } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const startScan = async () => {
    setLoading(true);
    setErrorMsg(null);
    try {
      const res = await axios.post('http://localhost:8000/scan', {
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
    <div className="max-w-2xl mx-auto space-y-8 mt-12 relative animate-in fade-in slide-in-from-bottom-4 duration-500">
      <button
        onClick={() => navigate(-1)}
        disabled={loading}
        className="absolute -top-14 left-0 inline-flex items-center text-sm font-medium text-muted-foreground hover:text-foreground transition-colors disabled:opacity-50"
      >
        <ArrowLeft className="w-4 h-4 mr-1.5" /> Go Back
      </button>

      <div className="text-center space-y-2">
        <h2 className="text-3xl font-bold tracking-tight text-foreground">Ready to Screen</h2>
        <p className="text-base text-muted-foreground">Vendor data saved. Launch a comprehensive diligence scan.</p>
      </div>

      {errorMsg && (
        <div className="bg-destructive/10 text-destructive p-4 rounded-xl border border-destructive/20 flex items-start gap-3 animate-in fade-in zoom-in-95">
          <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
          <span className="text-sm font-medium">{errorMsg}</span>
        </div>
      )}

      <div className="grid grid-cols-1 gap-6">
        <div
          className={`relative bg-card border-2 rounded-2xl p-8 shadow-sm flex flex-col items-center text-center space-y-6 transition-all duration-300 ${
            loading 
              ? 'border-primary/50 opacity-80 cursor-wait' 
              : 'border-transparent hover:border-primary/50 hover:shadow-xl hover:shadow-primary/5 cursor-pointer group overflow-hidden'
          }`}
          onClick={loading ? undefined : startScan}
        >
          {/* Subtle gradient background effect on hover */}
          <div className="absolute inset-0 bg-gradient-to-br from-primary/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none" />

          <div className="relative p-5 bg-primary/10 rounded-2xl text-primary group-hover:scale-110 group-hover:bg-primary group-hover:text-primary-foreground transition-all duration-300">
            <ShieldCheck className="w-12 h-12" />
          </div>
          
          <div className="relative z-10 space-y-3">
            <h3 className="text-2xl font-bold">Deep Diligence</h3>
            <p className="text-sm text-muted-foreground leading-relaxed max-w-md mx-auto">
              Full screening — entity integrity, sanctions, UBO &amp; director checks,
              tax/registration verification, domain intelligence, adverse media, and
              address/digital footprint analysis.
            </p>
          </div>

          <button
            disabled={loading}
            className="relative z-10 w-full max-w-xs bg-primary text-primary-foreground hover:bg-primary/90 h-12 px-6 rounded-xl font-semibold disabled:opacity-70 transition-colors shadow-sm flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <div className="w-5 h-5 border-2 border-primary-foreground/30 border-t-primary-foreground rounded-full animate-spin" />
                Starting Scan...
              </>
            ) : (
              'Run Deep Diligence'
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ScanSelector;
