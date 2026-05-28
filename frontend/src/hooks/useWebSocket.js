import { useEffect, useRef, useCallback } from 'react'
import { useStore } from '../store/useStore'
import { WS_URL } from '../api/client'

export function useWebSocket() {
  const wsRef = useRef(null)
  const reconnectRef = useRef(null)
  const { setWsConnected, setEngineStatus, addInsight, addNotification } = useStore()

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return

    const ws = new WebSocket(WS_URL)
    wsRef.current = ws

    ws.onopen = () => {
      setWsConnected(true)
      console.log('[WS] Connected to NexusIntel engine')
      if (reconnectRef.current) {
        clearTimeout(reconnectRef.current)
        reconnectRef.current = null
      }
    }

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data)

        if (msg.type === 'status') {
          setEngineStatus(msg.data)
        } else if (msg.type === 'insight') {
          const insight = msg.data
          addInsight(insight)
          addNotification({
            id: insight.id,
            title: insight.title,
            track: insight.track,
            impact: insight.impact,
            timestamp: insight.timestamp,
          })
        } else if (msg.type === 'ping') {
          ws.send(JSON.stringify({ type: 'pong' }))
        }
      } catch (e) {
        console.warn('[WS] Parse error:', e)
      }
    }

    ws.onerror = () => {
      setWsConnected(false)
    }

    ws.onclose = () => {
      setWsConnected(false)
      console.log('[WS] Disconnected — reconnecting in 3s...')
      reconnectRef.current = setTimeout(connect, 3000)
    }
  }, [setWsConnected, setEngineStatus, addInsight, addNotification])

  useEffect(() => {
    connect()
    return () => {
      if (reconnectRef.current) clearTimeout(reconnectRef.current)
      wsRef.current?.close()
    }
  }, [connect])
}
