FROM ubuntu:24.04

# Install dependencies
ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y \
# Dependencies for mCRL2
 build-essential \
 cmake \
 git \
 libboost-dev \
 python3 \
 python3-pip \
 python3-psutil \ 
 z3 \
# Requires to install Rust
 curl
 
# Build mCRL2 from source
COPY ./mCRL2 /root/mCRL2/

# Configure build
RUN mkdir ~/mCRL2/build && cd ~/mCRL2/build && cmake . \
 -DCMAKE_BUILD_TYPE=RELEASE \
 -DMCRL2_ENABLE_GUI_TOOLS=OFF \
 ~/mCRL2

# Build the toolset and install it such that the tools are available on the PATH
ARG THREADS=8
RUN cd ~/mCRL2/build && make -j${THREADS} && make install

# Install Rust for building merc
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y

# Build merc from source
COPY ./merc /root/merc/

RUN cd ~/merc/ \
    && cargo build --release

# Copy the experiments into the container
COPY ./cases/ /root/cases/
COPY ./script/ /root/script/

RUN scripts/prepare.sh -t /usr/bin -m /root/merc/target/release/