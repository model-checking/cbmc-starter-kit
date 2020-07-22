FROM centos:7

ENV PKG cbmc
ENV TARBALL /tmp/${PKG}.tar.gz

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

ENV CMAKE /cmake
ENV CMAKE_REPO https://github.com/Kitware/CMake.git
ENV CMAKE_TAG v3.18.0

RUN \
    git clone ${CMAKE_REPO} ${CMAKE} && \
    cd ${CMAKE} && \
    git checkout -b ${CMAKE_TAG} ${CMAKE_TAG} && \
    ./bootstrap --parallel=$(nproc) -- -DCMAKE_USE_OPENSSL=OFF && \
    make -j$(nproc) && \
    make install && \
    cd / && \
    rm -rf ${CMAKE} && \
    echo -n "CMake version: " && \
    cmake --version

ENV NINJA /ninja
ENV NINJA_REPO https://github.com/ninja-build/ninja.git

RUN \
    git clone ${NINJA_REPO} ${NINJA} && \
    cd ${NINJA} && \
    python3 ./configure.py --bootstrap && \
    mkdir build2 && \
    cd build2 && \
    PATH=..:$PATH cmake -GNinja .. && \
    PATH=..:$PATH ninja && \
    PATH=..:$PATH ninja install && \
    cd / && \
    rm -rf ${NINJA} && \
    echo -n "Ninja version: " && \
    ninja --version

RUN \
    yum install -y yum-utils centos-release-scl && \
    yum --enablerepo=centos-sclo-rh-testing install -y devtoolset-7-gcc devtoolset-7-gcc-c++ && \
    yum --enablerepo=centos-sclo-rh-testing install -y glibc-static && \
    source /opt/rh/devtoolset-7/enable  && \
    echo -n "GCC version: " && \
    gcc --version && \
    echo -n "G++ version: " && \
    g++ --version

ENV CBMC /cbmc
ENV CBMC_REPO https://github.com/diffblue/cbmc.git

RUN \
    source /opt/rh/devtoolset-7/enable  && \
    git clone ${CBMC_REPO} ${CBMC} && \
    cd ${CBMC} && \
    git submodule update --init && \
    mkdir build && \
    cd build && \
    cmake -GNinja -DCMAKE_EXE_LINKER_FLAGS="-static" .. && \
    ninja && \
    ninja install && \
    cp -r bin ${PKG} && \
    tar fcz ${TARBALL} ${PKG} && \
    cd / && \
    rm -rf ${CBMC} && \
    echo -n "CBMC version: " && \
    cbmc --version
