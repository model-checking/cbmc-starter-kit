OS = centos8
TARBALL = cbmc.tar.gz

USER = $(shell whoami)
GROUP = $(shell groups | awk '{print $$1}')

default: container

container:
	docker build --tag cbmc-$(OS) .

tarball:
	docker run -v $(shell pwd):/home cbmc-$(OS) cp /tmp/$(TARBALL) /home
	sudo chown $(USER) $(TARBALL)
	sudo chgrp $(GROUP) $(TARBALL)
	mv $(TARBALL) cbmc-$(OS).tar.gz

clean:
	$(RM) *~
	$(RM) $(TARBALL) cbmc-$(OS).tar.gz

.PHONY: container tarball clean
