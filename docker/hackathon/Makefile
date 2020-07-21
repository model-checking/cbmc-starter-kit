CBMC_DEB=cbmc_5.12-132~bionic_amd64.deb
CBMC_URL=https://drive.corp.amazon.com/view/AWS%20Automated%20Reasoning%20Group/Padstone/CBMC%20Distributions/$(CBMC_DEB)?download=true

VIEWER_TAR=cbmc-viewer.tar.gz
VIEWER_URL=https://drive.corp.amazon.com/view/AWS%20Automated%20Reasoning%20Group/Padstone/CBMC%20Distributions/$(VIEWER_TAR)?download=true

default: container

$(CBMC_DEB):
	curl -o $@ -L --negotiate -u: ${CBMC_URL}

$(VIEWER_TAR):
	curl -o $@ -L --negotiate -u: ${VIEWER_URL}

container: $(CBMC_DEB) $(VIEWER_TAR)
	docker build --tag cbmc .
	@echo
	@echo Run 'docker run -it -v `pwd`:/home/cbmc cbmc'
	@echo

veryclean:
	$(RM) $(CBMC_DEB) $(VIEWER_TAR)
