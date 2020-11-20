from pymarshal import (
    type_assert,
    type_assert_dict,
    type_assert_iter,
)
import datetime


class Recording:
    def __init__(
        self,
        start,
        stop,
        lookup,
    ):
        self.start = type_assert(
            start,
            str,
            cast_from=datetime.datetime,
            desc="The date and time that the recording started",
        )
        self.stop = type_assert(
            stop,
            str,
            cast_from=datetime.datetime,
            desc="The date and time that the recording stopped",
        )
        self.lookup = type_assert_dict(
            lookup,
            kcls=str,
            vcls=int,
            desc="audio input name -> uid",
        )

class Recordings:
    def __init__(
        self,
        recordings,
    ):
        self.recordings = type_assert_iter(
            recordings,
            Recording,
        )

