from pymarshal import type_assert, type_assert_iter


class RackAudioEvent:
    _marshal_list_row_header = "a"
    def __init__(
        self,
        audio_file_uid,
        pos,
        end,
        start_offset,
        fade_in_end,
        fade_in_end_recip,
        fade_out_start,
        fade_out_start_recip,
        fade_in_vol,
        fade_out_vol,
        volume,
        pitch_mode,
        pitch_start,
        pitch_end,
        reverse,
        send_mode,
        paifx_uid,
    ):
        self.audio_file_uid = type_assert(
            audio_file_uid,
            int,
            desc="The wav pool uid of the audio file",
        )
        self.pos = type_assert(
            pos,
            int,
            desc="The sample number within the project that starts playback",
        )
        self.end = type_assert(
            end,
            int,
            desc="The sample number within the project that ends playback",
        )
        self.start_offset = type_assert(
            start_offset,
            int,
            check=lambda x: x >= 0,
            desc="The offset to start playing the sample from, in samples",
        )
        self.fade_in_end = type_assert(
            fade_in_end,
            int,
            desc="The sample number to end the fade-in on",
        )
        self.fade_in_end_recip = type_assert(
            fade_in_end_recip,
            float,
            desc="""
                One divided by the length of fade in in samples
                Used to interpolate:
                    dB=fade_in_vol-(((pos-item.pos)*recip)*fade_in_vol)
            """,
        )
        self.fade_out_start = type_assert(
            fade_out_start,
            int,
            desc="The sample number to start the fade-out on",
        )
        self.fade_out_start_recip = type_assert(
            fade_out_start_recip,
            float,
            desc="""
                One divided by the length of fade out in samples
                Used to interpolate:
                    dB=(((pos-fade_out_start)*recip)*fade_out_vol)
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

