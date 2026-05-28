import { Activity, Eye, Zap, Clock, Play, Square } from 'lucide-react'
import { useState } from 'react'
import { useStore } from '../store/useStore'
import { api } from '../api/client'
import clsx from 'clsx'

function Stat({ icon: Icon, label, value, color }) {
  return (
    <div className="flex items-center gap-2">
      <Icon size={14} className={color || 'text-text-muted'} />
      <div>
        <div className="text-xs text-text-muted">{label}</div>
        <div className="text-sm font-semibold text-text-primary">{value ?? '—'}</div>
      </div>
    </div>
  )
}

export function AutoFocusStatus() {
  const { engineStatus, wsConnected, setEngineStatus } = useStore()
  const [toggling, setToggling] = useState(false)
  const [runningDemo, setRunningDemo] = useState(false)

  const status = engineStatus

  const toggle = async () => {
    setToggling(true)
    try {
      if (status?.running) {
        await api.stopEngine()
      } else {
        await api.startEngine()
      }
      const updated = await api.getStatus()
      setEngineStatus(updated)
    } catch (e) {
      console.error(e)
    } finally {
      setToggling(false)
    }
  }

  const runDemo = async (scenario) => {
    setRunningDemo(true)
    try {
      await api.runDemo(scenario)
    } catch (e) {
      console.error(e)
    } finally {
      setRunningDemo(false)
    }
  }

  return (
    <div className="card space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Activity size={16} className="text-accent" />
          <span className="font-semibold text-sm">Auto-Focus Engine</span>
          <div className="flex items-center gap-1.5">
            <span
              className={clsx(
                'pulse-dot animate-pulse-slow',
                status?.running ? 'bg-finance' : 'bg-surface-border'
              )}
            />
            <span className={clsx('text-xs', status?.running ? 'text-finance' : 'text-text-muted')}>
              {status?.running ? 'Active' : 'Paused'}
            </span>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span
            className={clsx(
              'w-2 h-2 rounded-full',
              wsConnected ? 'bg-finance' : 'bg-security'
            )}
            title={wsConnected ? 'WebSocket connected' : 'WebSocket disconnected'}
          />
          <button
            onClick={toggle}
            disabled={toggling}
            className={clsx(
              'btn text-xs py-1 px-3',
              status?.running
                ? 'bg-security/20 text-security hover:bg-security/30 border border-security/30'
                : 'bg-finance/20 text-finance hover:bg-finance/30 border border-finance/30'
            )}
          >
            {status?.running ? (
              <><Square size={12} /> Stop</>
            ) : (
              <><Play size={12} /> Start</>
            )}
          </button>
        </div>
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-2 gap-x-6 gap-y-3 sm:grid-cols-4">
        <Stat icon={Eye} label="Watching" value={status?.watchlist_count} />
        <Stat icon={Zap} label="Anomalies" value={status?.anomalies_detected} color="text-gtm" />
        <Stat icon={Activity} label="Insights" value={status?.insights_generated} color="text-finance" />
        <Stat
          icon={Clock}
          label="Last check"
          value={
            status?.last_check
              ? new Date(status.last_check).toLocaleTimeString()
              : 'Never'
          }
        />
      </div>

      {/* Demo buttons */}
      <div className="pt-3 border-t border-surface-border">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-xs text-text-muted">Demo scenarios:</span>
          {[
            { key: 'competitor_price_cut', label: '📉 Price Cut' },
            { key: 'data_breach_detected', label: '🔓 Data Breach' },
            { key: 'regulatory_filing', label: '📋 Filing Alert' },
          ].map(({ key, label }) => (
            <button
              key={key}
              onClick={() => runDemo(key)}
              disabled={runningDemo}
              className="text-xs px-3 py-1 rounded border border-surface-border text-text-secondary hover:border-accent hover:text-accent transition-colors disabled:opacity-50"
            >
              {label}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
