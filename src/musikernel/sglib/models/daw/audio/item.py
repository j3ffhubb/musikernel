from sglib.math import (
    clip_value,
    db_to_lin,
    pitch_to_ratio,
)
from pymarshal.json import type_assert, type_assert_iter


class AudioItem:
    def __init__(
        self,
        uid,
        wav_pool_uid,
        start,
        end,
        attack,
        fade_in_end,
        fade_in_vol,
        fade_out_start,
        fade_out_vol,
        release,
        volume,
        pitch_mode, # time affecting pitch, pitch affecting time
        pitch_start,
        pitch_end,
        reverse,
        paifx_uid,
        pan,
    ):
        self.uid = type_assert(uid, int)
        self.wav_pool_uid = type_assert(
            wav_pool_uid,
            int,
            desc="The wav pool uid of the audio file",
        )
        self.end = type_assert(
            end,
            float,
            check=lambda x: x > 0. and x <= 1.,
            desc="""
                0.0 to 1.0, the end of the audio item, as a fraction of
                the end of the audio file
            """,
        )
        self.start = type_assert(
            start,
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
                PLACEHOLDER: CURRENTLY IGNORED
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
        self.paifx_uid = type_assert(
            paifx_uid,
            int,
            desc="""
                The UID of the per-audio-item-effects controls for this
                audio item.
            """,
        )
        self.attack = type_assert(
            attack,
            int,
            check=lambda x: x >= 0 and x <= 50,
            desc="""
                The attack of the audio item envelope, in milliseconds.
                Will go from linear 0.0 to the bottom of the fade in volume
                in this time.  If attack is longer than the fade in, there
                will be no fade in.  If there is no fade in, there will be
                no attack.
            """,
        )
        self.release = type_assert(
            release,
            int,
            check=lambda x: x >= 0 and x <= 50,
            desc="""
                The release of the audio item envelope, in milliseconds.
                Will go from linear 0.0 to the bottom of the fade out volume
                in this time.  If release is longer than the fade out, there
                will be no fade out.  If there is no fade out, there will be
                no release.
            """
        )
        self.pan = type_assert(
            pan,
            float,
            allow_none=True,
            desc="""
                Pan for this audio item.
                -1 == left only, 0 == center, 1 == right only
            """,
        )

    def compile_fade_in(
        self,
        pos,
        length,
        sr,
    ):
        """
            @pos:
                int, The global positon of of the audio item, in samples
            @length:
                int, The length of the item, in samples, minus any start and
                end offset
            @sr:
                int, The sample rate of the audio device, in hertz
            @return:
                attack_end:
                    int, The global sample that attack ends on
                attack_recip:
                    float, The reciprocal of the length of the attack
                attack_vol:
                    float, The linear (not decibels) value that the attack
                    ends at before transitioning to the fade in
                fade_in_end:
                    int, The global sample that fade in ends on
                fade_in_recip:
                    int, The reciprocal of the fade in length in samples
        """
        attack_length = int(
            clip_value(
                self.attack * 0.001 * sr,
                0,
                length,
                True,
            ),
        )
        attack_recip = 1. / (attack_length or 1.)
        attack_end = attack_length + pos

        fade_in_length = int(
            clip_value(
                length * self.fade_in_end,
                0,
                length - attack_length,
                True,
            )
        )
        fade_in_recip = 1. / (fade_in_length or 1.)
        fade_in_end = fade_in_length + attack_end
        if fade_in_end > attack_end:
            attack_vol = db_to_lin(self.fade_in_vol)
        else:
            attack_vol = 1.0

        return (
            attack_end,
            attack_recip,
            attack_vol,
            fade_in_end,
            fade_in_recip,
        )

    def compile_fade_out(
        self,
        pos,
        length,
        sr,
    ):
        """
            @pos:
                int, The global positon of of the audio item, in samples
            @length:
                int, The length of the item, in samples, minus any start and
                end offset
            @sr:
                int, The sample rate of the audio device, in hertz
            @return:
                fade_out_start:
                    int, The global sample that fade out starts on
                fade_out_recip:
                    int, The reciprocal of the fade out length, in samples
                release_start:
                    int, The global sample that release starts on
                release_recip:
                    float, The reciprocal of the length of the release
                release_vol:
                    float, The linear (not decibels) value that fade out
                    ends at before transitioning to the release
        """
        # in samples
        release_length = int(
            clip_value(
                self.release * 0.001 * sr,
                0,
                length,
                True,
            )
        )
        end = pos + length
        release_recip = 1. / (release_length or 1.)
        release_start = end - release_length
        fade_out_length = int(
            clip_value(
                length * (1.0 - self.fade_out_start),
                0,
                length - release_length,
                True,
            ),
        )
        fade_out_recip = 1. / (fade_out_length or 1.)
        fade_out_start = end - fade_out_length - release_length
        if fade_out_start < release_start:
            release_vol = db_to_lin(self.fade_out_vol)
        else:
            release_vol = 1.0

        return (
            fade_out_start,
            fade_out_recip,
            release_start,
            release_recip,
            release_vol,
        )

    def get_rate(self):
        if self.pitch_mode == 0:
            return pitch_to_ratio(self.pitch_start)
        elif self.pitch_mode == 1:
            return self.pitch_start
        raise ValueError(
            "Invalid pitch_mode: {}".format(self.pitch_mode),
        )

