import { AlertTriangle, AlertCircle, Info, CheckCircle, ExternalLink, ChevronDown, ChevronUp, Link } from 'lucide-react'
import { useState } from 'react'
import clsx from 'clsx'
import { toText } from '../utils'

const IMPACT_CONFIG = {
  Critical: { icon: AlertTriangle, class: 'badge-critical', bar: 'bg-red-500' },
  High: { icon: AlertCircle, class: 'badge-high', bar: 'bg-orange-500' },
  Medium: { icon: Info, class: 'badge-medium', bar: 'bg-yellow-500' },
  Low: { icon: CheckCircle, class: 'badge-low', bar: 'bg-green-500' },
}

const TRACK_CONFIG = {
  gtm: { label: 'GTM', color: 'text-gtm', bg: 'bg-gtm/10' },
  finance: { label: 'Finance', color: 'text-finance', bg: 'bg-finance/10' },
  security: { label: 'Security', color: 'text-security', bg: 'bg-security/10' },
}

function RelativeTime({ timestamp }) {
  const diff = Date.now() - new Date(timestamp).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return <span>just now</span>
  if (mins < 60) return <span>{mins}m ago</span>
  const hours = Math.floor(mins / 60)
  if (hours < 24) return <span>{hours}h ago</span>
  return <span>{Math.floor(hours / 24)}d ago</span>
}

export function InsightBrief({ insight }) {
  const [expanded, setExpanded] = useState(false)
  const impact = IMPACT_CONFIG[insight.impact] || IMPACT_CONFIG.Medium
  const track = TRACK_CONFIG[insight.track] || TRACK_CONFIG.gtm
  const Icon = impact.icon

  return (
    <div
      className={clsx(
        'card border-l-4 animate-slide-in transition-shadow hover:shadow-lg',
        {
          'border-l-red-500': insight.impact === 'Critical',
          'border-l-orange-500': insight.impact === 'High',
          'border-l-yellow-500': insight.impact === 'Medium',
          'border-l-green-500': insight.impact === 'Low',
        }
      )}
    >
      {/* Header */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-3 flex-1 min-w-0">
          <div className={clsx('p-2 rounded-lg mt-0.5', impact.class.replace('badge-', 'bg-').replace('critical', 'red-900/40').replace('high', 'orange-900/40').replace('medium', 'yellow-900/40').replace('low', 'green-900/40'))}>
            <Icon size={16} />
          </div>
          <div className="flex-1 min-w-0">
            <h3 className="font-semibold text-text-primary text-sm leading-snug mb-1">
              {insight.title}
            </h3>
            <div className="flex items-center gap-2 flex-wrap">
              <span className={clsx('badge', impact.class)}>
                <Icon size={10} />
                {insight.impact}
              </span>
              <span className={clsx('badge', track.bg, track.color)}>
                {track.label}
              </span>
              {insight.cross_track_links?.length > 0 && (
                <span className="badge bg-surface-elevated text-text-muted">
                  <Link size={10} />
                  {insight.cross_track_links.join(', ')}
                </span>
              )}
              <span className="text-xs text-text-muted">
                <RelativeTime timestamp={insight.timestamp} />
              </span>
            </div>
          </div>
        </div>
        <button
          onClick={() => setExpanded((v) => !v)}
          className="text-text-muted hover:text-text-primary transition-colors p-1 flex-shrink-0"
        >
          {expanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
        </button>
      </div>

      {/* Summary */}
      <p className="text-text-secondary text-sm mt-3 leading-relaxed">
        {insight.summary}
      </p>

      {/* Expanded details */}
      {expanded && (
        <div className="mt-4 space-y-4 animate-fade-in">
          {/* Recommendations */}
          <div>
            <h4 className="text-xs font-semibold text-text-muted uppercase tracking-wide mb-2">
              Recommendations
            </h4>
            <ul className="space-y-1.5">
              {insight.recommendations?.map((rec, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-text-secondary">
                  <span className="text-accent mt-0.5 flex-shrink-0">→</span>
                  {toText(rec)}
                </li>
              ))}
            </ul>
          </div>

          {/* Metadata */}
          <div className="flex items-center gap-4 pt-3 border-t border-surface-border">
            {insight.source_url && (
              <a
                href={insight.source_url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-1 text-xs text-accent hover:underline"
              >
                <ExternalLink size={12} />
                {insight.source_name || 'Source'}
              </a>
            )}
            {insight.similarity_score > 0 && (
              <span className="text-xs text-text-muted font-mono">
                Δ similarity: {(1 - insight.similarity_score).toFixed(3)}
              </span>
            )}
            <span className="text-xs text-text-muted font-mono ml-auto">
              {insight.id?.slice(0, 8)}
            </span>
          </div>
        </div>
      )}
    </div>
  )
}
