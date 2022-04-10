# This test clones a proof repository and compares the proof results
# with the proof results after running cbmc-starter-kit-update.

PACKAGE_ROOT = ../..

REPO = https://github.com/FreeRTOS/coreHTTP.git
REPO_CBMC_ROOT = test/cbmc
REPO_PROOF_ROOT = $(REPO_CBMC_ROOT)/proofs
REPO_PROOFS = --proofs \
  HTTPClient_AddRangeHeader \
  HTTPClient_ReadHeader \
  HTTPClient_strerror \
  findHeaderFieldParserCallback \
  findHeaderOnHeaderCompleteCallback \
  findHeaderValueParserCallback \
  httpParserOnBodyCallback \
  httpParserOnHeaderFieldCallback \
  httpParserOnHeaderValueCallback \
  httpParserOnHeadersCompleteCallback \
  httpParserOnMessageBeginCallback \
  httpParserOnMessageCompleteCallback \
  httpParserOnStatusCallback

REPO_ROOT = /tmp/repo
LITANI_ROOT = /tmp/litani
CONFIG_ROOT = /tmp/config
REPORT_ROOT = /tmp/reports
REPORT_ROOT1 = $(REPORT_ROOT)1
REPORT_ROOT2 = $(REPORT_ROOT)2

LITANI = $(LITANI_ROOT)/litani
CONFIG = $(CONFIG_ROOT)/tests/config/config.py

default:
	@ echo "Run test with 'make test'"

test: clone-repo clone-litani clone-config run1 install-starter update-starter run2 compare

clone-repo:
	$(RM) -r $(REPO_ROOT)
	git clone $(REPO) $(REPO_ROOT)
	cd $(REPO_ROOT) && git submodule update --init --checkout --recursive

clone-litani:
	$(RM) -r $(LITANI_ROOT)
	git clone https://github.com/awslabs/aws-build-accumulator $(LITANI_ROOT)

# The config.py command is currently in the config branch of a fork
clone-config:
	$(RM) -r $(CONFIG_ROOT)
	git clone https://github.com/markrtuttle/aws-viewer-for-cbmc $(CONFIG_ROOT)
	cd $(CONFIG_ROOT) && git checkout config

install-starter:
	cd $(PACKAGE_ROOT) && make develop

update-starter:
	cd $(REPO_ROOT)/$(REPO_CBMC_ROOT) && /tmp/cbmc-starter-kit/bin/cbmc-starter-kit-update

run:
	$(RM) -r $(REPORT_ROOT)
	cd $(REPO_ROOT)/$(REPO_PROOF_ROOT) && \
	  $(LITANI) init --project-name "Report" && \
	  ./run-cbmc-proofs.py --no-standalone $(REPO_PROOFS) && \
	  $(CONFIG) --litani-bindir $(LITANI_ROOT) --report-root $(REPORT_ROOT) && \
	  $(LITANI) run-build

run1:
	$(MAKE) REPORT_ROOT=$(REPORT_ROOT1) run

run2:
	$(MAKE) REPORT_ROOT=$(REPORT_ROOT2) run

# Need to use the semantic comparison for the json output
# A simple 'diff -rq $(REPORT_ROOT1) $(REPORT_ROOT2)' fails on json property/result output
# For now, just skip comparison of the json output
compare:
	@ for html in $$(cd $(REPORT_ROOT1) && find . -name html); do \
	  diff -rq $(REPORT_ROOT1)/$$html $(REPORT_ROOT2)/$$html; \
	done
	@ for html in $$(cd $(REPORT_ROOT2) && find . -name html); do \
	  diff -rq $(REPORT_ROOT1)/$$html $(REPORT_ROOT2)/$$html; \
	done
