def test_turns_at_node_empty():
    turns = {}
    node_id = 123

    result = [t for t in turns.values() if t["node"] == node_id]
    assert result == []


def test_turns_at_node_multiple():
    turns = {
        1: {"turn_id": 1, "node": 10},
        2: {"turn_id": 2, "node": 10},
        3: {"turn_id": 3, "node": 11},
    }

    node_id = 10
    result = [t for t in turns.values() if t["node"] == node_id]

    assert len(result) == 2
    assert all(t["node"] == 10 for t in result)
