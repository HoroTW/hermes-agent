"""Codex auxiliary answers must exclude non-final narration."""
from types import SimpleNamespace as NS

import pytest

from agent.auxiliary_client import _CodexCompletionsAdapter


def _complete(items, streamed):
    usage = NS(input_tokens=10, output_tokens=20, total_tokens=30)
    if streamed:
        result = iter([
            *[NS(type="response.output_item.done", item=item) for item in items],
            NS(type="response.completed", response=NS(status="completed", usage=usage)),
        ])
    else:
        result = NS(output=items, usage=usage)
    client = NS(base_url="https://chatgpt.com/backend-api/codex/",
                responses=NS(create=lambda **kwargs: result))
    return _CodexCompletionsAdapter(client, "gpt-5.3-codex").create(
        messages=[{"role": "user", "content": "Write a short progress label"}])


@pytest.mark.parametrize("shape", [dict, NS])
@pytest.mark.parametrize("answer_phase", ["final_answer", "final", None])
@pytest.mark.parametrize("streamed", [False, True])
def test_auxiliary_answer_excludes_nonfinal_message_phases(shape, answer_phase, streamed):
    def message(phase, text):
        fields = dict(type="message", content=[shape(type="output_text", text=text)])
        if phase is not None:
            fields["phase"] = phase
        return shape(**fields)

    response = _complete([
        message("analysis", "internal analysis"),
        message("commentary", "Viewing guidance\n\u8276\u65d7final\nViewing guidance"),
        message(answer_phase, "Viewing guidance"),
        shape(type="function_call", call_id="call_1", name="example", arguments="{}"),
    ], streamed)
    assert response.choices[0].message.content == "Viewing guidance"
    assert response.choices[0].message.tool_calls[0].function.name == "example"
    assert response.usage.total_tokens == 30


@pytest.mark.parametrize("streamed", [False, True])
def test_nonfinal_only_response_has_no_answer_text(streamed):
    response = _complete([
        {"type": "message", "phase": phase,
         "content": [{"type": "output_text", "text": "not a final answer"}]}
        for phase in ("analysis", "commentary")
    ], streamed)
    assert response.choices[0].message.content is None
