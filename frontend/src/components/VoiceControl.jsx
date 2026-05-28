import { useState, useRef, useCallback } from 'react'
import { Mic, MicOff, Volume2, Loader2 } from 'lucide-react'
import { useStore } from '../store/useStore'
import { api } from '../api/client'
import clsx from 'clsx'

function blobToBase64(blob) {
  return new Promise((resolve) => {
    const reader = new FileReader()
    reader.onloadend = () => {
      const base64 = reader.result.split(',')[1]
      resolve(base64)
    }
    reader.readAsDataURL(blob)
  })
}

export function VoiceControl() {
  const { voiceActive, setVoiceActive, lastTranscript, setLastTranscript, setActiveTrack } = useStore()
  const [recording, setRecording] = useState(false)
  const [processing, setProcessing] = useState(false)
  const [status, setStatus] = useState('')
  const mediaRecorderRef = useRef(null)
  const chunksRef = useRef([])

  const startRecording = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const mr = new MediaRecorder(stream, { mimeType: 'audio/webm' })
      mediaRecorderRef.current = mr
      chunksRef.current = []

      mr.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data)
      }

      mr.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop())
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' })
        const b64 = await blobToBase64(blob)
        setProcessing(true)
        setStatus('Transcribing...')
        try {
          const resp = await api.sendVoiceCommand(b64, 'webm')
          setLastTranscript(resp.transcript)
          setStatus(`"${resp.transcript}"`)

          if (resp.command_type === 'track_switch' && resp.track_switched_to) {
            setActiveTrack(resp.track_switched_to)
            speak(`Switching to ${resp.track_switched_to} track`)
          } else if (resp.command_type === 'briefing') {
            speak('Generating your latest briefing.')
          } else {
            speak(resp.result || 'Command received.')
          }
        } catch (e) {
          setStatus('Error: ' + e.message)
        } finally {
          setProcessing(false)
        }
      }

      mr.start()
      setRecording(true)
      setStatus('Recording...')
    } catch (e) {
      setStatus('Microphone access denied')
    }
  }, [setLastTranscript, setActiveTrack])

  const stopRecording = useCallback(() => {
    mediaRecorderRef.current?.stop()
    setRecording(false)
    setStatus('Processing...')
  }, [])

  const speak = (text) => {
    if (!window.speechSynthesis) return
    window.speechSynthesis.cancel()
    const utt = new SpeechSynthesisUtterance(text)
    utt.rate = 1.05
    window.speechSynthesis.speak(utt)
  }

  const toggle = () => {
    if (recording) {
      stopRecording()
    } else {
      startRecording()
    }
  }

  return (
    <div className="flex items-center gap-3">
      <button
        onClick={toggle}
        disabled={processing}
        className={clsx(
          'relative flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all border',
          recording
            ? 'bg-security/20 text-security border-security/40 animate-pulse'
            : processing
            ? 'bg-surface-elevated text-text-muted border-surface-border'
            : 'bg-surface-elevated text-text-secondary border-surface-border hover:border-accent hover:text-accent'
        )}
        title={recording ? 'Click to stop recording' : 'Click to speak a command'}
      >
        {processing ? (
          <Loader2 size={15} className="animate-spin" />
        ) : recording ? (
          <MicOff size={15} />
        ) : (
          <Mic size={15} />
        )}
        <span className="hidden sm:inline">
          {recording ? 'Stop' : processing ? 'Processing' : 'Voice'}
        </span>
      </button>

      {status && (
        <div className="flex items-center gap-1.5 text-xs text-text-muted max-w-xs truncate">
          <Volume2 size={12} />
          <span>{status}</span>
        </div>
      )}
    </div>
  )
}
