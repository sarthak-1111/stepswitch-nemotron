"""A per-step model ladder in rules, escalation-aware, and a second opinion on reviews
(ADR 0044)."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from stepswitch.router.features import TaskFeatures
from stepswitch.router.router import RouterState, route
from stepswitch.router.rules import parse_rules
from stepswitch.verify import review
from stepswitch.workers.base import WorkerSpec

SMALL = WorkerSpec(id="h/small", endpoint="h", model="small", tier="t1", family="n", local=False)
MID = WorkerSpec(id="h/mid", endpoint="h", model="mid", tier="t3", family="n", local=False)
BIG = WorkerSpec(id="h/big", endpoint="h", model="big", tier="remote", family="n", local=False)
OTHER = WorkerSpec(id="h/other", endpoint="h", model="other", tier="t3", family="g", local=False)
WORKERS = [SMALL, MID, BIG, OTHER]
FEATURES = TaskFeatures()
LADDER = parse_rules(
    [
        {
            "name": "small-reads",
            "when": {"step_type": ["navigate", "read", "summarize", "write-text"]},
            "to": {"model": "small"},
        },
        {
            "name": "mid-edits",
            "when": {"step_type": ["edit", "run", "triage"], "escalations": 0},
            "to": {"model": "mid"},
        },
        {
            "name": "big-plans-reviews-and-escalations",
            "when": {"step_type": ["plan", "review", "edit", "run", "triage"]},
            "to": {"model": "big"},
        },
    ]
)


def chosen(step_type: str, **state: object) -> str | None:
    base: dict[str, object] = {"step": 1, "level": 1, "allow_remote": True}
    decision = route(
        FEATURES,
        step_type,
        RouterState(**{**base, **state}),  # type: ignore[arg-type]
        WORKERS,
        LADDER,
    )
    return decision.chosen


def test_each_step_type_goes_to_its_rung_of_the_ladder() -> None:
    for step_type in ("navigate", "read", "summarize", "write-text"):
        assert chosen(step_type) == SMALL.id, step_type
    for step_type in ("edit", "run", "triage"):
        assert chosen(step_type) == MID.id, step_type
    for step_type in ("plan", "review"):
        assert chosen(step_type) == BIG.id, step_type


def test_work_steps_move_up_once_the_ladder_escalated() -> None:
    for step_type in ("edit", "run", "triage"):
        assert chosen(step_type, escalations=1, level=2) == BIG.id, step_type
    # Reading stays on the small model after an escalation.
    assert chosen("read", escalations=1, level=2) == SMALL.id


def test_rules_compare_escalations() -> None:
    rules = parse_rules(
        [{"name": "late", "when": {"escalations": ">=2"}, "to": {"model": "other"}}]
    )
    early = route(FEATURES, "edit", RouterState(step=1, level=2, allow_remote=True), WORKERS, rules)
    late = route(
        FEATURES,
        "edit",
        RouterState(step=1, level=2, allow_remote=True, escalations=2),
        WORKERS,
        rules,
    )
    assert early.rule is None and late.chosen == OTHER.id and late.rule == "late"


def test_a_second_opinion_sets_review_pins_aside_for_another_family() -> None:
    authors = frozenset({"n"})
    pinned = route(
        FEATURES,
        "review",
        RouterState(step=1, level=1, allow_remote=True, avoid_families=authors),
        WORKERS,
        LADDER,
    )
    assert pinned.chosen == BIG.id and pinned.rule == "big-plans-reviews-and-escalations"
    second = route(
        FEATURES,
        "review",
        RouterState(step=1, level=1, allow_remote=True, avoid_families=authors, cross_check=True),
        WORKERS,
        LADDER,
    )
    assert second.chosen == OTHER.id and second.rule is None
    assert any("set aside for a second opinion" in note for note in second.notes)
    # Other step types keep their pins during a second opinion.
    edit = route(
        FEATURES,
        "edit",
        RouterState(step=1, level=1, allow_remote=True, cross_check=True),
        WORKERS,
        LADDER,
    )
    assert edit.chosen == MID.id


def test_second_opinion_setting_and_verdicts() -> None:
    on = SimpleNamespace(model_extra={"review": {"second_opinion": True}})
    assert review.second_opinion_enabled(on)
    assert not review.second_opinion_enabled(SimpleNamespace(model_extra={}))
    assert not review.second_opinion_enabled(None)
    yes, no, none = {"approved": True}, {"approved": False}, {"approved": None}
    assert review.verdicts_agree(yes, yes) is True
    assert review.verdicts_agree(yes, no) is False
    assert review.verdicts_agree(yes, none) is None


def test_combined_verdict_blocks_when_either_reviewer_disapproves() -> None:
    first = {"approved": True, "text": "", "reviewer": "h/big"}
    second = {"approved": False, "text": "- [high] a.py:3: wrong", "reviewer": "h/other"}
    combined = review.combine(first, second)
    assert combined["approved"] is False and combined["agrees"] is False
    assert combined["text"] == "- [high] a.py:3: wrong"
    assert combined["reviewer"] == "h/big" and combined["second_opinion"]["reviewer"] == "h/other"
    both = review.combine({**first, "approved": False, "text": "x"}, second)
    assert both["approved"] is False and both["text"].splitlines()[0] == "x"
    agreed = review.combine(first, {**second, "approved": True, "text": ""})
    assert agreed["approved"] is True and agreed["agrees"] is True
    # A first review without a verdict takes the second's.
    failed = {"approved": None, "failed": True, "text": "", "reviewer": "h/big"}
    rescued = review.combine(failed, {**second, "approved": True})
    assert rescued["approved"] is True and "failed" not in rescued
    assert rescued["agrees"] is None


SECOND_OPINION = SimpleNamespace(model_extra={"review": {"second_opinion": True}})


def test_the_agent_asks_another_family_for_a_second_opinion(tmp_path: Path) -> None:
    from tests.unit.test_builtin_agent import StubGates, events, fixer_script, make_loop, worker

    rules = parse_rules([{"name": "a-does-everything", "to": {"model": "a"}}])
    author = worker("h/a", "t2", fixer_script(), family="n")
    other = worker("h/b", "t2", fixer_script({"review": "ISSUES\n- test zero"}), family="g")
    loop = make_loop(tmp_path, [author, other], StubGates([True]), rules=rules)
    loop.config = SECOND_OPINION
    outcome = loop.run()
    assert outcome.status == "done"
    reviews = events(loop, "review")
    first, second = reviews[0], reviews[1]
    assert first["reviewer"] == "h/a" and first["approved"] is True
    assert second["reviewer"] == "h/b" and second["second_opinion"] is True
    assert second["approved"] is False and second["agrees"] is False
    assert any("test zero" in m.text_content() for m in loop.messages)


def test_no_second_opinion_without_the_setting_or_with_a_pinned_worker(tmp_path: Path) -> None:
    from tests.unit.test_builtin_agent import StubGates, events, fixer_script, make_loop, worker

    def reviewers(path: Path, setting: bool, **spec: object) -> list[object]:
        path.mkdir()
        loop = make_loop(
            path,
            [
                worker("h/a", "t2", fixer_script(), family="n"),
                worker("h/b", "t2", fixer_script({"review": "ISSUES\n- x"}), family="g"),
            ],
            StubGates([True]),
            rules=parse_rules([{"name": "a", "to": {"model": "a"}}]),
            **spec,
        )
        if setting:
            loop.config = SECOND_OPINION
        loop.run()
        return [r["reviewer"] for r in events(loop, "review")]

    assert reviewers(tmp_path / "off", False) == ["h/a"]
    assert reviewers(tmp_path / "pinned", True, worker="h/a") == ["h/a"]
