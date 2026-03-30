import { useEffect, useRef } from 'react'
import { useStore } from '../store/useStore'
import type { MonitorEvent } from '../types'

export function useWebSocket() {
  const setConnectionStatus = useStore((s) => s.setConnectionStatus)
  const handleLiveEvent = useStore((s) => s.handleLiveEvent)
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    function connect() {
      if (
        wsRef.current &&
        (wsRef.current.readyState === WebSocket.OPEN ||
          wsRef.current.readyState === WebSocket.CONNECTING)
      ) {
        return
      }

      setConnectionStatus('connecting')
      const proto = location.protocol === 'https:' ? 'wss:' : 'ws:'
      const ws = new WebSocket(`${proto}//${location.host}/ws/live`)
      wsRef.current = ws

      ws.onopen = () => {
        setConnectionStatus('connected')
        if (reconnectRef.current) {
          clearTimeout(reconnectRef.current)
          reconnectRef.current = null
        }
      }

      ws.onmessage = (evt) => {
        try {
          handleLiveEvent(JSON.parse(evt.data) as MonitorEvent)
        } catch (e) {
          console.error('WS parse error:', e)
        }
      }

      ws.onclose = () => {
        setConnectionStatus('disconnected')
        scheduleReconnect()
      }

      ws.onerror = () => {
        setConnectionStatus('disconnected')
      }
    }

    function scheduleReconnect() {
      if (reconnectRef.current) return
      reconnectRef.current = setTimeout(() => {
        reconnectRef.current = null
        connect()
      }, 3000)
    }

    connect()

    return () => {
      if (reconnectRef.current) clearTimeout(reconnectRef.current)
      wsRef.current?.close()
    }
  }, [setConnectionStatus, handleLiveEvent])
}
