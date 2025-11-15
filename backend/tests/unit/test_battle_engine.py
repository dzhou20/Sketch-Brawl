"""Property-based tests for deterministic battle engine."""
from hypothesis import given, strategies as st

from src.services.battle_engine import BattleEngine, Combatant
from src.services.battle_timeline import BattleTimelineBuilder

combatant_strategy = st.builds(
    Combatant,
    slot=st.sampled_from(['A', 'B']),
    name=st.text(min_size=1, max_size=10),
    element=st.sampled_from(['fire', 'water', 'wood', 'earth', 'metal']),
    base_hp=st.integers(min_value=80, max_value=160),
    base_attack=st.integers(min_value=20, max_value=60),
    skill_power=st.integers(min_value=5, max_value=30),
)


@given(seed=st.integers(min_value=1, max_value=10**6),
       a=combatant_strategy,
       b=combatant_strategy)
def test_battle_determinism(seed, a, b):
    a.slot = 'A'
    b.slot = 'B'
    engine = BattleEngine(seed)
    result1 = engine.run_match([a, b])
    engine2 = BattleEngine(seed)
    result2 = engine2.run_match([a, b])

    assert result1.winner_slot == result2.winner_slot
    assert result1.wins == result2.wins
    assert [e.__dict__ for e in result1.timeline] == [e.__dict__ for e in result2.timeline]


def test_battle_summary_matches_timeline():
    a = Combatant(slot='A', name='TestA', element='fire', base_hp=130, base_attack=45)
    b = Combatant(slot='B', name='TestB', element='water', base_hp=125, base_attack=42)
    engine = BattleEngine(seed=99)
    result = engine.run_match([a, b])
    builder = BattleTimelineBuilder()
    payload = builder.build_payload([a, b], result)

    assert payload["winner_slot"] in {'A', 'B'}
    assert payload["wins"][payload["winner_slot"]] >= 2
    for round_summary in payload["rounds"]:
        events = [ev for ev in payload["timeline"] if ev["round"] == round_summary["round"]]
        total_turns = len([ev for ev in events if ev["event"] != "round_end"])
        damage = sum(ev["damage"] for ev in events if ev["event"] != "round_end")
        assert round_summary["turns"] == total_turns
        assert sum(round_summary["total_damage"].values()) == damage
