# Overview

First, initialize and update the submodules:

```bash
git submodule update --init --recursive
```

Apply the patches to `mCRL2` and `merc`:

```bash
cd mCRL2
git apply ../mcrl2.patch
cd ../merc
git apply ../merc.patch
```