[![Tests](https://github.com//ckanext-unfold/workflows/Tests/badge.svg?branch=master)](https://github.com//ckanext-unfold/actions)

# ckanext-unfold

Preview for different archive formats

## What are the dependencies?

Working with different archive formats requires different tools:

### RAR, CBR

It depends on `unrar` command-line utility to do the actual decompression. Note that by default it expect it to be in `PATH`.
If unrar launching fails, you need to fix this.

Alternatively, `rarfile` can also use either [unar](https://theunarchiver.com/command-line) from [TheUnarchiver](https://theunarchiver.com/) or
[bsdtar](https://github.com/libarchive/libarchive/wiki/ManPageBsdtar1) from [libarchive](https://www.libarchive.org/) as
decompression backend. From those unar is preferred as bsdtar has very limited support for RAR archives.

It depends on [cryptography](https://pypi.org/project/cryptography/) or [PyCryptodome](https://pypi.org/project/pycryptodome/)
modules to process archives with password-protected headers.


## Config settings

TODO

## License

[AGPL](https://www.gnu.org/licenses/agpl-3.0.en.html)
