import { useEffect, useState } from 'react'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  deleteEmailAccount,
  listEmailAccounts,
  upsertEmailAccount,
  type EmailAccountInfo
} from '@/hermes'
import { notify, notifyError } from '@/store/notifications'

type Provider = 'gmail' | 'workspace' | 'outlook' | 'other'

const PROVIDERS: Array<{ hint: string; id: Provider; label: string }> = [
  { id: 'gmail', label: 'Gmail', hint: 'gmail.com — use an App Password' },
  { id: 'workspace', label: 'Google Workspace', hint: 'Company domain on Google, e.g. aakalaninfra.com' },
  { id: 'outlook', label: 'Outlook / Microsoft 365', hint: 'outlook.com or a Microsoft 365 mailbox' },
  { id: 'other', label: 'Other IMAP', hint: 'Any mailbox with IMAP + SMTP' }
]

export function EmailQuickConnect({
  onChanged
}: {
  onChanged: () => Promise<void> | void
}) {
  const [accounts, setAccounts] = useState<EmailAccountInfo[]>([])
  const [busy, setBusy] = useState(false)
  const [adding, setAdding] = useState(false)
  const [provider, setProvider] = useState<Provider>('gmail')
  const [address, setAddress] = useState('')
  const [password, setPassword] = useState('')
  const [imapHost, setImapHost] = useState('')
  const [smtpHost, setSmtpHost] = useState('')
  const [workspaceFull, setWorkspaceFull] = useState(true)
  const [hint, setHint] = useState('Add every mailbox Aakalan should read and reply from.')

  const refresh = async () => {
    const result = await listEmailAccounts()
    setAccounts(result.accounts || [])
  }

  useEffect(() => {
    void refresh().catch(error => {
      setHint(error instanceof Error ? error.message : 'Could not load email accounts.')
    })
  }, [])

  const addAccount = async () => {
    const email = address.trim()
    if (!email || !password.trim()) {
      setHint('Enter the email address and an app password.')
      return
    }
    if (provider === 'other' && (!imapHost.trim() || !smtpHost.trim())) {
      setHint('For other IMAP mailboxes, fill IMAP host and SMTP host.')
      return
    }
    setBusy(true)
    try {
      await upsertEmailAccount({
        address: email,
        password,
        provider,
        imap_host: provider === 'other' ? imapHost.trim() : undefined,
        smtp_host: provider === 'other' ? smtpHost.trim() : undefined,
        workspace_full: provider === 'workspace' ? workspaceFull : false
      })
      setAddress('')
      setPassword('')
      setImapHost('')
      setSmtpHost('')
      setAdding(false)
      setHint(
        provider === 'workspace' && workspaceFull
          ? 'Workspace mailbox saved. Aakalan can mail from this address. Calendar/Drive/Docs use this same Google account when the Workspace skill is set up.'
          : 'Mailbox saved. Aakalan will restart the gateway and start reading this inbox.'
      )
      notify({ title: 'Email connected', body: email })
      await refresh()
      await onChanged()
    } catch (error) {
      notifyError(error, 'Could not save that email account.')
    } finally {
      setBusy(false)
    }
  }

  const removeAccount = async (account: EmailAccountInfo) => {
    if (!window.confirm(`Remove ${account.address}? Aakalan will stop reading this mailbox.`)) {
      return
    }
    setBusy(true)
    try {
      const result = await deleteEmailAccount(account.id)
      setAccounts(result.accounts || [])
      notify({ title: 'Email removed', body: account.address })
      await onChanged()
    } catch (error) {
      notifyError(error, 'Could not remove that email account.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className="rounded-xl border border-[#EA4335]/20 bg-[linear-gradient(180deg,#fff8f6_0%,#ffffff_55%)] p-4 dark:bg-none">
      <div>
        <p className="m-0 text-[0.68rem] font-semibold uppercase tracking-[0.18em] text-[#C5221F]">Email</p>
        <h4 className="mt-1 mb-1 text-[0.95rem] font-semibold text-[#17324d] dark:text-foreground">
          Add Gmail, Google Workspace, or more mailboxes
        </h4>
        <p className="m-0 text-sm leading-relaxed text-muted-foreground">{hint}</p>
      </div>

      {accounts.length > 0 && (
        <ul className="mt-3 mb-0 list-none space-y-2 p-0">
          {accounts.map(account => (
            <li
              className="flex items-center justify-between gap-3 rounded-lg border border-black/5 bg-white/80 px-3 py-2 dark:bg-background"
              key={account.id}
            >
              <div className="min-w-0">
                <p className="m-0 truncate text-sm font-medium">{account.address}</p>
                <p className="m-0 text-xs text-muted-foreground">
                  {account.label || account.provider}
                  {account.workspace_full ? ' · complete Workspace' : ''}
                </p>
              </div>
              <Button disabled={busy} onClick={() => void removeAccount(account)} size="sm" variant="ghost">
                Remove
              </Button>
            </li>
          ))}
        </ul>
      )}

      {adding ? (
        <div className="mt-4 grid gap-3">
          <div className="flex flex-wrap gap-2">
            {PROVIDERS.map(item => (
              <Button
                key={item.id}
                onClick={() => setProvider(item.id)}
                size="sm"
                variant={provider === item.id ? 'default' : 'outline'}
              >
                {item.label}
              </Button>
            ))}
          </div>
          <p className="m-0 text-xs text-muted-foreground">{PROVIDERS.find(item => item.id === provider)?.hint}</p>
          <Input
            autoComplete="username"
            onChange={event => setAddress(event.target.value)}
            placeholder={provider === 'workspace' ? 'you@aakalaninfra.com' : 'you@gmail.com'}
            value={address}
          />
          <Input
            autoComplete="current-password"
            onChange={event => setPassword(event.target.value)}
            placeholder="App password (not your normal login password)"
            type="password"
            value={password}
          />
          {provider === 'other' && (
            <>
              <Input onChange={event => setImapHost(event.target.value)} placeholder="IMAP host, e.g. imap.example.com" value={imapHost} />
              <Input onChange={event => setSmtpHost(event.target.value)} placeholder="SMTP host, e.g. smtp.example.com" value={smtpHost} />
            </>
          )}
          {provider === 'workspace' && (
            <label className="flex items-start gap-2 text-sm text-muted-foreground">
              <input
                checked={workspaceFull}
                className="mt-1"
                onChange={event => setWorkspaceFull(event.target.checked)}
                type="checkbox"
              />
              <span>
                Complete Workspace: this mailbox plus Gmail / Calendar / Drive / Docs / Sheets for the same Google account.
              </span>
            </label>
          )}
          <p className="m-0 text-xs text-muted-foreground">
            Gmail and Google Workspace: Google Account → Security → 2-Step Verification → App passwords. Create one named
            Aakalan and paste it here. Do not use the normal account password.
          </p>
          <div className="flex flex-wrap gap-2">
            <Button disabled={busy} onClick={() => void addAccount()}>
              {busy ? 'Saving…' : 'Save mailbox'}
            </Button>
            <Button disabled={busy} onClick={() => setAdding(false)} variant="ghost">
              Cancel
            </Button>
          </div>
        </div>
      ) : (
        <div className="mt-4">
          <Button disabled={busy} onClick={() => setAdding(true)}>
            Add email
          </Button>
        </div>
      )}
    </section>
  )
}
