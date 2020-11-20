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
        """ Add a file to the wav pool
            @entry: WavPoolEntry, the entry to add
            @raises:
                FileExistsError: If @entry is already in the WavPool
        """
        type_assert(entry, WavPoolEntry)
        pm_assert(
            (
                entry.path not in self.by_path()
                and
                entry.uid not in self.by_uid()
            ),
            FileExistsError,
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
        volume,
        pan,
        pan_law,
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
            #check=lambda x: os.path.isfile(x),
            desc="The full path to the file.",
        )
        self.default_paifx_uid = type_assert(
            default_paifx_uid,
            int,
            desc="""
                The default per-audio item effects uid to assign to
                new audio item instances of this file
            """,
        )
        self.volume = type_assert(
            volume,
            float,
            desc="""
                Volume for this entry, in decibels.
                Used to globally modify the volume of all instances of this
                sample, is combined with other volume adjustments in the item
                and the reference.
            """,
        )
        self.pan = type_assert(
            pan,
            float,
            allow_none=True,
            desc="""
                Pan for this file.
                -1 == left only, 0 == center, 1 == right only
            """,
        )
        self.pan_law = type_assert(
            pan_law,
            float,
            desc="""
                The pan law for this file.  0.0 will maintain volume of the
                channel being panned towards.  -3, for example, will attenuate
                the channel being panned to by 3dB when fully panned.
            """,
        )

    @staticmethod
    def new(
        uid,
        path,
        cache_dir,
        cached,
        paifx_uid,
        volume=0.,
        pan=None,
        pan_law=0.,
    ):
        """ Add a new file to the wav pool, caching it in the project
            @uid:
                int, The next available uid in this project
            @path:
                str, The local path to the file
            @cache_dir:
                str, The project wav file cache dir
            @cached:
                bool, True to cache the file, otherwise False.  The file should
                be in $project/audio/local if False, and @path should be only a
                file name rather than an absolute path to the source
            @paifx_uid:
                int, The default per-audio-item effects uid for this file
            @volume:
                float, The volume of this entry
        """
        mut = mutagen.File(path)
        sample_count = int(mut.info.sample_rate * mut.info.length)
        sample_rate = mut.info.sample_rate
        channels = mut.info.channels
        # Current behavior is to overwrite even if it exists
        if cached:
            # TODO: Windows
            cache_file = os.path.join(
                cache_dir,
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
            int(cached),
            path,
            paifx_uid,
            volume,
            pan,
            pan_law
        )

    def project_length(
        self,
        sr,
        start,
        end,
        rate,
    ):
        """ The length this sample will be in a project
            @sr:
                int, The sample rate of the audio device
            @start:
                float, 0. to 1., where the sample starts playing
            @end:
                float, 0. to 1., the end of the sample
            @rate:
                float, The rate at which the sample will play, for example:
                    1.0: normal speed
                    2.0: double
                    0.5: half
                    Convert semitones to linear first

            @return:
                int, The count of samples
        """
        frac = end - start
        sample_count = int(
            round(self.sample_count * frac)
        )
        sr_rate = self.sample_rate / sr
        final_rate = rate * sr_rate
        return int(
            round(sample_count / final_rate)
        )

