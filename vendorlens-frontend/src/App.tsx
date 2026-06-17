import { useState } from 'react'
import axios from 'axios'

function App() {
  const [legalName, setLegalName] = useState('')
  const [websiteDomain, setWebsiteDomain] = useState('')
  const [registrationNumber, setRegistrationNumber] = useState('')
  const [result, setResult] = useState<any>(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    setResult(null)

    try {
      const response = await axios.post('http://localhost:8000/api/v1/vendor/intake', {
        legal_name: legalName,
        website_url: websiteDomain,
        registration_number: registrationNumber,
        jurisdiction: "US", // Default for now
        directors: [],
        ubo: []
      })
      
      setResult(response.data)
    } catch (err: any) {
      console.error(err)
      setError(err.response?.data?.detail || err.message || 'An error occurred')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8 bg-white p-8 rounded-lg shadow-md">
        <div>
          <h2 className="text-center text-3xl font-extrabold text-gray-900">
            VendorLens Intake
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Minimal UI for testing FastAPI Backend
          </p>
        </div>
        
        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          <div className="rounded-md shadow-sm space-y-4">
            <div>
              <label htmlFor="legal_name" className="block text-sm font-medium text-gray-700">Legal Name *</label>
              <input
                id="legal_name"
                name="legal_name"
                type="text"
                required
                className="appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm"
                placeholder="Acme Corp Inc."
                value={legalName}
                onChange={(e) => setLegalName(e.target.value)}
              />
            </div>
            
            <div>
              <label htmlFor="website_domain" className="block text-sm font-medium text-gray-700">Website Domain</label>
              <input
                id="website_domain"
                name="website_domain"
                type="text"
                className="appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm"
                placeholder="acmecorp.com"
                value={websiteDomain}
                onChange={(e) => setWebsiteDomain(e.target.value)}
              />
            </div>

            <div>
              <label htmlFor="registration_number" className="block text-sm font-medium text-gray-700">Registration Number</label>
              <input
                id="registration_number"
                name="registration_number"
                type="text"
                className="appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm"
                placeholder="C123456"
                value={registrationNumber}
                onChange={(e) => setRegistrationNumber(e.target.value)}
              />
            </div>
          </div>

          <div>
            <button
              type="submit"
              disabled={loading}
              className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:bg-blue-300"
            >
              {loading ? 'Submitting...' : 'Save Vendor (Intake)'}
            </button>
          </div>
        </form>

        {error && (
          <div className="mt-4 bg-red-50 border-l-4 border-red-400 p-4">
            <div className="flex">
              <div className="ml-3">
                <p className="text-sm text-red-700">{error}</p>
              </div>
            </div>
          </div>
        )}

        {result && (
          <div className="mt-4 bg-green-50 border-l-4 border-green-400 p-4">
            <div className="flex">
              <div className="ml-3">
                <h3 className="text-sm font-medium text-green-800">Success!</h3>
                <div className="mt-2 text-sm text-green-700">
                  <p><strong>Input ID:</strong> {result.input_id}</p>
                  <p><strong>Message:</strong> {result.message}</p>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default App
