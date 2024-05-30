

### Some useful commands

Our plan is to benchmark on all the recent tags


```bash
asv run 0.100.0^!
asv run 0.100.1^!
asv run 0.100.2^!
asv run 0.100.3^!
asv run 0.100.4^!
asv run 0.100.5^!
asv run 0.100.6^!
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


### To-do
* We have a benchmark for the function `write_to_binary`. 
* Let's run this single benchmark for python versions 3.8, 3.9. 3.10, 3.11 and 3.12.
* Let's run also this single benchmark for the latest five release tags
* Check that visualization works.
* Push that to github page`s.
