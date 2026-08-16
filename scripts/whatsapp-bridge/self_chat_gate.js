/**
 * Decide whether a WhatsApp upsert should be treated as the owner's
 * self-chat in WHATSAPP_MODE=self-chat.
 *
 * Phone "Message yourself" is usually fromMe + own JID. After LID
 * migration / reconnect it often arrives as !fromMe with the owner's
 * phone or LID. Those must still be accepted. Stranger DMs and
 * chats with other people must stay blocked (#8389).
 */
import { matchesAllowedUser, normalizeWhatsAppIdentifier } from './allowlist.js';

export function isOwnerSelfChat({
  fromMe,
  isGroup,
  chatId,
  senderId,
  myNumber,
  myLid,
  allowedUsers,
  sessionDir,
}) {
  if (isGroup) {
    return false;
  }

  const chatNumber = normalizeWhatsAppIdentifier(chatId);
  const senderNumber = normalizeWhatsAppIdentifier(senderId);
  const ownerNumbers = new Set(
    [myNumber, myLid].map((value) => normalizeWhatsAppIdentifier(value)).filter(Boolean),
  );

  const isOwnerId = (value) => {
    if (!value) {
      return false;
    }
    if (ownerNumbers.has(value)) {
      return true;
    }
    return matchesAllowedUser(value, allowedUsers, sessionDir);
  };

  if (fromMe) {
    // Own outbound: only the Message-yourself thread (chat is us).
    return isOwnerId(chatNumber);
  }

  // Phone-originated self-chat can be delivered as a normal inbound
  // from the owner. Require the chat (and sender, when present) to be us.
  if (!isOwnerId(chatNumber)) {
    return false;
  }
  if (senderNumber && !isOwnerId(senderNumber)) {
    return false;
  }
  return true;
}
