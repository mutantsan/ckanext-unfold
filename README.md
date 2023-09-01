[![Tests](https://github.com//ckanext-unfold/workflows/Tests/badge.svg?branch=master)](https://github.com//ckanext-unfold/actions)

# ckanext-unfold

Preview for different archive formats
### TODO
    * implement remote support for tar, 7z
    * add password support for all adapters


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

### 7Z

We are using [`py7zr`](https://py7zr.readthedocs.io/) library.

The py7zr depends on several external libraries. You should install these libraries with py7zr.
There are `PyCryptodome`, `PyZstd`, `PyPPMd`, `bcj-cffi`, `texttable`, and `multivolumefile`.
These packages are automatically installed when installing with pip command.

For extra information, please visit the [official documentation](https://py7zr.readthedocs.io/en/latest/user_guide.html#dependencies),
especially the dependencies section.

### ZIP

We are using built-in library [`zipfile`](https://docs.python.org/3/library/zipfile.html). Please consider referring to the official documentation for more information.

### TAR, TAR.XZ, TAR.GZ, TAR.BZ2

We are using built-in library [`tarfile`](https://docs.python.org/3/library/tarfile.html). Please consider referring to the official documentation for more information.

## Config settings

TODO

## License

[AGPL](https://www.gnu.org/licenses/agpl-3.0.en.html)
