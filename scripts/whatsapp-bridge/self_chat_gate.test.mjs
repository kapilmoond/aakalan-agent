import test from 'node:test';
import assert from 'node:assert/strict';
import os from 'node:os';
import path from 'node:path';
import { mkdtempSync, rmSync, writeFileSync } from 'node:fs';

import { parseAllowedUsers } from './allowlist.js';
import { isOwnerSelfChat } from './self_chat_gate.js';

const OWNER_PHONE = '917015854935';
const OWNER_LID = '216938848514123';
const STRANGER_LID = '190554914721951';

function gate(overrides = {}) {
  return isOwnerSelfChat({
    fromMe: false,
    isGroup: false,
    chatId: `${OWNER_LID}@lid`,
    senderId: `${OWNER_LID}@lid`,
    myNumber: OWNER_PHONE,
    myLid: OWNER_LID,
    allowedUsers: parseAllowedUsers(OWNER_PHONE),
    sessionDir: os.tmpdir(),
    ...overrides,
  });
}

test('accepts fromMe Message-yourself on owner phone JID', () => {
  assert.equal(
    gate({
      fromMe: true,
      chatId: `${OWNER_PHONE}@s.whatsapp.net`,
      senderId: `${OWNER_PHONE}@s.whatsapp.net`,
    }),
    true,
  );
});

test('accepts fromMe Message-yourself on owner LID', () => {
  assert.equal(gate({ fromMe: true }), true);
});

test('rejects fromMe messages sent to another person', () => {
  assert.equal(
    gate({
      fromMe: true,
      chatId: `${STRANGER_LID}@lid`,
      senderId: `${OWNER_PHONE}@s.whatsapp.net`,
    }),
    false,
  );
});

test('accepts !fromMe phone self-chat that WhatsApp delivers as inbound owner LID', () => {
  assert.equal(gate({ fromMe: false }), true);
});

test('accepts !fromMe owner LID when allowlist is phone-only and mapping exists', () => {
  const sessionDir = mkdtempSync(path.join(os.tmpdir(), 'aakalan-wa-selfchat-'));
  try {
    writeFileSync(path.join(sessionDir, `lid-mapping-${OWNER_PHONE}.json`), JSON.stringify(OWNER_LID));
    writeFileSync(
      path.join(sessionDir, `lid-mapping-${OWNER_LID}_reverse.json`),
      JSON.stringify(OWNER_PHONE),
    );
    assert.equal(
      gate({
        fromMe: false,
        myNumber: '',
        myLid: '',
        sessionDir,
      }),
      true,
    );
  } finally {
    rmSync(sessionDir, { recursive: true, force: true });
  }
});

test('rejects stranger DMs in self-chat mode', () => {
  assert.equal(
    gate({
      fromMe: false,
      chatId: `${STRANGER_LID}@lid`,
      senderId: `${STRANGER_LID}@lid`,
    }),
    false,
  );
});

test('rejects groups even when fromMe', () => {
  assert.equal(
    gate({
      fromMe: true,
      isGroup: true,
      chatId: '120363162011172819@g.us',
      senderId: `${OWNER_PHONE}@s.whatsapp.net`,
    }),
    false,
  );
});
