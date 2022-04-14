This directory contains our documentation on how to use cbmc-viewer.

The [`mdbook` documentation](https://rust-lang.github.io/mdBook/)
explains how to use `mdbook` to generate documentation.
* The file `book.toml` is the configuration file used by `mdbook` to
  build the documentation.
* The directory `src` is the tree of markdown files that generate the
  "book" containing the documentation.
* The file `src/SUMMARY.md` is the list of "chapters" and
  "subchapters" that will appear in the book.  The only pages that
  will appear in the book are those generated from the markdown files
  listed in this summary.
* The directory `book` will contain the html making up the book.

You can build and browse the documentation by running the following
commands in this directory:
```bash
mdbook build
mdbook serve --open
```
