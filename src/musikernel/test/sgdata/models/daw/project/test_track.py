from sgdata.models.daw.project.track import DawTrack, DawTracks


def test_active_tracks():
    tracks = DawTracks.new()
    active = tracks.active_tracks()
    assert active == set(range(32)), active

    tracks.tracks[12].solo = 1
    active = tracks.active_tracks()
    assert active == set([12]), active
    tracks.tracks[12].solo = 0

    tracks.tracks[31].mute = 1
    active = tracks.active_tracks()
    assert active == set(range(31)), active
    tracks.tracks[31].mute = 0

def test_tracks_by_uid():
    tracks = DawTracks.new()
    by_uid = tracks.by_uid()
    assert by_uid, by_uid
    for k, v in by_uid.items():
        assert k == v.uid, (k, v.uid)

