from pymarshal.csv import marshal_csv, unmarshal_csv
from sglib.models.daw.engine.audio import RackAudioEvent


def test_marshal_unmarshal():
    event = RackAudioEvent(
        wav_pool_uid=0,
        pos=0,
        start=0,
        end=10000,
        attack_end=0,
        attack_recip=1.,
        attack_vol=1.,
        fade_in_end=0,
        fade_in_recip=1.,
        fade_in_vol=-18.,
        fade_out_start=123,
        fade_out_recip=1.,
        fade_out_vol=-18.,
        release_start=456,
        release_recip=1.,
        release_vol=1.,
        volume_left=1.,
        volume_right=1.,
        pitch_mode=1,
        pitch_start=0.,
        pitch_end=0.,
        reverse=0,
        send_mode=0,
        paifx_uid=0,
    )
    _csv = marshal_csv([event])
    _cls = unmarshal_csv(_csv, {'a': RackAudioEvent})[0]
    assert _cls.__dict__ == event.__dict__, (_cls.__dict__, event.__dict__)

