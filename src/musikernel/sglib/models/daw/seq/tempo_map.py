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

    def samples_to_beats(
        self,
        pos,
        sample_count,
        end,
    ):
        """ Convert samples to beats
            @pos:
                float, The global starting position, in beats
            @sample_count:
                int, The number of samples to calculate
            @end:
                float or None, The beginning of the next TempoMapPoint, in
                beats

            @return:
                float, The number of beats added
                int, The remaining samples to process after this
        """
        beats = sample_count / self.spb
        if (
            end is not None
            and
            pos + beats > end
        ):
            result_beats = (end - pos)
            rem_beats = beats - result_beats
            rem_samples = rem_beats * self.spb
            return result_beats, rem_samples
        else:
            return beats, 0

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
        i, marker = self.binary_search(pos)
        return marker.beats_to_samples(pos)

    def binary_search(
        self,
        pos,
    ):
        """ Binary search for the marker that starts before a position
            @pos: float, The position to search for

            @return:
                int, The index of the tempo map
                TempoMapPoint, The map point that corresponds to @pos
        """
        if len(self.tmap) <= 6:
            return self.linear_search(pos)
        else:
            return self._binary_search(pos)

    def linear_search(self, pos):
        last = len(self.tmap) - 1
        for i in range(last):
            if (
                self.tmap[i].pos <= pos
                and
                self.tmap[i + 1].pos < pos
            ):
                return i, self.tmap[i]
        return last, self.tmap[-1]

    def _binary_search(self, pos):
        def _shift(jump):
            jump >>= 1
            if jump == 0:
                jump = 1
            return jump
        index = jump = len(self.tmap) >> 1 or 1
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
                return len(self.tmap) - 1, self.tmap[-1]
            else:
                if self.tmap[index].pos < pos:
                    # @pos is inbetween this tempo marker and the next
                    if self.tmap[index + 1].pos > pos:
                        return index, self.tmap[index]
                    else:
                        jump = _shift(jump)
                        index += 1
                else:
                    jump = _shift(jump)
                    index -= 1

    def beat(
        self,
        pos,
        sample_count,
    ):
        """ Return the beat that an arbitrary number of samples will end on
            @pos:
                float, A start beat
            @sample_count:
                int, The number of samples to add to @start

            @return:
                float, A beat number within the tempo map
        """
        orig_pos = pos
        i, point = self.binary_search(pos)
        last = len(self.tmap) - 1
        beats, sample_count = point.samples_to_beats(
            pos,
            sample_count,
            self.tmap[i + 1].pos if i + 1 <= last else None,
        )
        pos += beats
        while sample_count:
            i += 1
            point = self.tmap[i]
            beats, sample_count = point.samples_to_beats(
                pos,
                sample_count,
                self.tmap[i + 1].pos if i + 1 <= last else None,
            )
            pos += beats
        return pos - orig_pos

