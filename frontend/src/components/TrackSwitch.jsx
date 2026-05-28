import { TrendingUp, DollarSign, Shield } from 'lucide-react'
import { useStore } from '../store/useStore'
import clsx from 'clsx'

const TRACKS = [
  {
    id: 'gtm',
    label: 'GTM Intelligence',
    icon: TrendingUp,
    description: 'Competitors · Pricing · Leads',
    color: 'gtm',
    bg: 'bg-gtm-muted',
    text: 'text-gtm',
    border: 'border-gtm/40',
    activeBorder: 'border-gtm',
  },
  {
    id: 'finance',
    label: 'Finance & Markets',
    icon: DollarSign,
    description: 'Alt-Data · Filings · Risk',
    color: 'finance',
    bg: 'bg-finance-muted',
    text: 'text-finance',
    border: 'border-finance/40',
    activeBorder: 'border-finance',
  },
  {
    id: 'security',
    label: 'Security & Compliance',
    icon: Shield,
    description: 'Threats · Leaks · Regulation',
    color: 'security',
    bg: 'bg-security-muted',
    text: 'text-security',
    border: 'border-security/40',
    activeBorder: 'border-security',
  },
]

export function TrackSwitch() {
  const { activeTrack, setActiveTrack, insights } = useStore()

  return (
    <div className="flex gap-3">
      {TRACKS.map((track) => {
        const Icon = track.icon
        const isActive = activeTrack === track.id
        const count = insights.filter((i) => i.track === track.id).length

        return (
          <button
            key={track.id}
            onClick={() => setActiveTrack(track.id)}
            className={clsx(
              'track-tab flex items-center gap-3 border transition-all',
              isActive
                ? `${track.bg} ${track.text} ${track.activeBorder} shadow-lg`
                : 'border-surface-border text-text-secondary hover:text-text-primary hover:border-surface-elevated hover:bg-surface-elevated'
            )}
          >
            <Icon size={18} className={isActive ? track.text : ''} />
            <div className="text-left">
              <div className="font-semibold text-sm">{track.label}</div>
              <div
                className={clsx(
                  'text-xs',
                  isActive ? 'opacity-80' : 'text-text-muted'
                )}
              >
                {track.description}
              </div>
            </div>
            {count > 0 && (
              <span
                className={clsx(
                  'ml-auto px-2 py-0.5 rounded-full text-xs font-bold',
                  isActive ? 'bg-white/20' : 'bg-surface-elevated'
                )}
              >
                {count}
              </span>
            )}
          </button>
        )
      })}
    </div>
  )
}
