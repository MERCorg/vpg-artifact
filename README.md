# Overview

First, initialize and update the submodules:

```bash
git submodule update --init --recursive
```

Apply the patches to `mCRL2` and `merc`:

```bash
cd mCRL2
git apply ../mcrl2.patch
```

Finally, for the results without applying the reachability on the projected parity games, apply the following patch:

```bash
cd merc/
git apply ../merc_no_reachability.patch
```