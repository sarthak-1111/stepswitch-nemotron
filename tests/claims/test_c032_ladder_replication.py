"""C-032: C-029 made again, on a second pair of runs.

Proof: bench evidence (ADR 0047). The runs named in the claim's thresholds were made the way
C-029's were, with the same pool, policy, per-task cap and interleaving, on a later commit.
They are compared exactly as C-029's are (`test_c029_nemotron_ladder.compare`): the claim
holds when the ladder passes at least as many task runs as Ultra alone and its dollars' share
of Ultra's, with its whole interval, lies below `cost_share_max`.
"""

from __future__ import annotations

import pytest

from tests.claims import evidence
from tests.claims.test_c029_nemotron_ladder import compare

pytestmark = [pytest.mark.claim("C-032")]


def test_the_ladder_holds_on_a_second_pair_of_runs() -> None:
    data, problems = compare("C-032")
    evidence.write("C-032", "comparison", data)
    assert not problems, problems
