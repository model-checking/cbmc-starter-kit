FROM ubuntu:18.04

RUN apt update

# Add a PPA for libgcc-s1
# A bug on Ubuntu18 causes cbmc to depend on libgcc-s1
RUN apt install -y software-properties-common
RUN add-apt-repository ppa:ubuntu-toolchain-r/test
RUN apt update

RUN apt install -y gcc libgcc-s1 minisat python3 build-essential

COPY cbmc_5.12-132~bionic_amd64.deb /tmp
RUN dpkg -i /tmp/cbmc_5.12-132~bionic_amd64.deb
RUN rm /tmp/cbmc_5.12-132~bionic_amd64.deb

COPY cbmc-viewer.tar.gz /tmp
RUN cd /tmp && tar fx cbmc-viewer.tar.gz
RUN rm /tmp/cbmc-viewer.tar.gz
ENV PATH="/tmp/cbmc-viewer:/tmp/cbmc-viewer/etags/ubuntu18:${PATH}"
