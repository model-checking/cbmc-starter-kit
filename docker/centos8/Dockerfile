FROM centos:8

ENV NINJA /ninja
ENV CBMC /cbmc
ENV PKG cbmc
ENV TARBALL /tmp/${PKG}.tar.gz

ENV PATH $PATH:$NINJA

RUN yum install -y \
    bison  \
    cmake \
    flex \
    gcc \
    gcc-c++ \
    git \
    jq \
    make \
    maven \
    patch \
    python3 \
    which

RUN \
    git clone https://github.com/ninja-build/ninja.git ${NINJA} && \
    cd ${NINJA} && \
    python3 ./configure.py --bootstrap

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
