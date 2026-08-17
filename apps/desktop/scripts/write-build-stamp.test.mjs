import assert from 'node:assert/strict'
import { test } from 'vitest'

import {
  FALLBACK_BRANCH,
  FALLBACK_COMMIT,
  fromCI,
  fromCliRemote,
  fromFallback,
  fromLocalGit,
  isFallbackCommit,
  resolveStamp
} from './write-build-stamp.mjs'

test('fromCI reads GITHUB_SHA only when the CI repo is aakalan-cli1', () => {
  assert.deepEqual(
    fromCI({
      GITHUB_SHA: 'a'.repeat(40),
      GITHUB_REF_NAME: 'release',
      GITHUB_REPOSITORY: 'kapilmoond/aakalan-cli1'
    }),
    { commit: 'a'.repeat(40), branch: 'release', dirty: false, source: 'ci' }
  )
  assert.equal(
    fromCI({
      GITHUB_SHA: 'a'.repeat(40),
      GITHUB_REF_NAME: 'main',
      GITHUB_REPOSITORY: 'kapilmoond/aakalan-agent'
    }),
    null,
    'desktop-repo SHA must not be pinned against aakalan-cli1'
  )
  assert.equal(fromCI({ GITHUB_SHA: 'a'.repeat(40) }), null)
  assert.equal(fromCI({}), null)
})

test('fromCI accepts an explicit AAKALAN_CLI_SHA', () => {
  assert.deepEqual(
    fromCI({ AAKALAN_CLI_SHA: 'e'.repeat(40), GITHUB_REF_NAME: 'main' }),
    { commit: 'e'.repeat(40), branch: 'main', dirty: false, source: 'ci' }
  )
})

test('fromCliRemote parses ls-remote of aakalan-cli1 main', () => {
  const sha = 'f'.repeat(40)
  assert.deepEqual(
    fromCliRemote(() => `${sha}\trefs/heads/main`),
    { commit: sha, branch: 'main', dirty: false, source: 'cli-remote' }
  )
  assert.equal(fromCliRemote(() => null), null)
})

test('fromLocalGit returns null when git rev-parse fails', () => {
  const stamp = fromLocalGit('/tmp/not-a-repo', () => null)
  assert.equal(stamp, null)
})

test('fromLocalGit reads HEAD + branch + dirty status', () => {
  const calls = []
  const execFn = (cmd) => {
    calls.push(cmd)
    if (cmd === 'git rev-parse HEAD') return 'b'.repeat(40)
    if (cmd === 'git rev-parse --abbrev-ref HEAD') return 'main'
    if (cmd === 'git status --porcelain -uno') return ' M apps/desktop/package.json'
    return null
  }
  assert.deepEqual(fromLocalGit('/repo', execFn), {
    commit: 'b'.repeat(40),
    branch: 'main',
    dirty: true,
    source: 'local'
  })
  assert.ok(calls.includes('git rev-parse HEAD'))
})

test('fromFallback uses the all-zero placeholder commit', () => {
  assert.deepEqual(fromFallback(), {
    commit: FALLBACK_COMMIT,
    branch: FALLBACK_BRANCH,
    dirty: false,
    source: 'fallback'
  })
  assert.equal(isFallbackCommit(FALLBACK_COMMIT), true)
  assert.equal(isFallbackCommit('a'.repeat(40)), false)
})

test('resolveStamp prefers cli1 CI over ls-remote over fallback', () => {
  const ci = resolveStamp({
    env: {
      GITHUB_SHA: 'c'.repeat(40),
      GITHUB_REF_NAME: 'main',
      GITHUB_REPOSITORY: 'kapilmoond/aakalan-cli1'
    },
    execFn: () => 'should-not-run'
  })
  assert.equal(ci.source, 'ci')
  assert.equal(ci.commit, 'c'.repeat(40))

  const remote = resolveStamp({
    env: {},
    execFn: (cmd) => {
      if (String(cmd).includes('ls-remote')) return `${'d'.repeat(40)}\trefs/heads/main`
      return null
    }
  })
  assert.equal(remote.source, 'cli-remote')
  assert.equal(remote.commit, 'd'.repeat(40))
})

test('resolveStamp falls back when neither CI nor git is available', () => {
  const stamp = resolveStamp({ env: {}, execFn: () => null })
  assert.deepEqual(stamp, {
    commit: FALLBACK_COMMIT,
    branch: FALLBACK_BRANCH,
    dirty: false,
    source: 'fallback'
  })
})
