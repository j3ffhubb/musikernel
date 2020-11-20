from pymarshal import type_assert


class NextUID:
    def __init__(
        self,
        next_uid,
    ):
        self.next_uid = type_assert(
            next_uid,
            int,
            desc="The next uid in the sequence",
        )

    @staticmethod
    def new():
        return NextUID(0)

    def get(self):
        result = self.next_uid
        self.next_uid += 1
        return result

