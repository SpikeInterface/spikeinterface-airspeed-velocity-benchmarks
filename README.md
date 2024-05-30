
# Spikeinterface Airspeed Velocity (ASV) Benchmarking

This repository contains the benchmarking code for the SpikeInterface project. We use the Airspeed Velocity (ASV) framework to run the benchmarks. The benchmarks are run on the SpikeInterface codebase and the results can be visualized on the following website:

https://spikeinterface.github.io/spikeinterface-airspeed-velocity-benchmarks/




### Some useful commands

Our plan is to benchmark on all the recent tags. They are stored in the files hashes_to_benchmark.txt and can be fetched using the following command:

```bash
git log --tags --simplify-by-decoration --pretty="format:%H" -n 10
```
Now the benchmark can be run by using the following command:

```bash
asv run HASHFILE:hashestobenchmark.txt
```

How to benchmark a specific commit

```bash
asv run 0.100.6^!
```

Specific commmit

```bash
asv run 790715c959898baaf71335dd7c27d233fd434cdc^! --verbose --steps 1
```

How to benchmark using the python environment

```bash
asv run --setps 1 --python=same
```

Git tricks to fetch the latest tags and their hashes

```bash
git describe --tags `git rev-list --tags --max-count=30`
``` 

Prettier
```bash
git log --tags --simplify-by-decoration --pretty="format:%H" -n 10
```

Push results to github pages

```bash
asv gh-pages
```