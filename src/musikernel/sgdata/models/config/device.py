from pymarshal import type_assert


class DeviceConfig:
    def __init__(
        self,
        host_api,
        name,
        buffer_size,
        sample_rate,
        audio_engine,
        threads,
        thread_lock,
        huge_pages,
        audio_inputs,
        audio_outputs,
    ):
        self.host_api = type_assert(
            host_api,
            str,
            desc="The Portaudio host api",
        )
        self.name = type_assert(
            name,
            str,
            desc="The name of the audio device",
        )
        self.buffer_size = type_assert(
            buffer_size,
            int,
            check=lambda x: x >=16 and x <= 2048,
            desc=(
                "The buffer size, latency will be "
                "(buffer_size / sample_rate) seconds"
            ),
        )
        self.sample_rate = type_assert(
            sample_rate,
            int,
            check=lambda x: x >= 44100 and x <= 384000,
            desc="The sample rate of the audio device in hertz",
        )
        self.audio_engine = type_assert(
            audio_engine,
            int,
            # TODO: Choices and desc
        )
        self.threads = type_assert(
            threads,
            int,
            desc="0 to auto-select, otherwise the number of worker threads",
        )
        self.thread_lock = type_assert(
            thread_lock,
            int,
            choices=(0, 1),
            desc="1 to attempt to lock worker threads to a core, otherwise 0",
        )
        self.huge_pages = type_assert(
            huge_pages,
            int,
            choices=(0, 1),
            desc="1 to attempt to allocate huge page memory, otherwise 0",
        )
        self.audio_inputs = type_assert(
            audio_inputs,
            int,
            desc="The audio device inputs to make available, 0 to N",
        )
        self.audio_outputs = type_assert(
            audio_outputs,
            str,
            desc="count,ch1,ch2",
        )

