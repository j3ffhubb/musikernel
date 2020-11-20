from .tempo_marker import TempoMarker
from pymarshal import (
    pm_assert,
    type_assert,
    type_assert_iter,
)


class TempoMapPoint:
    def __init__(
        self,
        pos,
        sample_num,
        spb,
    ):
        self.pos = type_assert(
            pos,
            float,
            desc="Sequence position, in beats",
        )
        self.sample_num = type_assert(
            sample_num,
            int,
            desc="The song sample number at @pos in the sequence",
        )
        self.spb = type_assert(
            spb,
            int,
            desc="Samples per beat",
        )

    def beats_to_samples(
        self,
        pos,
    ):
        """
            @pos: float, Position within the sequence, in beats
            @sr:  int, Sample rate, in hertz
        """
        diff = pos - self.pos
        samples = self.spb * diff
        return int(round(samples + self.sample_num))


class TempoMap:
    def __init__(
        self,
        tmap,
    ):
        self.tmap = type_assert_iter(
            tmap,
            TempoMapPoint,
            desc="The map points in this tempo map",
        )

    @staticmethod
    def factory(
        tmarkers,
        sr,
    ):
        type_assert_iter(
            tmarkers,
            TempoMarker,
        )
        tmarkers.sort(
            key=lambda x: x.pos
        )
        type_assert(sr, int)
        pm_assert(
            sr >= 22000 and sr < 3000000,
            ValueError,
            sr,
        )
        pm_assert(
            len(tmarkers) >= 1,
            ValueError,
            tmarkers,
        )
        pm_assert(
            tmarkers[0].pos == 0.0,
            ValueError,
            tmarkers[0].pos,
        )

        def _samples_per_beat(tempo):
            return int(round((60. / tempo) * sr))

        tmap = [
            TempoMapPoint(
                0.,
                0,
                _samples_per_beat(tmarkers[0].tempo),
            )
        ]
        sample_num = 0
        for _prev, marker in zip(
            tmarkers,
            tmarkers[1:],
        ):
            sample_num += int(round(tmap[-1].spb * (marker.pos - _prev.pos)))
            point = TempoMapPoint(
                marker.pos,
                sample_num,
                _samples_per_beat(marker.tempo)
            )
            tmap.append(point)
        return TempoMap(tmap)

    def sample_num(
        self,
        pos,
    ):
        """ Return the sample number within the sequence of a position
            Works by binary searching the tempo map, then calculating
            the remainder

            @pos: float, Position within the sequence, in beats
        """
        def _shift(jump):
            jump >>= 1
            if jump == 0:
                jump = 1
            return jump
        index = jump = len(self.tmap) >> 1
        for i in range(len(self.tmap)):
            if index == len(self.tmap) - 1:
                # @pos comes after the last tempo marker
                # In theory, if we are in this logical branch, this
                # could only be true
                pm_assert(
                    self.tmap[index].pos <= pos,
                    ValueError,
                    (index, self.tmap[index].pos, pos),
                )
                return self.tmap[-1].beats_to_samples(pos)
            else:
                if self.tmap[index].pos < pos:
                    # @pos is inbetween this tempo marker and the next
                    if self.tmap[index + 1].pos > pos:
                        return self.tmap[index].beats_to_samples(pos)
                    else:
                        jump = _shift(jump)
                        index += 1
                else:
                    jump = _shift(jump)
                    index -= 1

