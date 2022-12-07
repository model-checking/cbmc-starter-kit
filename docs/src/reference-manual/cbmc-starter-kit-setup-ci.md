# Reference manual

## Name

`cbmc-starter-kit-setup-ci` - Add GitHub Actions workflow to run proofs as part of CI

## Synopsis

```
cbmc-starter-kit-setup-ci [-h]
  --github-actions-runner <name-of-GitHub-hosted-runner-operating-on-Ubuntu-20.04>
  [--cbmc <X.Y.Z>]
  [--cbmc-viewer <X.Y>]
  [--litani <X.Y.Z>]
  [--kissat <TAG>]
  [--cadical <TAG>]
  [--verbose] [--debug] [--version]
```

## Description

This script will copy a GitHub Action workflow to `.github/workflows` of your
repository. The workflow will runs CBMC proofs on every push event.

The workflow must be executed in a GitHub-hosted Ubuntu 20.04 runner. If the
proofs are unable to run in
[GitHub's standard Runner](https://docs.github.com/en/actions/using-github-hosted-runners/about-github-hosted-runners#supported-runners-and-hardware-resources),
you may need to constrain some proofs' parallelism with the
[`EXPENSIVE`](https://model-checking.github.io/cbmc-starter-kit/tutorial/index.html#the-makefile)
setting, or [create a Large Runner for your repository](https://docs.github.com/en/actions/using-github-hosted-runners/using-larger-runners).

The script offers users with the option of specifying custom versions and tags
for all tools being used inside of the CI.

For a given invocation of the GitHub Actions workflow, the results of the 
execution of all CBMC proofs will be presented in a tabular format in the logs
of the GitHub Actions step called "CBMC proof results". 2 tables are being
printed out that summarize the number of proofs that succeeded/failed as well
as individual statuses per CBMC proof. Aside for the logs, these tables are also  available at the "Summary" page for this particular invocation workflow. Finally,
a zip artifact, which contains all logs and artifacts pertaining to this
execution of CBMC proofs, is available to be downloaded at this "Summary" page.

If a CBMC proof fails, the GitHub Actions workflow will fail at the
"CBMC proof results" step.
