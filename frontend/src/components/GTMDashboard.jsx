import { useState } from 'react'
import { Search, TrendingUp, Users, ExternalLink, Loader2 } from 'lucide-react'
import { InsightBrief } from './InsightBrief'
import { useStore } from '../store/useStore'
import { api } from '../api/client'
import { toText } from '../utils'

function SearchPanel({ title, placeholder, onSearch, loading, results, searched }) {
  const [query, setQuery] = useState('')

  return (
    <div className="card space-y-3">
      <h3 className="font-semibold text-sm flex items-center gap-2">
        <Search size={14} className="text-gtm" />
        {title}
      </h3>
      <div className="flex gap-2">
        <input
          className="input flex-1"
          placeholder={placeholder}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && query.trim() && onSearch(query)}
        />
        <button
          className="btn-primary text-xs"
          disabled={loading || !query.trim()}
          onClick={() => onSearch(query)}
        >
          {loading ? <Loader2 size={14} className="animate-spin" /> : 'Search'}
        </button>
      </div>
      {results?.length > 0 ? (
        <ul className="space-y-2 max-h-64 overflow-y-auto">
          {results.map((r, i) => (
            <li key={i} className="text-sm border-b border-surface-border pb-2 last:border-0">
              <a
                href={r.url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-start gap-1 text-accent hover:underline font-medium"
              >
                {r.title} <ExternalLink size={11} className="mt-0.5 flex-shrink-0" />
              </a>
              <p className="text-text-muted text-xs mt-0.5">{r.snippet}</p>
            </li>
          ))}
        </ul>
      ) : searched && !loading ? (
        <p className="text-xs text-text-muted italic">No results returned — try a broader query.</p>
      ) : null}
    </div>
  )
}

function CompetitorAnalyzer() {
  const [url, setUrl] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)

  const analyze = async () => {
    if (!url.trim()) return
    setLoading(true)
    setResult(null)
    try {
      const data = await api.analyzeCompetitor(url.trim())
      setResult(data)
    } catch (e) {
      setResult({ error: e.message })
    } finally {
      setLoading(false)
    }
  }

  const analysis = result?.analysis

  return (
    <div className="card space-y-3">
      <h3 className="font-semibold text-sm flex items-center gap-2">
        <TrendingUp size={14} className="text-gtm" />
        Competitor Analyzer
      </h3>
      <div className="flex gap-2">
        <input
          className="input flex-1"
          placeholder="https://competitor.com/pricing"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && analyze()}
        />
        <button className="btn-primary text-xs" disabled={loading || !url.trim()} onClick={analyze}>
          {loading ? <Loader2 size={14} className="animate-spin" /> : 'Analyze'}
        </button>
      </div>

      {analysis && typeof analysis === 'object' && !analysis.error && (
        <div className="space-y-3 text-sm">
          {analysis.pricing?.length > 0 && (
            <div>
              <div className="text-xs text-text-muted font-semibold uppercase mb-1">Pricing</div>
              <ul className="space-y-1">
                {analysis.pricing.map((p, i) => (
                  <li key={i} className="text-text-secondary font-mono text-xs bg-surface-elevated rounded px-2 py-1">{toText(p)}</li>
                ))}
              </ul>
            </div>
          )}
          {analysis.key_messages?.length > 0 && (
            <div>
              <div className="text-xs text-text-muted font-semibold uppercase mb-1">Key Messages</div>
              <ul className="list-disc list-inside space-y-1 text-text-secondary text-xs">
                {analysis.key_messages.map((m, i) => <li key={i}>{toText(m)}</li>)}
              </ul>
            </div>
          )}
          {analysis.products?.length > 0 && (
            <div>
              <div className="text-xs text-text-muted font-semibold uppercase mb-1">Products</div>
              <ul className="list-disc list-inside space-y-1 text-text-secondary text-xs">
                {analysis.products.map((p, i) => <li key={i}>{toText(p)}</li>)}
              </ul>
            </div>
          )}
          {analysis.hiring_signals?.length > 0 && (
            <div>
              <div className="text-xs text-text-muted font-semibold uppercase mb-1">Hiring Signals</div>
              <ul className="list-disc list-inside space-y-1 text-text-secondary text-xs">
                {analysis.hiring_signals.map((h, i) => <li key={i}>{toText(h)}</li>)}
              </ul>
            </div>
          )}
          {analysis.raw && (
            <pre className="text-xs text-text-muted bg-surface-elevated rounded p-2 overflow-x-auto whitespace-pre-wrap">
              {toText(analysis.raw)}
            </pre>
          )}
        </div>
      )}
      {result?.error && (
        <p className="text-security text-xs">{result.error}</p>
      )}
      {typeof analysis === 'string' && (
        <p className="text-xs text-yellow-400">{analysis}</p>
      )}
      {result && !analysis && !result.error && (
        <p className="text-xs text-text-muted italic">Analyzer returned no structured data — try a different URL.</p>
      )}
    </div>
  )
}

export function GTMDashboard() {
  const { insights } = useStore()
  const trackInsights = insights.filter((i) => i.track === 'gtm')
  const [searchLoading, setSearchLoading] = useState(false)
  const [searchResults, setSearchResults] = useState([])
  const [searched, setSearched] = useState(false)
  const [hiringLoading, setHiringLoading] = useState(false)
  const [hiringResults, setHiringResults] = useState([])
  const [hiringSearched, setHiringSearched] = useState(false)

  const handleSearch = async (query) => {
    setSearchLoading(true)
    try {
      const data = await api.gtmSearch(query)
      setSearchResults(data.results || [])
    } catch (e) {
      console.error(e)
      setSearchResults([])
    } finally {
      setSearched(true)
      setSearchLoading(false)
    }
  }

  const handleHiring = async (company) => {
    setHiringLoading(true)
    try {
      const data = await api.getHiringSignals(company)
      setHiringResults(data.hiring_signals || [])
    } catch (e) {
      console.error(e)
      setHiringResults([])
    } finally {
      setHiringSearched(true)
      setHiringLoading(false)
    }
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Auto-Focus Insights */}
      <section>
        <h2 className="text-sm font-semibold text-text-muted uppercase tracking-wide mb-3">
          GTM Critical Insights ({trackInsights.length})
        </h2>
        {trackInsights.length === 0 ? (
          <div className="card text-center py-10 text-text-muted text-sm">
            No GTM insights yet — the engine is monitoring competitors in real time.
            <br />
            <span className="text-xs">Use a Demo scenario above to see an example insight.</span>
          </div>
        ) : (
          <div className="space-y-3">
            {trackInsights.map((insight) => (
              <InsightBrief key={insight.id} insight={insight} />
            ))}
          </div>
        )}
      </section>

      {/* Tools */}
      <section className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <CompetitorAnalyzer />
        <SearchPanel
          title="Web Intelligence Search"
          placeholder="Search competitors, market signals..."
          onSearch={handleSearch}
          loading={searchLoading}
          results={searchResults}
          searched={searched}
        />
        <SearchPanel
          title="Hiring Signal Detector"
          placeholder="Company name (e.g. Salesforce)"
          onSearch={handleHiring}
          loading={hiringLoading}
          results={hiringResults}
          searched={hiringSearched}
        />
      </section>
    </div>
  )
}
