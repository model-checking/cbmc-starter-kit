default:
	@echo Nothing to do

pylint:
	pylint \
		--disable=missing-module-docstring \
		--disable=missing-function-docstring \
		--disable=duplicate-code \
		--module-rgx '[\w-]+' \
	*.py \
	template-for-repository/proofs/*.py \
	template-for-repository/proofs/lib/*.py
