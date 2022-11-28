# Reference manual

## Name

`cbmc-starter-kit-setup-ci` - Add GitHub Actions workflow to run proofs as part of CI

## Synopsis

```
cbmc-starter-kit-setup-ci [-h] --github-actions-runner
                                 <ubuntu-20.04>|<name-of-your-Ubuntu-20.04-large-runner>
                                 [--cbmc <latest>|<X.Y.Z>]
                                 [--cbmc-viewer <latest>|<X.Y>]
                                 [--litani <latest>|<X.Y.Z>]
                                 [--kissat <latest>|<TAG>]
                                 [--cadical <latest>|<TAG>] [--verbose]
                                 [--debug] [--version]
```

## Description

This script adds a GitHub Actions workflow to your GitHub repository, such that
either the standard GitHub-hosted Ubuntu 20.04 runner or a larger Ubuntu 20.04
runner (
[more details on large runners in GitHub Actions](https://docs.github.com/en/actions/using-github-hosted-runners/using-larger-runners)
) execute CBMC proofs as part of your project's CI phase.

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

## Options

`--verbose`

* Verbose output.

`--debug`

* Debugging output.

`--version`

* Display version number and exit.

`--help, -h`

* Print the help message and exit.
