from .seq_ref import SequenceRef
from pymarshal import type_assert_iter
from sglib.models.daw.engine.seq_ref import EngineSeqRef


class Playlist:
    """ A collection of Sequences, played sequentially """
    def __init__(
        self,
        sequences,
    ):
        self.sequences = type_assert_iter(
            sequences,
            SequenceRef,
            desc="""
                The uids of the sequences to be played, in the order they
                should be played in.
            """,
        )

    @staticmethod
    def new():
        return Playlist([SequenceRef(0, 0, -1)])

    def compile(
        self,
        seq_by_uid,
        sr,
    ):
        """ Compile the playlist to the engine format
            @seq_by_uid:
                {uid: Sequence}, The sequences in this project
            @sr:
                int, The sample rate of the audio device, in hertz

            @return: list-of-EngineSeqRef
        """
        result = []
        for ref in self.sequences:
            seq = seq_by_uid[ref.uid]
            tempo_map = seq.tempo_map(sr)
            start = tempo_map.sample_num(ref.start)
            if ref.end == -1:
                length = len(seq)
                end = tempo_map.sample_num(length)
            else:
                end = tempo_map.sample_num(ref.end)
            eng = EngineSeqRef(
                ref.uid,
                start,
                end,
            )
            result.append(eng)
        return result

