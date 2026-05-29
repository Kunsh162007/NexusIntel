import { useState } from 'react'
import { Shield, AlertTriangle, Eye, Globe, Loader2, ExternalLink } from 'lucide-react'
import { InsightBrief } from './InsightBrief'
import { useStore } from '../store/useStore'
import { api } from '../api/client'
import clsx from 'clsx'

function SeverityBadge({ severity }) {
  const map = {
    Critical: 'badge-critical',
    High: 'badge-high',
    Medium: 'badge-medium',
    Low: 'badge-low',
    None: 'bg-surface-elevated text-text-muted',
  }
  return <span className={clsx('badge', map[severity] || map.None)}>{severity}</span>
}

function ThreatScanner() {
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)

  const scan = async () => {
    if (!query.trim()) return
    setLoading(true)
    setResult(null)
    try {
      const data = await api.threatScan(query.trim())
      setResult(data)
    } catch (e) {
      setResult({ error: e.message })
    } finally {
      setLoading(false)
    }
  }

  const analysis = result?.threat_analysis

  return (
    <div className="card space-y-3">
      <h3 className="font-semibold text-sm flex items-center gap-2">
        <AlertTriangle size={14} className="text-security" />
        Threat Scanner
      </h3>
      <div className="flex gap-2">
        <input
          className="input flex-1"
          placeholder="Brand, product, company name..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && scan()}
        />
        <button className="btn text-xs bg-security/20 text-security hover:bg-security/30 border border-security/30"
          disabled={loading || !query.trim()} onClick={scan}>
          {loading ? <Loader2 size={14} className="animate-spin" /> : 'Scan'}
        </button>
      </div>
      {analysis && typeof analysis === 'object' && (
        <div className="space-y-2">
          {(analysis.overall_severity || analysis.summary) && (
            <div className="flex items-center gap-2">
              {analysis.overall_severity && <SeverityBadge severity={analysis.overall_severity} />}
              <span className="text-xs text-text-secondary">{analysis.summary}</span>
            </div>
          )}
          {analysis.threats?.map((t, i) => (
            <div key={i} className="bg-surface-elevated rounded p-2 text-xs space-y-1">
              <div className="flex items-center gap-2">
                <SeverityBadge severity={t.severity} />
                <span className="text-text-primary font-medium">{t.type}</span>
              </div>
              <p className="text-text-muted">{t.description}</p>
            </div>
          ))}
          {analysis.recommendations?.length > 0 && (
            <div className="pt-2 border-t border-surface-border">
              <div className="text-xs font-semibold text-text-muted uppercase mb-1">Actions</div>
              <ul className="space-y-1">
                {analysis.recommendations.map((r, i) => (
                  <li key={i} className="text-xs text-text-secondary flex gap-1.5">
                    <span className="text-security">→</span>{r}
                  </li>
                ))}
              </ul>
            </div>
          )}
          {!analysis.summary && !analysis.threats?.length && !analysis.recommendations?.length && (
            <p className="text-xs text-text-muted italic">Scanner returned no structured threats for this query.</p>
          )}
        </div>
      )}
      {typeof analysis === 'string' && <p className="text-xs text-yellow-400">{analysis}</p>}
      {result?.error && <p className="text-security text-xs">{result.error}</p>}
    </div>
  )
}

function CredentialChecker() {
  const [domain, setDomain] = useState('')
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState(null)

  const check = async () => {
    if (!domain.trim()) return
    setLoading(true)
    try {
      const data = await api.credentialCheck(domain.trim())
      setResults(data)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="card space-y-3">
      <h3 className="font-semibold text-sm flex items-center gap-2">
        <Shield size={14} className="text-security" />
        Credential Leak Checker
      </h3>
      <div className="flex gap-2">
        <input
          className="input flex-1"
          placeholder="example.com"
          value={domain}
          onChange={(e) => setDomain(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && check()}
        />
        <button className="btn text-xs bg-security/20 text-security hover:bg-security/30 border border-security/30"
          disabled={loading || !domain.trim()} onClick={check}>
          {loading ? <Loader2 size={14} className="animate-spin" /> : 'Check'}
        </button>
      </div>
      {results?.results?.length > 0 ? (
        <ul className="space-y-2 max-h-48 overflow-y-auto">
          {results.results.map((r, i) => (
            <li key={i} className="text-xs border-b border-surface-border pb-1.5 last:border-0">
              <a href={r.url} target="_blank" rel="noopener noreferrer"
                className="text-security hover:underline flex items-center gap-1">
                {r.title} <ExternalLink size={10} />
              </a>
              <p className="text-text-muted mt-0.5">{r.snippet}</p>
            </li>
          ))}
        </ul>
      ) : results && !loading ? (
        <p className="text-xs text-text-muted italic">No public leak mentions found for this domain.</p>
      ) : null}
    </div>
  )
}

function RegulatoryPanel() {
  const [region, setRegion] = useState('global')
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState(null)

  const fetch_ = async () => {
    setLoading(true)
    try {
      const data = await api.getRegulatoryChanges(region)
      setResults(data)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="card space-y-3">
      <h3 className="font-semibold text-sm flex items-center gap-2">
        <Globe size={14} className="text-security" />
        Regulatory Change Tracker
      </h3>
      <div className="flex gap-2">
        <select className="input flex-1" value={region} onChange={(e) => setRegion(e.target.value)}>
          <option value="global">Global</option>
          <option value="us">United States</option>
          <option value="eu">European Union</option>
        </select>
        <button className="btn text-xs bg-security/20 text-security hover:bg-security/30 border border-security/30"
          disabled={loading} onClick={fetch_}>
          {loading ? <Loader2 size={14} className="animate-spin" /> : 'Fetch'}
        </button>
      </div>
      {results?.regulatory_updates?.length > 0 ? (
        <ul className="space-y-2 max-h-64 overflow-y-auto">
          {results.regulatory_updates.map((r, i) => (
            <li key={i} className="text-xs border-b border-surface-border pb-1.5 last:border-0">
              <a href={r.url} target="_blank" rel="noopener noreferrer"
                className="text-accent hover:underline flex items-center gap-1 font-medium">
                {r.title} <ExternalLink size={10} />
              </a>
              <p className="text-text-muted mt-0.5">{r.snippet}</p>
            </li>
          ))}
        </ul>
      ) : results && !loading ? (
        <p className="text-xs text-text-muted italic">No regulatory updates returned for this region.</p>
      ) : null}
    </div>
  )
}

export function SecurityDashboard() {
  const { insights } = useStore()
  const trackInsights = insights.filter((i) => i.track === 'security')

  return (
    <div className="space-y-6 animate-fade-in">
      <section>
        <h2 className="text-sm font-semibold text-text-muted uppercase tracking-wide mb-3">
          Security Critical Insights ({trackInsights.length})
        </h2>
        {trackInsights.length === 0 ? (
          <div className="card text-center py-10 text-text-muted text-sm">
            No Security insights yet — monitoring CISA advisories and threat feeds.
            <br />
            <span className="text-xs">Use the "Data Breach" demo scenario above.</span>
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
        <ThreatScanner />
        <CredentialChecker />
        <RegulatoryPanel />
      </section>
    </div>
  )
}
