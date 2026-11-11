"""Shared helpers. Everything here must work on every benchmarked SpikeInterface version (0.101.2 -> main).

Convention: a benchmark that cannot run on a given version raises NotImplementedError in `setup`,
which asv records as skipped (n/a).
"""

import inspect
import json
import os
from pathlib import Path

import numpy as np

# GitHub-hosted runners have 4 cores
JOB = dict(n_jobs=4, chunk_duration="1s", progress_bar=False)


def real_recording(duration=None):
    """Real snippet written by scripts/fetch_data.py; folder given by $SI_BENCH_DATA."""
    data = os.environ.get("SI_BENCH_DATA")
    if not data or not (Path(data) / "meta.json").is_file():
        raise NotImplementedError("SI_BENCH_DATA not set or missing meta.json: run scripts/fetch_data.py")
    from probeinterface import ProbeGroup
    from spikeinterface.core import BinaryRecordingExtractor

    folder = Path(data)
    meta = json.loads((folder / "meta.json").read_text())
    rec = BinaryRecordingExtractor(
        file_paths=[str(folder / "traces.raw")],
        sampling_frequency=meta["sampling_frequency"],
        dtype=meta["dtype"],
        num_channels=meta["num_channels"],
        gain_to_uV=np.array(meta["gain_to_uV"]),
        offset_to_uV=np.array(meta["offset_to_uV"]),
        is_filtered=False,
    )
    # old versions return a copy with the probe; newer ones set it in place and return None
    rec = rec.set_probegroup(ProbeGroup.from_dict(meta["probegroup"])) or rec
    for key, values in meta.get("properties", {}).items():
        rec.set_property(key, np.array(values))
    if duration is not None:
        rec = rec.frame_slice(0, int(duration * rec.sampling_frequency))
    return rec


def synthetic_gt(folder, duration=120.0, num_channels=128, num_units=100):
    """Ground-truth recording saved to a binary folder (real I/O, not on-the-fly generation) + its sorting."""
    from spikeinterface.core import generate_ground_truth_recording

    rec, sorting = generate_ground_truth_recording(
        durations=[duration], num_channels=num_channels, num_units=num_units, seed=0
    )
    return rec.save(folder=folder, **JOB), sorting


def is_zarr_v3():
    import zarr

    return int(zarr.__version__.split(".")[0]) >= 3


def codec(name, **kwargs):
    """numcodecs codec by name, in the flavour the installed zarr expects (SI main is zarr v3, releases are v2)."""
    if is_zarr_v3():
        import numcodecs.zarr3 as nc
    else:
        import numcodecs as nc
    return getattr(nc, name)(**kwargs)


def set_jobs(**overrides):
    """Job kwargs go through the global setting: same API on every version, so calls need no job kwargs."""
    from spikeinterface.core import set_global_job_kwargs

    set_global_job_kwargs(**{**JOB, **overrides})


def si_call(func, *args, method_kwargs=None, **kwargs):
    """Call a sortingcomponents function in either API style.

    <= 0.102: method params are flat **kwargs; >= 0.103: they go in a `method_kwargs=` dict.
    """
    if "method_kwargs" in inspect.signature(func).parameters:
        kwargs["method_kwargs"] = method_kwargs or {}
    else:
        kwargs.update(method_kwargs or {})
    return func(*args, **kwargs)


def quality_metric_names():
    try:
        from spikeinterface.metrics.quality import get_quality_metric_list, get_quality_pca_metric_list
    except ImportError:  # < 0.104
        from spikeinterface.qualitymetrics import get_quality_metric_list, get_quality_pca_metric_list
    return set(get_quality_metric_list()) | set(get_quality_pca_metric_list())


# parents an extension requires at compute time but does not list in depend_on
_UNDECLARED_PARENTS = {"valid_unit_periods": ["amplitude_scalings"]}


def compute_parents(analyzer, extension_name):
    """Compute (untimed) the missing parents of an extension, recursively."""
    from spikeinterface.core.sortinganalyzer import get_extension_class

    for parent in get_extension_class(extension_name).depend_on + _UNDECLARED_PARENTS.get(extension_name, []):
        parent = parent.split("|")[0]  # "a|b" means either: take the first
        if not analyzer.has_extension(parent):
            compute_parents(analyzer, parent)
            analyzer.compute(parent)


def folder_size(path):
    return sum(f.stat().st_size for f in Path(path).rglob("*") if f.is_file())
