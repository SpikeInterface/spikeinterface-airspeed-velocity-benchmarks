"""Saving to / reading from zarr: compressors, filters, chunking and (zarr v3 only) sharding."""

import itertools
import tempfile
from pathlib import Path

import numpy as np

from ._common import codec, folder_size, is_zarr_v3, real_recording, set_jobs

DURATION = 30.0

# "none" is deliberately absent: on SI main compressor=None falls back to the default compressor,
# while releases <= 0.105 write uncompressed, so the plot would show a fake jump.
COMPRESSORS = ["default", "zstd-1", "zstd-5", "zstd-9", "lz4-5", "wavpack"]
FILTERS = ["none", "delta"]


def _compressor(name):
    if name == "default":
        from spikeinterface.core import get_default_zarr_compressor

        return get_default_zarr_compressor()
    if name == "wavpack":
        try:
            if is_zarr_v3():
                from wavpack_numcodecs.wavpackv3 import WavPack  # wavpack-numcodecs >= 0.3
            else:
                from wavpack_numcodecs import WavPack
        except ImportError:
            raise NotImplementedError("wavpack-numcodecs missing or too old for this zarr")
        return WavPack()
    cname, clevel = name.split("-")
    # shuffle=2 (bitshuffle) as int: the only form accepted by both numcodecs 0.15 and 0.16
    return codec("Blosc", cname=cname, clevel=int(clevel), shuffle=2)


def _compression_kwargs(compressor, filters):
    kwargs = dict(compressor=_compressor(compressor))
    if filters == "delta":
        kwargs["filters"] = [codec("Delta", dtype="int16")]
    return kwargs


def _chunking_kwargs(chunk_duration, channel_chunk_size, shard_factor):
    if shard_factor is not None and not is_zarr_v3():
        raise NotImplementedError("sharding needs zarr v3")
    kwargs = dict(chunk_duration=chunk_duration)
    if channel_chunk_size is not None:
        kwargs["channel_chunk_size"] = channel_chunk_size
    if shard_factor is not None:
        kwargs["shard_factor"] = shard_factor
    return kwargs


class _Write:
    """time/peakmem of rec.save(format="zarr"); subclasses set params and zarr_kwargs."""

    timeout = 900
    number = 1
    repeat = 3
    warmup_time = 0

    def setup(self, *params):
        self.kwargs = self.zarr_kwargs(*params)
        self.rec = real_recording(DURATION)
        self.tmp = tempfile.TemporaryDirectory()
        set_jobs()

    def teardown(self, *params):
        if hasattr(self, "tmp"):  # teardown also runs after a skipped setup
            self.tmp.cleanup()

    def _save(self):
        self.rec.save(format="zarr", folder=Path(tempfile.mkdtemp(dir=self.tmp.name)) / "rec.zarr", **self.kwargs)

    def time_save_zarr(self, *params):
        self._save()

    def peakmem_save_zarr(self, *params):
        set_jobs(n_jobs=1)  # peakmem only sees the parent process
        self._save()


class _Read:
    """Each variant is written once in setup_cache; then read speed and compression ratio."""

    timeout = 1800

    def setup_cache(self):
        set_jobs()
        rec = real_recording(DURATION)
        folders = {}
        for combo in itertools.product(*self.params):
            try:
                kwargs = self.zarr_kwargs(*combo)
            except NotImplementedError:
                continue
            folder = Path("_".join(map(str, combo)) + ".zarr").absolute()
            rec.save(format="zarr", folder=folder, **kwargs)
            folders[combo] = str(folder)
        return folders

    def setup(self, folders, *params):
        if params not in folders:
            raise NotImplementedError("variant not available in this version")
        from spikeinterface.core import read_zarr

        self.folder = folders[params]
        self.rec = read_zarr(self.folder)
        fs = int(self.rec.sampling_frequency)
        self.starts = np.random.default_rng(0).integers(0, self.rec.get_num_samples() - fs, 10)
        self.fs = fs

    def time_read_random_1s(self, folders, *params):
        for start in self.starts:
            self.rec.get_traces(start_frame=start, end_frame=start + self.fs)

    def time_read_random_1s_64ch(self, folders, *params):
        channel_ids = self.rec.channel_ids[:64]
        for start in self.starts:
            self.rec.get_traces(start_frame=start, end_frame=start + self.fs, channel_ids=channel_ids)

    def track_compression_ratio(self, folders, *params):
        raw = self.rec.get_num_samples() * self.rec.get_num_channels() * self.rec.get_dtype().itemsize
        return raw / folder_size(self.folder)

    track_compression_ratio.unit = "x"


class _Compression:
    params = [COMPRESSORS, FILTERS]
    param_names = ["compressor", "filters"]
    zarr_kwargs = staticmethod(_compression_kwargs)


class _Chunking:
    params = [["0.1s", "1s", "5s"], [None, 64], [None, 10]]
    param_names = ["chunk_duration", "channel_chunk_size", "shard_factor"]
    zarr_kwargs = staticmethod(_chunking_kwargs)


class ZarrCompressionSuite(_Compression, _Write):
    pass


class ZarrCompressionReadSuite(_Compression, _Read):
    pass


class ZarrChunkingSuite(_Chunking, _Write):
    pass


class ZarrChunkingReadSuite(_Chunking, _Read):
    pass
