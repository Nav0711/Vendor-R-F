import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import IntakeForm from './components/IntakeForm';
import ScanSelector from './components/ScanSelector';
import Dashboard from './components/Dashboard';

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-background text-foreground flex flex-col">
        <header className="border-b px-6 py-4 flex items-center justify-between">
          <Link to="/" className="text-2xl font-bold text-primary tracking-tight hover:opacity-80 transition-opacity">
            VendorLens
          </Link>
          <nav className="text-sm font-medium">Automated KYB & Vendor Due Diligence</nav>
        </header>
        <main className="flex-1 p-6 max-w-7xl w-full mx-auto">
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
