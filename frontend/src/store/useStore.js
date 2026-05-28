import { create } from 'zustand'

export const useStore = create((set, get) => ({
  // Active track
  activeTrack: 'gtm',
  setActiveTrack: (track) => set({ activeTrack: track }),

  // Engine status
  engineStatus: null,
  setEngineStatus: (status) => set({ engineStatus: status }),

  // Insights (all tracks combined)
  insights: [],
  addInsight: (insight) =>
    set((state) => ({
      insights: [insight, ...state.insights].slice(0, 200),
    })),
  setInsights: (insights) => set({ insights }),

  // Filtered insights by track
  getTrackInsights: (track) => get().insights.filter((i) => i.track === track),

  // WebSocket state
  wsConnected: false,
  setWsConnected: (v) => set({ wsConnected: v }),

  // Loading states
  loading: {},
  setLoading: (key, val) =>
    set((state) => ({ loading: { ...state.loading, [key]: val } })),

  // Track-specific search results
  searchResults: {},
  setSearchResults: (track, results) =>
    set((state) => ({ searchResults: { ...state.searchResults, [track]: results } })),

  // Notifications (new insight alerts)
  notifications: [],
  addNotification: (n) =>
    set((state) => ({ notifications: [n, ...state.notifications].slice(0, 20) })),
  clearNotifications: () => set({ notifications: [] }),

  // Voice
  voiceActive: false,
  setVoiceActive: (v) => set({ voiceActive: v }),
  lastTranscript: '',
  setLastTranscript: (t) => set({ lastTranscript: t }),
}))
