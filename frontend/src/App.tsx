import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import IntakeForm from './components/IntakeForm';
import ScanSelector from './components/ScanSelector';
import Dashboard from './components/Dashboard';

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-background text-foreground flex flex-col font-sans selection:bg-primary/20">
        <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 shadow-sm">
          <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Link to="/" className="flex items-center gap-2 group">
                <div className="bg-primary/10 p-1.5 rounded-lg group-hover:bg-primary/20 transition-colors">
                  <div className="w-5 h-5 rounded-md bg-primary flex items-center justify-center">
                    <div className="w-2 h-2 bg-background rounded-full" />
                  </div>
                </div>
                <span className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-primary to-primary/70 tracking-tight">
                  VendorLens
                </span>
              </Link>
            </div>
            <nav className="flex items-center gap-6">
              <span className="text-sm font-medium text-muted-foreground hidden md:inline-block">
                Automated KYB & Vendor Due Diligence
              </span>
              <a href="https://github.com" target="_blank" rel="noreferrer" className="text-sm font-medium hover:text-primary transition-colors">
                Documentation
              </a>
            </nav>
          </div>
        </header>
        <main className="flex-1 w-full max-w-7xl mx-auto p-6 md:p-10 animate-in fade-in duration-500">
          <Routes>
            <Route path="/" element={<IntakeForm />} />
            <Route path="/scan/:inputId" element={<ScanSelector />} />
            <Route path="/dashboard/:scanId" element={<Dashboard />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

export default App;
