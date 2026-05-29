import { useState } from 'react'
import { Search, FileText, TrendingDown, Database, Loader2, ExternalLink } from 'lucide-react'
import { InsightBrief } from './InsightBrief'
import { useStore } from '../store/useStore'
import { api } from '../api/client'
import { toText } from '../utils'

function ResultList({ results, emptyLabel = 'No signals found.' }) {
  if (!results) return null
  if (!results.length) return <p className="text-xs text-text-muted italic mt-1">{emptyLabel}</p>
  return (
    <ul className="space-y-2 max-h-64 overflow-y-auto mt-2">
      {results.map((r, i) => (
        <li key={i} className="text-sm border-b border-surface-border pb-2 last:border-0">
          <a href={r.url} target="_blank" rel="noopener noreferrer"
            className="flex items-start gap-1 text-finance hover:underline font-medium">
            {r.title} <ExternalLink size={11} className="mt-0.5 flex-shrink-0" />
          </a>
          <p className="text-text-muted text-xs mt-0.5">{r.snippet}</p>
        </li>
      ))}
    </ul>
  )
}

function PricingAnomalyScanner() {
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)

  const scan = async () => {
    if (!query.trim()) return
    setLoading(true)
    setResult(null)
    try {
      const data = await api.getPricingAnomalies(query.trim())
      setResult(data)
    } catch (e) {
      setResult({ error: e.message })
    } finally {
      setLoading(false)
    }
  }

  const analysis = result?.anomaly_analysis

  return (
    <div className="card space-y-3">
      <h3 className="font-semibold text-sm flex items-center gap-2">
        <TrendingDown size={14} className="text-finance" />
        Pricing Anomaly Scanner
      </h3>
      <div className="flex gap-2">
        <input
          className="input flex-1"
          placeholder="Product name (e.g. iPhone 16)"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && scan()}
        />
        <button className="btn text-xs bg-finance/20 text-finance hover:bg-finance/30 border border-finance/30"
          disabled={loading || !query.trim()} onClick={scan}>
          {loading ? <Loader2 size={14} className="animate-spin" /> : 'Scan'}
        </button>
      </div>
      {analysis && typeof analysis === 'object' && (
        <div className="space-y-2 text-sm">
          {analysis.anomalies_found && (
            <div className="badge-high inline-flex badge mb-1">Anomalies detected</div>
          )}
          {analysis.summary && <p className="text-text-secondary text-xs">{toText(analysis.summary)}</p>}
          {analysis.anomalies?.map((a, i) => (
            <div key={i} className="bg-surface-elevated rounded p-2 text-xs">
              <span className="text-text-primary font-medium">{toText(a?.platform)}</span>
              {a?.price != null && <span className="text-finance ml-2">{toText(a.price)}</span>}
              <p className="text-text-muted mt-0.5">{toText(a?.context)}</p>
            </div>
          ))}
          {!analysis.summary && !analysis.anomalies?.length && (
            <p className="text-xs text-text-muted italic">Scanner returned no anomalies for this product.</p>
          )}
        </div>
      )}
      {typeof analysis === 'string' && <p className="text-xs text-yellow-400">{analysis}</p>}
      {result?.error && <p className="text-security text-xs">{result.error}</p>}
    </div>
  )
}

function AltDataPanel() {
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)

  const fetch_ = async () => {
    if (!query.trim()) return
    setLoading(true)
    try {
      const data = await api.getAltData(query.trim())
      setResult(data)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="card space-y-3">
      <h3 className="font-semibold text-sm flex items-center gap-2">
        <Database size={14} className="text-finance" />
        Alternative Data Feed
      </h3>
      <div className="flex gap-2">
        <input
          className="input flex-1"
          placeholder="Company (e.g. Stripe)"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && fetch_()}
        />
        <button className="btn text-xs bg-finance/20 text-finance hover:bg-finance/30 border border-finance/30"
          disabled={loading || !query.trim()} onClick={fetch_}>
          {loading ? <Loader2 size={14} className="animate-spin" /> : 'Fetch'}
        </button>
      </div>
      {result && (
        <div className="space-y-3">
          <div>
            <div className="text-xs font-semibold text-text-muted uppercase mb-1">Hiring Signals</div>
            <ResultList results={result.hiring_signals} />
          </div>
          <div>
            <div className="text-xs font-semibold text-text-muted uppercase mb-1">Traffic Signals</div>
            <ResultList results={result.traffic_signals} />
          </div>
        </div>
      )}
    </div>
  )
}

function FilingsPanel() {
  const [company, setCompany] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)

  const fetch_ = async () => {
    setLoading(true)
    try {
      const data = await api.getRegulatoryFilings(company.trim() || undefined)
      setResult(data)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="card space-y-3">
      <h3 className="font-semibold text-sm flex items-center gap-2">
        <FileText size={14} className="text-finance" />
        SEC Regulatory Filings
      </h3>
      <div className="flex gap-2">
        <input
          className="input flex-1"
          placeholder="Company name (optional)"
          value={company}
          onChange={(e) => setCompany(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && fetch_()}
        />
        <button className="btn text-xs bg-finance/20 text-finance hover:bg-finance/30 border border-finance/30"
          disabled={loading} onClick={fetch_}>
          {loading ? <Loader2 size={14} className="animate-spin" /> : 'Fetch'}
        </button>
      </div>
      {result?.content_preview && (
        <pre className="text-xs text-text-secondary bg-surface-elevated rounded p-3 overflow-auto max-h-48 whitespace-pre-wrap">
          {result.content_preview}
        </pre>
      )}
      {result && !result.content_preview && (
        <p className="text-xs text-security">
          {result.error || 'SEC EDGAR returned no content.'}
        </p>
      )}
    </div>
  )
}

export function FinanceDashboard() {
  const { insights } = useStore()
  const trackInsights = insights.filter((i) => i.track === 'finance')

  return (
    <div className="space-y-6 animate-fade-in">
      <section>
        <h2 className="text-sm font-semibold text-text-muted uppercase tracking-wide mb-3">
          Finance Critical Insights ({trackInsights.length})
        </h2>
        {trackInsights.length === 0 ? (
          <div className="card text-center py-10 text-text-muted text-sm">
            No Finance insights yet — monitoring SEC filings and alt-data streams.
            <br />
            <span className="text-xs">Use the "Filing Alert" demo scenario above.</span>
          </div>
        ) : (
          <div className="space-y-3">
            {trackInsights.map((insight) => (
              <InsightBrief key={insight.id} insight={insight} />
            ))}
          </div>
        )}
      </section>

      <section className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <PricingAnomalyScanner />
        <AltDataPanel />
        <FilingsPanel />
      </section>
    </div>
  )
}
