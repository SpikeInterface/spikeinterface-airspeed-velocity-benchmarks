"""SortingAnalyzer: one benchmark per extension, one per quality metric, and analyzer formats.

Uses synthetic ground truth (a sorting is needed; the real snippet has none).
"""

import tempfile
from pathlib import Path

from ._common import compute_parents, quality_metric_names, set_jobs, synthetic_gt

EXTENSIONS = [
    "random_spikes",
    "waveforms",
    "templates",
    "noise_levels",
    "amplitude_scalings",
    "spike_amplitudes",
    "spike_locations",
    "unit_locations",
    "principal_components",
    "template_similarity",
    "correlograms",
    "isi_histograms",
    "acgs_3d",
    "valid_unit_periods",
    "template_metrics",
    "quality_metrics",
    "spiketrain_metrics",
]

# union over versions (isolation_distance/l_ratio -> mahalanobis). The nn_* family is left out:
# > 15 min each on CI (and single-process with an in-memory analyzer).
QUALITY_METRICS = [
    "num_spikes",
    "firing_rate",
    "presence_ratio",
    "snr",
    "isi_violation",
    "rp_violation",
    "sliding_rp_violation",
    "synchrony",
    "firing_range",
    "amplitude_cv",
    "amplitude_cutoff",
    "amplitude_median",
    "noise_cutoff",
    "drift",
    "sd_ratio",
    "isolation_distance",
    "l_ratio",
    "mahalanobis",
    "d_prime",
    "nearest_neighbor",
    "silhouette",
]


def _make_analyzer(parents):
    """Ground truth + binary_folder analyzer with `parents` computed, in the asv setup_cache cwd."""
    from spikeinterface.core import create_sorting_analyzer

    set_jobs()
    rec, sorting = synthetic_gt(Path("gt_recording").absolute())
    folder = Path("analyzer").absolute()
    analyzer = create_sorting_analyzer(sorting, rec, format="binary_folder", folder=folder, sparse=True)
    for name in parents:
        analyzer.compute(name)
    return str(folder)


def _load_in_memory(folder):
    import spikeinterface.full  # noqa: F401  registers every extension on every version
    from spikeinterface.core import load_sorting_analyzer

    # timed computes then don't include disk writes, and never touch the cached folder
    return load_sorting_analyzer(folder).save_as(format="memory")


class PostprocessingSuite:
    params = [EXTENSIONS]
    param_names = ["extension"]
    timeout = 900
    number = 1
    repeat = 3
    warmup_time = 0

    def setup_cache(self):
        return _make_analyzer(["random_spikes", "noise_levels", "templates"])

    def setup(self, folder, extension):
        import spikeinterface.full  # noqa: F401
        from spikeinterface.core.sortinganalyzer import get_extension_class

        try:
            get_extension_class(extension)
        except Exception:
            raise NotImplementedError(f"{extension} not available in this version")
        set_jobs()
        self.analyzer = _load_in_memory(folder)
        compute_parents(self.analyzer, extension)

    def time_compute(self, folder, extension):
        self.analyzer.compute(extension)

    def peakmem_compute(self, folder, extension):
        set_jobs(n_jobs=1)  # peakmem only sees the parent process
        self.analyzer.compute(extension)


class QualityMetricSuite:
    params = [QUALITY_METRICS]
    param_names = ["metric"]
    timeout = 900
    number = 1
    repeat = 3
    warmup_time = 0

    def setup_cache(self):
        parents = ["random_spikes", "noise_levels", "waveforms", "templates", "spike_amplitudes", "spike_locations"]
        return _make_analyzer(parents + ["principal_components"])

    def setup(self, folder, metric):
        if metric not in quality_metric_names():
            raise NotImplementedError(f"{metric} not available in this version")
        set_jobs()
        self.analyzer = _load_in_memory(folder)

    def time_compute(self, folder, metric):
        self.analyzer.compute("quality_metrics", metric_names=[metric])


DEFAULT_SET = ["random_spikes", "noise_levels", "templates", "spike_amplitudes", "unit_locations"]


class AnalyzerCreateSuite:
    params = [["memory", "binary_folder", "zarr"]]
    param_names = ["format"]
    timeout = 900
    number = 1
    repeat = 3
    warmup_time = 0

    def setup_cache(self):
        set_jobs()
        rec, sorting = synthetic_gt(Path("gt_recording").absolute())
        sorting = sorting.save(folder=Path("gt_sorting").absolute())
        return rec, sorting

    def setup(self, cache, format):
        set_jobs()
        self.rec, self.sorting = cache
        self.tmp = tempfile.TemporaryDirectory()

    def teardown(self, cache, format):
        self.tmp.cleanup()

    def time_create_and_compute(self, cache, format):
        from spikeinterface.core import create_sorting_analyzer

        folder = None if format == "memory" else Path(tempfile.mkdtemp(dir=self.tmp.name)) / "analyzer"
        analyzer = create_sorting_analyzer(self.sorting, self.rec, format=format, folder=folder, sparse=True)
        analyzer.compute(DEFAULT_SET)


class AnalyzerLoadSuite:
    params = [["binary_folder", "zarr"]]
    param_names = ["format"]
    timeout = 900

    def setup_cache(self):
        from spikeinterface.core import create_sorting_analyzer

        set_jobs()
        rec, sorting = synthetic_gt(Path("gt_recording").absolute())
        folders = {}
        for format in self.params[0]:
            folder = Path(f"analyzer_{format}").absolute()
            analyzer = create_sorting_analyzer(sorting, rec, format=format, folder=folder, sparse=True)
            analyzer.compute(DEFAULT_SET)
            folders[format] = str(analyzer.folder)  # zarr may add a suffix
        return folders

    def time_load_sorting_analyzer(self, folders, format):
        from spikeinterface.core import load_sorting_analyzer

        load_sorting_analyzer(folders[format])
