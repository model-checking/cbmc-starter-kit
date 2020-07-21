This directory contains docker files for building cbmc inside a docker
container for various operating systems.

* The Dockerfile builds a container with
    * A CBMC installation: CBMC is intalled in the operating system's
      equivalent of /usr/local/bin
    * A CBMC tarball: CBMC binaries are packaged into a tarball in the
      operating system's equivalent of /tmp/cbmc.tar.gz.

* The Makefile contains two targets:
    * make container (the default) builds the container
    * make tarball mounts the container and extracts the tarball to the
      current working directory
