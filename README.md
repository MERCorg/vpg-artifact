# Overview

This artifact accompanies the journal paper:

> Maurice Ter Beek, Maurice Laveaux, Sjef van Loo, Erik de Vink and Tim A.C. Willemse. "Family-Based Model Checking Using Variability Parity Games". XXX.

This repository contains the implementation of the family-based model checking
approach using variability parity games (VPGs) in the tool `merc-vpg`, as well
as all experiments conducted for the paper.

First, initialize and update the submodules:

```bash
git submodule update --init --recursive
```

The provided `Dockerfile` contains the necessary steps to build the artifact and
run the experiments. Build the image with:

```bash
docker build . -t vpg_artifact
```

Run the Docker image:

```bash
docker run -it --mount type=bind,source=./results/,target=/root/results vpg_artifact
```

Inside the container, execute the experiments with:

```bash
python3 /root/scripts/run.py /root/merc/target/release/ /root/results/
```

After the run completes, the results are available in `results/results.json`.
Full logs are in `results/run.log`. A Latex table can be generated from the results
using the provided script.

```bash
python3 /root/scripts/create_table.py /root/results/results.json
```

Verify the results (this will check that all results match the expected output
and produce `results/verify.log`):

```bash
python3 /root/scripts/verify.py /root/results/
```