from pymarshal.json import type_assert, type_assert_iter


class AudioItem:
    def __init__(
        self,
        wav_pool_uid,
        pos,
        end,
        start_offset,
        fade_in_end,
        fade_out_start,
        fade_in_vol,
        fade_out_vol,
        volume,
        pitch_mode, # time affecting pitch, pitch affecting time
        pitch_start,
        pitch_end,
        reverse,
        send_mode,
        paifx_uid,
    ):
        self.wav_pool_uid = type_assert(
            wav_pool_uid,
            int,
            desc="The wav pool uid of the audio file",
        )
        self.pos = type_assert(
            pos,
            float,
            desc="The beat within the pattern that starts playback",
        )
        self.end = type_assert(
            end,
            float,
            desc="The beat within the pattern that ends playback",
        )
        self.start_offset = type_assert(
            start_offset,
            float,
            check=lambda x: x >= 0. and x < 1.,
            desc="The offset of the start of the sample, from 0.0 to <1.0"
        )
        self.fade_in_end = type_assert(
            fade_in_end,
            float,
            check=lambda x: x >= 0. and x <= fade_out_start,
            desc="The position in the sample to end fade-in, 0.0 to 1.0",
        )
        self.fade_out_start = type_assert(
            fade_out_start,
            float,
            check=lambda x: x >= fade_in_end and x <= 1.,
            desc="""
                The position in the sample to start the fade-out, 0.0 to 1.0
            """,
        )
        self.fade_in_vol = type_assert(
            fade_in_vol,
            float,
            desc="""
                <=0.0, The volume at which fade in starts, in decibels
                For example, -24dB would start at -24dB, be at -12dB halfway
                through fade_in_end, then 0dB at fade_in_end.
            """,
        )
        self.fade_out_vol = type_assert(
            fade_out_vol,
            float,
            desc="Same as fade_in_vol, but for fade out",
        )
        self.volume = type_assert(
            volume,
            float,
            desc="The volume of the item in decibels",
        )
        self.pitch_mode = type_assert(
            pitch_mode,
            int,
            choices=(0, 1, 2),
            desc="0=None, 1=Pitch affecting time, 2=Time affecting pitch",
        )
        self.pitch_start = type_assert(
            pitch_start,
            float,
            desc="""
                The pitch (or time rate) at the start of the sample.
                For pitch_mode=0, this is ignored.
                For pitch_mode=1, 0.0 = normal pitch, 12.0 = 1 octave up,
                -12.0 = 1 octave down
                For pitch_mode=2, must be >0.0, 2.0 = double speed,
                0.5 = half speed
            """,
        )
        self.pitch_end = type_assert(
            pitch_end,
            float,
            desc="""
                Same as pitch_start, but for the end of the item.
                If different than pitch start, the value will interpolate
                between the 2 values for the duration of the item.
            """,
        )
        self.reverse = type_assert(
            reverse,
            int,
            choices=(0, 1),
            desc="0 to play the sample as normal, 1 to play it backwards",
        )
        self.send_mode = type_assert(
            send_mode,
            int,
            choices=(0, 1, 2),
            desc="0: Normal, 1: Sidechain, 2: Both",
        )
        self.paifx_uid = type_assert(
            paifx_uid,
            int,
            desc="""
                The UID of the per-audio-item-effects controls for this
                audio item.
            """,
        )
