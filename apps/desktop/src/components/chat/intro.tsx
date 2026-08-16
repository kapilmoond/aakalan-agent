import { useState } from 'react'

import { BrandMark } from '@/components/brand-mark'
import { capitalize, normalize } from '@/lib/text'

import introCopyJsonl from './intro-copy.jsonl?raw'

type IntroCopy = {
  headline: string
  body: string
}

type IntroCopyRecord = IntroCopy & {
  personality: string
}

export type IntroProps = {
  personality?: string
  seed?: number
}

const NEUTRAL_PERSONALITIES = new Set(['', 'default', 'none', 'neutral'])

const FALLBACK_COPY: IntroCopy[] = [
  {
    headline: 'Ready when you are.',
    body: 'Ask, attach a file, or drop a path. Aakalan will search, draft, and get the work done.'
  },
  {
    headline: 'Your work, handled.',
    body: 'Give the task in plain language. I will inspect first, then act with a clear next step.'
  },
  {
    headline: 'What should we finish today?',
    body: 'A letter, a search, a plan, or a stuck file — send it and I will take it forward.'
  },
  {
    headline: 'Start with the real problem.',
    body: 'Drop the context you have. I will sort it into a plan or a finished result.'
  },
  {
    headline: 'Confidence, then action.',
    body: 'I will check the facts, then write, search, or build — without guessing.'
  }
]

function normalizeKey(value?: string): string {
  return normalize(value)
}

function titleize(value: string): string {
  return value
    .split(/[-_\s]+/)
    .filter(Boolean)
    .map(capitalize)
    .join(' ')
}

function isIntroCopyRecord(value: unknown): value is IntroCopyRecord {
  if (!value || typeof value !== 'object') {
    return false
  }

  const record = value as Record<string, unknown>

  return (
    typeof record.personality === 'string' &&
    typeof record.headline === 'string' &&
    typeof record.body === 'string' &&
    Boolean(record.personality.trim()) &&
    Boolean(record.headline.trim()) &&
    Boolean(record.body.trim())
  )
}

function parseIntroCopy(raw: string): Record<string, IntroCopy[]> {
  const byPersonality: Record<string, IntroCopy[]> = {}

  for (const line of raw.split(/\r?\n/)) {
    const trimmed = line.trim()

    if (!trimmed) {
      continue
    }

    try {
      const parsed: unknown = JSON.parse(trimmed)

      if (!isIntroCopyRecord(parsed)) {
        continue
      }

      const key = normalizeKey(parsed.personality)
      byPersonality[key] ??= []
      byPersonality[key].push({
        headline: parsed.headline.trim(),
        body: parsed.body.trim()
      })
    } catch {
      // Bad generated copy should not break the whole desktop app.
    }
  }

  return byPersonality
}

const INTRO_COPY_BY_PERSONALITY = parseIntroCopy(introCopyJsonl)

function neutralCopy(): IntroCopy[] {
  return INTRO_COPY_BY_PERSONALITY.none || INTRO_COPY_BY_PERSONALITY.default || FALLBACK_COPY
}

function fallbackCopyForPersonality(personalityKey: string): IntroCopy[] {
  if (NEUTRAL_PERSONALITIES.has(personalityKey)) {
    return neutralCopy()
  }

  const label = titleize(personalityKey)

  return [
    {
      headline: `${label} mode is ready.`,
      body: 'Send the task, file, or idea. I will keep the work grounded and move it forward.'
    }
  ]
}

function pickCopy(copies: IntroCopy[], seed = 0): IntroCopy {
  return copies[Math.abs(seed) % copies.length] || FALLBACK_COPY[0]
}

function resolveCopy(personality?: string, seed?: number): IntroCopy {
  const personalityKey = normalizeKey(personality)

  const copies = NEUTRAL_PERSONALITIES.has(personalityKey)
    ? INTRO_COPY_BY_PERSONALITY[personalityKey] || neutralCopy()
    : INTRO_COPY_BY_PERSONALITY[personalityKey] || fallbackCopyForPersonality(personalityKey)

  return pickCopy(copies, seed)
}

export function Intro({ personality, seed }: IntroProps) {
  const [mountSeed] = useState(() => Math.floor(Math.random() * 100000))
  const copy = resolveCopy(personality, mountSeed + (seed ?? 0))

  return (
    <div
      className="pointer-events-none flex w-full min-w-0 flex-col items-center justify-center px-6 py-10 text-center"
      data-slot="aui_intro"
    >
      <div className="flex max-w-xl flex-col items-center">
        <BrandMark className="mb-6 size-[5.5rem] rounded-2xl shadow-[0_10px_30px_-12px_rgba(23,50,77,0.35)] ring-1 ring-black/5" />

        <p className="m-0 text-[0.68rem] font-semibold tracking-[0.28em] text-[#ea580c] uppercase">
          Aaklan Infra Consultancy
        </p>

        <h1 className="mt-2 mb-0 font-['Collapse'] text-[clamp(2.4rem,6vw,3.75rem)] font-bold leading-[0.92] tracking-[0.04em] text-[#17324d] uppercase dark:text-[#f8fafc]">
          Aakalan Agent
        </h1>

        <span className="mt-4 h-[3px] w-16 rounded-full bg-(--aaklan-strip,linear-gradient(90deg,#c2410c,#ea580c,#f59e0b))" />

        <p className="mt-5 mb-1 text-[1.15rem] font-medium tracking-tight text-[#17324d] dark:text-foreground">
          {copy.headline}
        </p>
        <p className="m-0 max-w-md text-[0.95rem] leading-relaxed text-muted-foreground">{copy.body}</p>
      </div>
    </div>
  )
}
