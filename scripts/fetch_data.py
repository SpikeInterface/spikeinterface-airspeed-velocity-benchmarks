"""Write the real-data snippet used by the benchmarks, in a version-independent layout:

    <out>/traces.raw   int16, (num_samples, num_channels)
    <out>/meta.json    sampling_frequency, dtype, gains/offsets, probegroup, extra properties

Runs once (outside asv) with any recent SpikeInterface; CI caches <out>, keyed on this file's hash,
so changing SOURCE or DURATION_S invalidates the cache.

    python scripts/fetch_data.py [--source s3://...zarr | synthetic] [--out data/np_snippet]
"""

import argparse
import json
from pathlib import Path

# open AIND bucket, SpikeInterface zarr compressed with WavPack (needs wavpack-numcodecs to decode)
SOURCE = (
    "s3://aind-open-data/ecephys_830852_2026-02-25_10-32-11/ecephys/ecephys_compressed/"
    "experiment1_Record Node 101#Neuropix-PXI-100.ProbeA-AP.zarr"
)
DURATION_S = 60.0  # benchmarks use 30 s; 384 ch x 30 kHz x 60 s ~ 1.4 GB (raise to minutes for motion)
START_S = 60.0  # skip the first minute (often noisy at the start of a session)
# recording properties the benchmarks need (phase_shift uses inter_sample_shift)
PROPERTIES = ["inter_sample_shift"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default=SOURCE)
    parser.add_argument("--out", default="data/np_snippet")
    args = parser.parse_args()

    import spikeinterface.core as si

    out = Path(args.out)
    if (out / "meta.json").is_file():
        print(f"{out} already exists, nothing to do")
        return
    if not args.source:
        raise SystemExit("No source: set SOURCE in scripts/fetch_data.py or pass --source")

    if args.source == "synthetic":
        # for local smoke tests without network
        from spikeinterface.preprocessing import scale

        rec, _ = si.generate_ground_truth_recording(durations=[DURATION_S], num_channels=384, num_units=100, seed=0)
        rec = scale(rec, gain=1 / 0.195, dtype="int16")  # uV -> int16 counts, NP gain
        rec.set_channel_gains(0.195)
        rec.set_channel_offsets(0.0)
    else:
        import wavpack_numcodecs  # noqa: F401  registers the WavPack codec used by AIND compressed data

        rec = si.read_zarr(args.source, storage_options={"anon": True})
        if rec.get_num_segments() > 1:
            rec = rec.select_segments([0])
        fs = rec.sampling_frequency
        start = min(int(START_S * fs), max(rec.get_num_samples() - int(DURATION_S * fs), 0))
        rec = rec.frame_slice(start, start + int(DURATION_S * fs))

    out.mkdir(parents=True, exist_ok=True)
    # threads: the S3 client is not fork-safe, and reading is network-bound anyway
    si.write_binary_recording(
        rec, file_paths=[out / "traces.raw"], dtype="int16", n_jobs=8, pool_engine="thread", progress_bar=True
    )
    meta = dict(
        sampling_frequency=float(rec.sampling_frequency),
        dtype="int16",
        num_channels=int(rec.get_num_channels()),
        gain_to_uV=rec.get_channel_gains().tolist(),
        offset_to_uV=rec.get_channel_offsets().tolist(),
        probegroup=rec.get_probegroup().to_dict(array_as_list=True),
        properties={p: rec.get_property(p).tolist() for p in PROPERTIES if rec.get_property(p) is not None},
    )
    (out / "meta.json").write_text(json.dumps(meta))
    print(f"wrote {out}: {rec.get_num_channels()} ch, {rec.get_total_duration():.0f} s")


if __name__ == "__main__":
    main()
