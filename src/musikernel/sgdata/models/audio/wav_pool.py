from pymarshal import (
    pm_assert,
    type_assert,
    type_assert_iter,
)
import mutagen
import os
import shutil


class WavPool:
    def __init__(
        self,
        entries,
    ):
        self.entries = type_assert_iter(
            entries,
            WavPoolEntry,
        )

    @staticmethod
    def new():
        return WavPool([])

    def add(
        self,
        entry,
    ):
        type_assert(entry, WavPoolEntry)
        pm_assert(
            (
                entry.path not in self.by_path()
                and
                entry.uid not in self.by_uid()
            ),
            ValueError,
            entry.__dict__,
        )
        self.entries.append(entry)

    def by_path(self):
        return {
            x.path: x
            for x in self.entries
        }

    def by_uid(self):
        return {
            x.uid: x
            for x in self.entries
        }

class WavPoolEntry:
    def __init__(
        self,
        uid,
        sample_count,
        sample_rate,
        channels,
        cached,
        path,
        default_paifx_uid,
    ):
        self.uid = type_assert(uid, int)
        self.sample_count = type_assert(
            sample_count,
            int,
            check=lambda x: x > 0,
            desc="The count of sample frames in this file",
        )
        self.sample_rate = type_assert(
            sample_rate,
            int,
            check=lambda x: x >= 5000 and x <= 2000000,
            desc="The sample rate of the file",
        )
        self.channels = type_assert(
            channels,
            int,
            choices=(1, 2),
            desc="The channel count (1=mono, 2=stereo)",
        )
        self.cached = type_assert(
            cached,
            int,
            choices=(0, 1),
            desc="""
                1 if this file is cached locally in the project folder from
                elsewhere, 0 if the source is local to the project folder and
                therefore not cached.
            """,
        )
        self.path = type_assert(
            path,
            str,
            check=lambda x: os.path.isfile(x),
            desc="The full path to the file.",
        )
        self.default_paifx_uid = type_assert(
            default_paifx_uid,
            int,
            desc=(
                "The default per-audio item effects uid to assign to "
                "new audio item instances of this file"
            ),
        )

    @staticmethod
    def new(
        uid,
        path,
        wav_dir,
        cache,
        paifx_uid,
    ):
        """ Add a new file to the wav pool, caching it in the project
            @uid:       int, The next available uid in this project
            @path:      str, The local path to the file
            @wav_dir:   str, The project wav file cache dir
            @cache:     bool, True to cache the file, otherwise False
            @paifx_uid: int, The default per-audio-item effects uid for
                        this file
        """
        mut = mutagen.File(path)
        sample_count = int(mut.info.sample_rate * mut.info.length)
        sample_rate = mut.info.sample_rate
        channels = mut.info.channels
        # Current behavior is to overwrite even if it exists
        if cache:
            # TODO: Windows
            cache_file = os.path.join(
                wav_dir,
                path.lstrip(os.path.sep),
            )
            cache_dir = os.path.dirname(cache_file)
            if not os.path.isdir(cache_dir):
                os.makedirs(cache_dir)
            shutil.copyfile(path, cache_file)
        return WavPoolEntry(
            uid,
            sample_count,
            sample_rate,
            channels,
            int(cache),
            path,
            paifx_uid,
        )


