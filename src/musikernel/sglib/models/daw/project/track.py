from pymarshal import type_assert, type_assert_iter


class DawTracks:
    def __init__(
        self,
        tracks,
    ):
        self.tracks = type_assert_iter(tracks, DawTrack)

    @staticmethod
    def new():
        return DawTracks([
            DawTrack(
                i,
                0,
                0,
                "ffaabb",
                "track{}".format(i + 1),
            ) for i in range(32)
        ])

    def active_tracks(self):
        solo = set(
            x.uid
            for x in self.tracks
            if x.solo and not x.mute
        )
        if solo:
            return solo
        else:
            return set(
                x.uid
                for x in self.tracks
                if not x.mute
            )

    def by_uid(self):
        return {
            x.uid: x
            for x in self.tracks
        }

class DawTrack:
    def __init__(
        self,
        uid,
        solo,
        mute,
        color,
        name,
    ):
        self.uid = type_assert(uid, int)
        self.solo = type_assert(
            solo,
            int,
            choices=(0, 1),
            desc="1 to solo the track, 0 to not"
        )
        self.mute = type_assert(
            mute,
            int,
            choices=(0, 1),
            desc="1 to mute the track, 0 to not"
        )
        self.color = type_assert(
            color,
            str,
            desc="A hex color, for example: 000000(black), ffffff(white)",
        )
        self.name = type_assert(
            name,
            str,
            desc="The display name for this track",
        )

