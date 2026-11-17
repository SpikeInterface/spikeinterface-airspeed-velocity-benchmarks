# SpikeInterface Airspeed Velocity (ASV) Benchmarking

Benchmarks for [SpikeInterface](https://github.com/SpikeInterface/spikeinterface), run with
[airspeed velocity](https://asv.readthedocs.io). Results:
https://spikeinterface.github.io/spikeinterface-airspeed-velocity-benchmarks/

## What is benchmarked

| Module | Suites |
|---|---|
| `benchmarks.py` | import time of every submodule |
| `bench_zarr.py` | save to zarr by compressor (Blosc zstd/lz4 levels, WavPack) x filter (Delta), chunking and sharding (zarr v3 only); read speed and compression ratio (`track_`) |
| `bench_preprocessing.py` | preprocessing chains saved to binary, by `n_jobs` / `pool_engine`; peak memory |
| `bench_postprocessing.py` | `SortingAnalyzer`: one benchmark per extension, one per quality metric, create/load per format |
| `bench_sortingcomponents.py` | peak detection, peak localization (motion correction not yet: most presets need torch) |

Benchmarks that cannot run on a given SpikeInterface version (e.g. an extension that did not exist yet)
are skipped and show as n/a. Shared helpers, including the few version switches, are in `_common.py`.

Benchmarked versions: the latest patch of each minor from 0.101 (the first with `SortingAnalyzer`),
listed in `hashestobenchmark.txt`, plus `main`.

## Data

zarr, preprocessing and sortingcomponents suites use a real Neuropixels snippet (a few minutes, 384 ch),
written by `scripts/fetch_data.py` in a version-independent layout (`traces.raw` + `meta.json`).
Point `SI_BENCH_DATA` to it; without it those suites are skipped. Postprocessing uses synthetic ground truth.

```bash
python scripts/fetch_data.py --out data/np_snippet            # from the S3 source set in the script
python scripts/fetch_data.py --source synthetic --out data/np_snippet  # offline, for smoke tests
export SI_BENCH_DATA=$PWD/data/np_snippet
```

In CI the snippet is cached, keyed on the hash of `fetch_data.py`.

## Useful commands

```bash
# quick smoke test against the SpikeInterface installed in the current env
asv run --python=same --quick --show-stderr
asv run --python=same --quick --bench PostprocessingSuite   # one suite

# all benchmarked tags, then main
asv run --skip-existing-successful HASHFILE:hashestobenchmark.txt
asv run main^!

# a specific tag or commit
asv run 0.105.4^!

# refresh hashestobenchmark.txt (run in a spikeinterface checkout)
for t in 0.101.2 0.102.3 0.103.2 0.104.9 0.105.4; do git rev-list -n1 $t; done

# look at results locally / publish
asv publish && asv preview
asv gh-pages
```
