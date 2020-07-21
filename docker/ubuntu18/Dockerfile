FROM ubuntu:18.04

ENV CBMC /cbmc
ENV PKG cbmc
ENV TARBALL /tmp/${PKG}.tar.gz

RUN apt update && apt install -y \
    bison  \
    cmake \
    flex \
    gcc \
    g++ \
    git \
    jq \
    make \
    maven \
    ninja-build \
    patch \
    python3

RUN \
    git clone https://github.com/diffblue/cbmc.git ${CBMC} && \
    cd ${CBMC} && \
    git submodule update --init && \
    mkdir build && \
    cd build && \
    cmake -GNinja .. && \
    ninja && \
    ninja install && \
    cp -r bin ${PKG} && \
    tar fcz ${TARBALL} ${PKG} && \
    cd / && \
    rm -rf ${CBMC}
