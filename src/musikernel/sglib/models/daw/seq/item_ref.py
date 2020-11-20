from pymarshal.json import type_assert


class ItemRef:
    """
        A reference to an item within the sequence
    """
    def __init__(
        self,
        uid,
        item_uid,
        pos,
        item_start,
        length,
        track_num,
    ):
        self.uid = type_assert(
            uid,
            int,
            desc="The uid of this item reference",
        )
        self.item_uid = type_assert(
            item_uid,
            int,
            desc="The uid of the underlying item",
        )
        self.pos = type_assert(
            pos,
            float,
            desc="The start position within the sequencer, in beats",
        )
        self.item_start = type_assert(
            item_start,
            float,
            desc=(
                "The start offset of the item, in beats."
                "A value of 1.0 starts 1 beat into the item"
            ),
        )
        self.length = type_assert(
            length,
            float,
            desc="The length of this item reference, in beats",
        )
        self.track_num = type_assert(
            track_num,
            int,
            desc="The track number this reference is displayed on"
        )

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def item(
        self,
        items,
    ):
        """ Return the underlying item
            @items: ProjectFolder, The project folder for items
        """
        return items.load(self.item_uid)

    def clone(
        self,
        uid=None,
        item_uid=None,
        pos=None,
        item_start=None,
        length=None,
        track_num=None,
    ):
        """ Create a clone of this item ref, overriding any fields """
        return ItemRef(
            uid if uid is not None else self.uid,
            item_uid if item_uid is not None else self.item_uid,
            pos if pos is not None else self.pos,
            item_start if item_start is not None else self.item_start,
            length if length is not None else self.length,
            track_num if track_num is not None else self.track_num,
        )

