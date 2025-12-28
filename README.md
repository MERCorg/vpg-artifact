# Overview

This is the artifact for the journal paper "Family-Based Model Checking Using Variability Parity Games" by Maurice Ter Beek, Maurice Laveaux, Sjef van Loo, Erik de Vink and Tim A.C. Willemse.

The artifact contains the implementation of the family-based model checking approach using variability parity games (VPGs) in the tool `merc-vpg`, as well as all experiments conducted for the paper. First of all the submodules must be initialized and updated:

```bash
git submodule update --init --recursive
```

After that the `Dockerfile` provides all necessary steps to build the artifact and run the experiments. It can be built using the following command:

```bash
docker build .
```