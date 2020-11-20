from pymarshal import (
    type_assert,
    type_assert_iter,
)

class Stretch:
    def __init__(
        self,
        uid,
        wav_pool_uid,
        algorithm,
        ratio,
        pitch,
    ):
        self.uid = type_assert(uid, int)
        self.wav_pool_uid = type_assert(
            wav_pool_uid,
            int,
        )
        self.algorithm = type_assert(
            algorithm,
            str,
            choices=("Rubberband", "SBSMS", "TODO",),
            desc="The algorith used",
        )
        self.ratio = type_assert(
            ratio,
            float,
            check=lambda x: x >= 0.01 and x != 1.0,
            desc="The amount of stretch.  0.5 == half length, 2.0 == double",
        )
        self.pitch = type_assert(
            pitch,
            float,
            desc="The pitch shift of this file",
        )

    def key(self):
        return (
            self.wav_pool_uid,
            self.algorithm,
            self.ratio,
            self.pitch,
        )

class Stretches:
    def __init__(
        self,
        entries,
    ):
        self.entries = type_assert_iter(
            entries,
            Stretch,
        )

    def add(self, entry):
        type_assert(entry, Stretch)
        if entry.key() not in self.by_key():
            self.entries.append(entry)

    def by_key(self):
        return {
            x.key(): x
            for x in self.entries
        }

