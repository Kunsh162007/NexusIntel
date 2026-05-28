import { useEffect } from 'react'
import { Brain, Bell, X } from 'lucide-react'
import { useStore } from './store/useStore'
import { useWebSocket } from './hooks/useWebSocket'
import { api } from './api/client'
import { TrackSwitch } from './components/TrackSwitch'
import { AutoFocusStatus } from './components/AutoFocusStatus'
import { GTMDashboard } from './components/GTMDashboard'
import { FinanceDashboard } from './components/FinanceDashboard'
import { SecurityDashboard } from './components/SecurityDashboard'
import { VoiceControl } from './components/VoiceControl'
import clsx from 'clsx'

const IMPACT_COLORS = {
  Critical: 'border-l-red-500 bg-red-900/10',
  High: 'border-l-orange-500 bg-orange-900/10',
  Medium: 'border-l-yellow-500 bg-yellow-900/10',
  Low: 'border-l-green-500 bg-green-900/10',
}

function NotificationToast() {
  const { notifications, clearNotifications } = useStore()
  const latest = notifications[0]
  if (!latest) return null

  return (
    <div
      className={clsx(
        'fixed bottom-5 right-5 z-50 w-80 card border-l-4 shadow-xl animate-slide-in',
        IMPACT_COLORS[latest.impact] || IMPACT_COLORS.Medium
      )}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          <div className="text-xs font-semibold text-text-muted uppercase mb-0.5">
            New {latest.track?.toUpperCase()} Insight · {latest.impact}
          </div>
          <p className="text-sm text-text-primary font-medium leading-snug">{latest.title}</p>
        </div>
        <button
          onClick={clearNotifications}
          className="text-text-muted hover:text-text-primary transition-colors flex-shrink-0"
        >
          <X size={14} />
        </button>
      </div>
    </div>
  )
}

export default function App() {
  const { activeTrack, setInsights, setEngineStatus } = useStore()

  useWebSocket()

  useEffect(() => {
    // Load initial insights and engine status
    Promise.allSettled([
      api.getInsights(null, 100).then(setInsights),
      api.getStatus().then(setEngineStatus),
    ])
  }, [setInsights, setEngineStatus])

  return (
    <div className="min-h-screen bg-surface">
      {/* Top bar */}
      <header className="border-b border-surface-border sticky top-0 z-40 bg-surface/95 backdrop-blur">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 h-14 flex items-center justify-between gap-4">
          {/* Logo */}
          <div className="flex items-center gap-2 flex-shrink-0">
            <div className="p-1.5 bg-accent/10 rounded-lg">
              <Brain size={18} className="text-accent" />
            </div>
            <div>
              <span className="font-bold text-text-primary text-sm">NexusIntel</span>
              <span className="text-accent font-bold text-sm"> AI</span>
            </div>
            <span className="hidden sm:inline text-xs text-text-muted border border-surface-border rounded px-1.5 py-0.5 ml-1">
              v1.0
            </span>
          </div>

          {/* Voice + Notifications */}
          <div className="flex items-center gap-3 ml-auto">
            <VoiceControl />
            <NotificationBell />
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-6 space-y-6">
        {/* Engine status */}
        <AutoFocusStatus />

        {/* Track switch */}
        <div className="overflow-x-auto pb-1">
          <TrackSwitch />
        </div>

        {/* Track content */}
        {activeTrack === 'gtm' && <GTMDashboard />}
        {activeTrack === 'finance' && <FinanceDashboard />}
        {activeTrack === 'security' && <SecurityDashboard />}
      </main>

      {/* Toast notification */}
      <NotificationToast />

      {/* Footer */}
      <footer className="border-t border-surface-border mt-12 py-4">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 flex items-center justify-between text-xs text-text-muted">
          <span>NexusIntel AI · Web Data UNLOCKED Hackathon · Bright Data × lablab.ai</span>
          <span className="font-mono">GTM · Finance · Security</span>
        </div>
      </footer>
    </div>
  )
}

function NotificationBell() {
  const { notifications, clearNotifications } = useStore()
  if (!notifications.length) return null

  return (
    <button
      onClick={clearNotifications}
      className="relative p-2 rounded-lg text-text-secondary hover:text-text-primary hover:bg-surface-elevated transition-colors"
    >
      <Bell size={16} />
      <span className="absolute top-1 right-1 w-2 h-2 bg-security rounded-full" />
    </button>
  )
}
