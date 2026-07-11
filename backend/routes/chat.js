const express = require('express');
const router = express.Router();
const prisma = require('../lib/prisma');
const auth = require('../middleware/auth');
const axios = require('axios');

const AI_SERVICE_URL = process.env.AI_SERVICE_URL || 'http://localhost:8000';

// ── POST /api/chat ─────────────────────────────────────────────────────────────
// 1. Validates the thread belongs to the authenticated user.
// 2. Saves the user message.
// 3. Proxies to the Python AI service.
// 4. Saves the assistant response.
// 5. Returns the full assistant message record.
router.post('/', auth, async (req, res) => {
  const { threadId, message } = req.body;

  if (!threadId || !message || !message.trim()) {
    return res.status(400).json({ msg: 'threadId and message are required.' });
  }

  try {
    // Verify thread ownership
    const thread = await prisma.thread.findFirst({
      where: { id: threadId, userId: req.user.id },
    });
    if (!thread) return res.status(404).json({ msg: 'Thread not found.' });

    // Persist user message immediately (so it is visible even if AI fails)
    await prisma.message.create({
      data: { threadId, role: 'USER', content: message.trim() },
    });

    // ── Call Python AI service ──────────────────────────────────────────────
    let aiContent = '';
    let sources = [];

    try {
      const aiRes = await axios.post(
        `${AI_SERVICE_URL}/chat/`,
        { session_id: threadId, message: message.trim() },
        { timeout: 60_000 } // 60-second timeout – AI graph can be slow
      );
      aiContent = aiRes.data.response || '';
      sources   = Array.isArray(aiRes.data.sources) ? aiRes.data.sources : [];
    } catch (aiErr) {
      const detail = aiErr.response?.data?.detail || aiErr.message;
      console.error('[AI Service Error]', detail);
      aiContent = "I'm sorry, I'm having trouble connecting to the AI service right now. Please try again in a moment.";
    }

    // Persist assistant response
    const assistantMsg = await prisma.message.create({
      data: {
        threadId,
        role:    'ASSISTANT',
        content: aiContent,
        sources: JSON.stringify(sources),
      },
    });

    // Bump thread's updatedAt so it rises to the top of the list
    await prisma.thread.update({
      where: { id: threadId },
      data:  { updatedAt: new Date() },
    });

    res.json(assistantMsg);
  } catch (err) {
    console.error('[POST /chat]', err);
    res.status(500).json({ msg: 'Failed to process chat message.' });
  }
});

module.exports = router;
