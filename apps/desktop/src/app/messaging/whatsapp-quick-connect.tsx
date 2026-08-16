import { useEffect, useState } from 'react'

import { Button } from '@/components/ui/button'
import {
  applyWhatsAppOnboarding,
  cancelWhatsAppOnboarding,
  disconnectWhatsApp,
  getWhatsAppOnboarding,
  startWhatsAppOnboarding,
  type WhatsAppOnboardingStatus
} from '@/hermes'
import { notify, notifyError } from '@/store/notifications'

type Phase = 'idle' | 'starting' | 'waiting' | 'finishing' | 'connected'

export function WhatsAppQuickConnect({
  connected,
  onChanged
}: {
  connected: boolean
  onChanged: () => Promise<void> | void
}) {
  const [phase, setPhase] = useState<Phase>(connected ? 'connected' : 'idle')
  const [busy, setBusy] = useState(false)
  const [pairingId, setPairingId] = useState<string | null>(null)
  const [qr, setQr] = useState<string | null>(null)
  const [account, setAccount] = useState<string | null>(null)
  const [hint, setHint] = useState('Only your WhatsApp can talk to Aakalan. Nobody else is allowed.')

  useEffect(() => {
    setPhase(connected ? 'connected' : phase === 'waiting' || phase === 'starting' ? phase : 'idle')
  }, [connected])

  useEffect(() => {
    if (!pairingId || (phase !== 'starting' && phase !== 'waiting')) {
      return
    }

    let cancelled = false
    const tick = async () => {
      try {
        const status = await getWhatsAppOnboarding(pairingId)
        if (cancelled) {
          return
        }
        applyStatus(status)
      } catch (error) {
        if (!cancelled) {
          setHint(error instanceof Error ? error.message : 'Could not read WhatsApp status.')
        }
      }
    }

    void tick()
    const id = window.setInterval(() => void tick(), 1500)
    return () => {
      cancelled = true
      window.clearInterval(id)
    }
  }, [pairingId, phase])

  const applyStatus = (status: WhatsAppOnboardingStatus) => {
    if (status.qr_payload) {
      setQr(status.qr_payload)
    }
    if (status.account_phone || status.account_name) {
      setAccount(status.account_name || status.account_phone || null)
    }
    if (status.status === 'waiting') {
      setPhase('waiting')
      setHint('Open WhatsApp → Linked devices → Link a device, then scan this code.')
    }
    if (status.status === 'connected') {
      void finish(status.pairing_id)
    }
    if (status.status === 'error' || status.status === 'expired') {
      setPhase('idle')
      setBusy(false)
      setHint(status.error || 'WhatsApp setup stopped. Try Connect again.')
    }
  }

  const finish = async (id: string) => {
    setPhase('finishing')
    try {
      await applyWhatsAppOnboarding(id)
      setPairingId(null)
      setQr(null)
      setPhase('connected')
      setHint('Connected. Messages from your own WhatsApp only.')
      notify({ title: 'WhatsApp connected', body: 'Aakalan will reply only to you.' })
      await onChanged()
    } catch (error) {
      setPhase('idle')
      notifyError('WhatsApp', error)
    } finally {
      setBusy(false)
    }
  }

  const connect = async () => {
    setBusy(true)
    setPhase('starting')
    setQr(null)
    setHint('Preparing a one-time QR code…')
    try {
      const status = await startWhatsAppOnboarding({ mode: 'self-chat' })
      setPairingId(status.pairing_id)
      applyStatus(status)
      if (status.status === 'connected') {
        await finish(status.pairing_id)
      }
    } catch (error) {
      setPhase('idle')
      setBusy(false)
      notifyError('WhatsApp', error)
    }
  }

  const cancel = async () => {
    if (pairingId) {
      try {
        await cancelWhatsAppOnboarding(pairingId)
      } catch {
        // already gone
      }
    }
    setPairingId(null)
    setQr(null)
    setBusy(false)
    setPhase(connected ? 'connected' : 'idle')
    setHint('Only your WhatsApp can talk to Aakalan. Nobody else is allowed.')
  }

  const disconnect = async () => {
    setBusy(true)
    try {
      await disconnectWhatsApp()
      setPhase('idle')
      setAccount(null)
      setHint('Disconnected. Click Connect WhatsApp when you want it again.')
      notify({ title: 'WhatsApp disconnected', body: 'This phone is no longer linked.' })
      await onChanged()
    } catch (error) {
      notifyError('WhatsApp', error)
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className="rounded-xl border border-[#25D366]/25 bg-[linear-gradient(180deg,#f0fff6_0%,#ffffff_55%)] p-4 dark:bg-none">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="m-0 text-[0.68rem] font-semibold uppercase tracking-[0.18em] text-[#128C7E]">Quick WhatsApp</p>
          <h4 className="mt-1 mb-1 text-[0.95rem] font-semibold text-[#17324d] dark:text-foreground">
            Talk to Aakalan from your own WhatsApp
          </h4>
          <p className="m-0 text-sm leading-relaxed text-muted-foreground">{hint}</p>
          {account && phase === 'connected' && (
            <p className="mt-2 mb-0 text-sm font-medium text-[#128C7E]">Linked as {account}</p>
          )}
        </div>
      </div>

      {qr && phase === 'waiting' && (
        <div className="mt-4 flex flex-col items-center gap-3">
          <img
            alt="WhatsApp QR code"
            className="size-[240px] rounded-lg bg-white p-2 shadow-sm ring-1 ring-black/10"
            src={`https://api.qrserver.com/v1/create-qr-code/?size=240x240&data=${encodeURIComponent(qr)}`}
          />
          <p className="m-0 text-xs text-muted-foreground">This code expires in a few minutes.</p>
        </div>
      )}

      <div className="mt-4 flex flex-wrap gap-2">
        {phase === 'connected' ? (
          <Button disabled={busy} onClick={() => void disconnect()} variant="destructive">
            {busy ? 'Disconnecting…' : 'Disconnect'}
          </Button>
        ) : (
          <>
            <Button className="bg-[#25D366] text-white hover:bg-[#1ebe5d]" disabled={busy} onClick={() => void connect()}>
              {busy && !qr ? 'Preparing…' : 'Connect WhatsApp'}
            </Button>
            {(phase === 'waiting' || phase === 'starting') && (
              <Button disabled={busy && !qr} onClick={() => void cancel()} variant="ghost">
                Cancel
              </Button>
            )}
          </>
        )}
      </div>
    </section>
  )
}
