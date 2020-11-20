from sglib.models.daw.seq.item_ref import ItemRef


def test_clone_eq():
    item_ref = ItemRef(
        0,
        0,
        0.,
        0.,
        4.,
        0,
    )
    clone = item_ref.clone()
    assert clone == item_ref, (clone.__dict__, item_ref.__dict__)
