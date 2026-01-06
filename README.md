# Overview

This is the artifact for the journal paper:

 >  Maurice Ter Beek, Maurice Laveaux, Sjef van Loo, Erik de Vink and Tim A.C. Willemse. "Family-Based Model Checking Using Variability Parity Games". XXX.

The artifact contains the implementation of the family-based model checking
approach using variability parity games (VPGs) in the tool `merc-vpg`, as well
as all experiments conducted for the paper. First of all the submodules must be
initialized and updated:

```bash
    git submodule update --init --recursive
```

After that the `Dockerfile` provides all necessary steps to build the artifact
and run the experiments. It can be built using the following command:

```bash
    docker build . -t vpg_artifact
```

The results can be found in the `results.json` file after the build has
completed, and it can be copied from the container using the following command:

```bash
    docker cp vpg_artifact:results.json ./results.json
```

There are also the complete `run.log` and `verify.log` files that show the
complete log, and the results of verifying the results, respectively. They can
be copied in a similar manner.

From the `results.json` file a LaTeX table can be generated using the provided
script `scripts/create_table.py`:

```bash
    python3 scripts/create_table.py results.json
```