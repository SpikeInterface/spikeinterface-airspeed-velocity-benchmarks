"""Peak detection and localization on the real snippet (bandpass + CMR, lazy).

Motion correction is not benchmarked for now: most presets need torch."""

from pathlib import Path

import numpy as np

from ._common import real_recording, set_jobs, si_call

PEAKS_DURATION = 30.0
DETECT_KWARGS = dict(peak_sign="neg", detect_threshold=5.0)


def _preprocessed(duration):
    import spikeinterface.preprocessing as spre

    return spre.common_reference(spre.bandpass_filter(real_recording(duration), dtype="float32"))


def _detect(rec, method="locally_exclusive"):
    from spikeinterface.sortingcomponents.peak_detection import detect_peaks

    return si_call(detect_peaks, rec, method=method, method_kwargs=DETECT_KWARGS)


def _localize(rec, peaks, method):
    from spikeinterface.sortingcomponents.peak_localization import localize_peaks

    return si_call(localize_peaks, rec, peaks, method=method)


class _Slow:
    timeout = 1800
    number = 1
    repeat = 3
    warmup_time = 0


class PeakDetectionSuite(_Slow):
    # matched_filtering is left out: it needs a template prototype as input
    params = [["by_channel", "locally_exclusive"]]
    param_names = ["method"]

    def setup(self, method):
        set_jobs()
        self.rec = _preprocessed(PEAKS_DURATION)

    def time_detect_peaks(self, method):
        _detect(self.rec, method)

    def peakmem_detect_peaks(self, method):
        set_jobs(n_jobs=1)  # peakmem only sees the parent process
        _detect(self.rec, method)

    def track_num_peaks(self, method):
        """Sanity check: a speedup that silently changes results shows up here."""
        return len(_detect(self.rec, method))

    track_num_peaks.unit = "peaks"


class PeakLocalizationSuite(_Slow):
    params = [["center_of_mass", "monopolar_triangulation", "grid_convolution"]]
    param_names = ["method"]

    def setup_cache(self):
        set_jobs()
        np.save("peaks.npy", _detect(_preprocessed(PEAKS_DURATION)))
        return str(Path("peaks.npy").absolute())

    def setup(self, peaks_file, method):
        set_jobs()
        self.rec = _preprocessed(PEAKS_DURATION)
        self.peaks = np.load(peaks_file)

    def time_localize_peaks(self, peaks_file, method):
        _localize(self.rec, self.peaks, method)

    def peakmem_localize_peaks(self, peaks_file, method):
        set_jobs(n_jobs=1)
        _localize(self.rec, self.peaks, method)
