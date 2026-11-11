"""Preprocessing chains saved to binary (replaces the old IoSuite.time_write_binary)."""

import tempfile
from pathlib import Path

from ._common import real_recording, set_jobs

DURATION = 30.0
CHAINS = ["none", "bandpass", "bandpass+cmr", "phase_shift+highpass+cmr", "highpass+highpass_spatial", "bandpass+whiten"]


def _chain(rec, name):
    import spikeinterface.preprocessing as spre

    if name == "none":
        return rec
    if name == "bandpass":
        return spre.bandpass_filter(rec)
    if name == "bandpass+cmr":
        return spre.common_reference(spre.bandpass_filter(rec))
    if name == "phase_shift+highpass+cmr":
        if rec.get_property("inter_sample_shift") is None:
            raise NotImplementedError("recording has no inter_sample_shift")
        return spre.common_reference(spre.highpass_filter(spre.phase_shift(rec)))
    if name == "highpass+highpass_spatial":
        return spre.highpass_spatial_filter(spre.highpass_filter(rec))
    if name == "bandpass+whiten":
        return spre.whiten(spre.bandpass_filter(rec, dtype="float32"))  # whitening matrix fitted here, untimed
    raise ValueError(name)


class _Save:
    timeout = 900
    number = 1
    repeat = 3
    warmup_time = 0

    def _setup(self, chain):
        self.rec = _chain(real_recording(DURATION), chain)
        self.tmp = tempfile.TemporaryDirectory()

    def teardown(self, *params):
        if hasattr(self, "tmp"):  # teardown also runs after a skipped setup
            self.tmp.cleanup()

    def _save(self):
        self.rec.save(format="binary", folder=Path(tempfile.mkdtemp(dir=self.tmp.name)) / "rec")


class PreprocessSaveSuite(_Save):
    params = [CHAINS, [1, 4], ["process", "thread"]]
    param_names = ["chain", "n_jobs", "pool_engine"]

    def setup(self, chain, n_jobs, pool_engine):
        if n_jobs == 1 and pool_engine == "thread":
            raise NotImplementedError("same as n_jobs=1 process")
        if pool_engine == "thread":
            from spikeinterface.core.job_tools import job_keys

            if "pool_engine" not in job_keys:  # < 0.102
                raise NotImplementedError("pool_engine not available")
        self._setup(chain)
        set_jobs(n_jobs=n_jobs, **({"pool_engine": pool_engine} if pool_engine == "thread" else {}))

    def time_save_binary(self, chain, n_jobs, pool_engine):
        self._save()


class PreprocessSaveMemorySuite(_Save):
    params = [CHAINS]
    param_names = ["chain"]

    def setup(self, chain):
        self._setup(chain)
        set_jobs(n_jobs=1)  # peakmem only sees the parent process

    def peakmem_save_binary(self, chain):
        self._save()
