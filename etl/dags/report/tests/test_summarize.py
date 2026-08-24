"""Tests for the summarization node and its pure helpers."""

import urllib.error
from unittest.mock import patch

from report.nodes import summarize
from report.nodes.summarize import (
    SOURCE_FALLBACK,
    SOURCE_MODEL,
    build_prompt,
    fallback_summary,
    make_summarize,
    parse_summary,
    strip_reasoning,
)


def test_a_reasoning_block_is_removed_before_the_answer():
    text = "<think>let me add these up 1+1</think>\nYields were strong today."
    assert strip_reasoning(text) == "Yields were strong today."


def test_an_unclosed_reasoning_block_leaves_nothing():
    """A reply truncated inside the thinking block has no answer, so it is empty
    and the node falls back rather than reporting the model's scratch work."""
    assert strip_reasoning("<think>still thinking and cut off") == ""


def test_a_reply_reaches_the_narrative_after_stripping():
    narrative, insights = parse_summary("<think>x</think>\nAll nominal.\n- one")
    assert narrative == "All nominal."
    assert insights == ["one"]


def test_prompt_carries_the_figures_and_names_no_html():
    prompt = build_prompt(
        {
            "report_date": "2026-08-15",
            "active_farms": 75,
            "totals": {"total_yield_kg": 1234.5},
            "top_farms": [],
        }
    )
    assert "2026-08-15" in prompt
    assert "75" in prompt
    assert "1234.5" in prompt


def test_parse_splits_narrative_from_bullets():
    text = "Yield rose today.\nEnergy held steady.\n- First insight\n- Second insight"
    narrative, insights = parse_summary(text)

    assert "Yield rose today." in narrative
    assert "Energy held steady." in narrative
    assert insights == ["First insight", "Second insight"]


def test_parse_without_bullets_is_all_narrative():
    narrative, insights = parse_summary("Just one line.")
    assert narrative == "Just one line."
    assert insights == []


def test_fallback_reads_the_figures_for_a_day_with_data(sample_kpis):
    narrative, insights = fallback_summary(sample_kpis)
    assert "75" in narrative
    assert insights


def test_fallback_for_an_empty_day_says_so():
    narrative, insights = fallback_summary(
        {"report_date": "2026-01-01", "has_data": False, "totals": {}}
    )
    assert "No warehouse metrics" in narrative
    assert insights == []


def test_node_uses_the_model_when_it_answers(deps, sample_kpis):
    node = make_summarize(deps)

    with patch.object(
        summarize, "call_ollama", return_value="A good day.\n- one\n- two"
    ):
        result = node({"kpis": sample_kpis})

    assert result["summary_source"] == SOURCE_MODEL
    assert result["narrative"] == "A good day."
    assert result["insights"] == ["one", "two"]


def test_node_falls_back_and_records_the_source_on_failure(deps, sample_kpis):
    """A cold-start failure must be visible as a fallback, not pass silently."""
    node = make_summarize(deps)

    with patch.object(
        summarize, "call_ollama", side_effect=urllib.error.URLError("cold")
    ):
        result = node({"kpis": sample_kpis})

    assert result["summary_source"] == SOURCE_FALLBACK
    assert result["narrative"]


def test_node_falls_back_when_the_model_returns_no_narrative(deps, sample_kpis):
    node = make_summarize(deps)

    with patch.object(summarize, "call_ollama", return_value="   "):
        result = node({"kpis": sample_kpis})

    assert result["summary_source"] == SOURCE_FALLBACK
