import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Zap, ShieldCheck } from 'lucide-react';

const ScanSelector = () => {
  const { inputId } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);

  const startScan = async (scanType: 'quick' | 'deep') => {
    setLoading(true);
    try {
      const res = await axios.post('http://localhost:8000/scan', {
        input_id: inputId,
        scan_type: scanType
      });
      navigate(`/dashboard/${res.data.scan_id}`);
    } catch (err) {
      console.error(err);
      alert('Error starting scan');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-8 mt-12">
      <div className="text-center space-y-2">
        <h2 className="text-3xl font-semibold tracking-tight">Select Scan Depth</h2>
        <p className="text-muted-foreground">Vendor data saved successfully. Choose how deep you want to screen.</p>
      </div>

      <div className="grid md:grid-cols-2 gap-8">
        <div className="bg-card border rounded-xl p-6 shadow-sm flex flex-col items-center text-center space-y-4 hover:border-primary cursor-pointer transition" onClick={() => startScan('quick')}>
          <div className="p-4 bg-primary/10 rounded-full text-primary">
            <Zap className="w-8 h-8" />
          </div>
          <h3 className="text-xl font-medium">Quick Scan</h3>
          <p className="text-sm text-muted-foreground flex-1">
            ~3 mins. Covers Entity Integrity, Sanctions, Domain Intelligence, and Adverse Media.
          </p>
          <button disabled={loading} className="w-full mt-4 bg-secondary text-secondary-foreground hover:bg-secondary/80 h-10 px-4 py-2 rounded-md font-medium disabled:opacity-50">
            Run Quick Scan
          </button>
        </div>

        <div className="bg-card border rounded-xl p-6 shadow-sm flex flex-col items-center text-center space-y-4 hover:border-primary cursor-pointer transition border-primary" onClick={() => startScan('deep')}>
          <div className="p-4 bg-primary/10 rounded-full text-primary">
            <ShieldCheck className="w-8 h-8" />
          </div>
          <h3 className="text-xl font-medium">Deep Diligence</h3>
          <p className="text-sm text-muted-foreground flex-1">
            ~15 mins. Includes Quick Scan PLUS UBO & Director Screening, Tax/Registration verify, and Address/Digital footprint checks.
          </p>
          <button disabled={loading} className="w-full mt-4 bg-primary text-primary-foreground hover:bg-primary/90 h-10 px-4 py-2 rounded-md font-medium disabled:opacity-50">
            Run Deep Diligence
          </button>
        </div>
      </div>
    </div>
  );
};

export default ScanSelector;
