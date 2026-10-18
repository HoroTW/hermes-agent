# Luna auxiliary response phases

**TL;DR:** Keep final-answer text; exclude explicit `commentary` and `analysis` messages. This prevents duplicated progress labels and leaked malformed commentary while preserving older, unphased responses.

**Model hint:** Switch the progress-label model to **Luna 6 (`gpt-6-luna`)** when available. Apply this fix before switching. Changing models is optional and separate from the parser fix; no model setting is changed by this patch.

## Why it happens

A Codex Responses completion may contain more than one assistant message. Luna 6 can return a commentary message followed by a final-answer message, even for a request for one short label. Captured provider commentary included repeated label text, extra lines, non-English characters, and marker-like fragments; the following final answer was clean.

The auxiliary chat-completions adapter previously concatenated the text of every message without checking its `phase`. This exposed the commentary and joined it directly to the final answer. Telegram rendered the text it received; this was not a client font/rendering issue.

## When this fix is needed

Use it when a Codex-compatible auxiliary model emits explicit non-final message phases. The visible report was Telegram progress labels, but the correction belongs in the shared auxiliary Responses adapter, not in Telegram-specific Unicode stripping.

The change skips only messages whose phase is `commentary` or `analysis`. Tool calls and usage extraction remain unchanged. It does not repair malformed text that a provider puts in the final answer itself.

## Backward compatibility

Messages without a phase field retain their previous behavior. Explicit final-answer messages are retained as well. Older Luna 5.6-style single, unphased answers therefore remain supported; users do not have to upgrade their model to use the fix.

A response containing only non-final messages now has no answer text instead of exposing narration. Callers retain responsibility for their existing empty-answer retry or fallback handling.

## Verification

- Regression tests fail on the original adapter and pass with the three-line guard.
- Tests cover streamed SSE and completed-response objects, dictionary and namespace items, final/unphased answers, non-final-only responses, tool calls, and usage.
- On this GitHub main port: **227 relevant tests passed** across the phase regression, auxiliary-client, Codex response-adapter, and plugin-LLM test files.
- The equivalent deployed implementation also passed replay of **12 captured real multi-message responses**, including three malformed-commentary cases.
- Backward compatibility is covered by response-shape tests; no fresh live Luna 5.6 call is claimed.
