# Blender USD plugin

This work is very preliminary. Basically, I needed an easy way to test out subdivision surfaces with ARKit on iOS and there wasn't a way to easily export crease info to USD, so I created this.

If you are interested in contributing, I might take your patches. In any case, feel free to fork and add to this.

## TODO:

- [ ] USDZ support
    - [ ] Selector for USD format
    - [ ] Add any images to bundle



## How it works

Because the USD tools use Python 2 and blender uses Python 3.5 (as of 2.79b), this code does not import the USD tools into Blender directly. Rather, it launches python as a subprocess running `io_export_usd/usd_python2/usdWriter.py outputFilename.usd` and then feeds it commands in JSON format over STDIN.

## Installation

### Installation macOS

Copy the USD directory from [https://developer.apple.com/go/?id=python-usd-library](Apple's build of the USD SDK) `USDPython/USD/` as `io_export_usd/usd_python2/USD/` in this repository, then symlink this into your user scripts directory:

```
python symlink.py
```

### Installation Linux

Not tested, but you should be able to install a built version of USD in the same location. You might need to adjust the python 2 path in the source code for your configuration.

### Installation Windows

Not yet supported

## Troubleshooting

If you want to see debug output, run blender on the command line (it prints there)

```bash
alias blender=/Applications/blender.app/Contents/MacOS/blender
blender
```
