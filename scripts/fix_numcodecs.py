"""asv install step (after the SpikeInterface wheel): pick numcodecs by the installed zarr.

asv has no per-commit requirements and reuses one env across commits, so this runs for each commit:
- zarr 2 (releases <= 0.105): numcodecs < 0.16, which zarr 2.17 (0.101.2) needs and 0.102+ pin anyway
- zarr 3 (main): the latest numcodecs, instead of whatever the previous commit left in the env
"""

import subprocess
import sys
from importlib.metadata import version

# metadata, not `import zarr`: zarr 2.17 fails to import with numcodecs >= 0.16, the case being fixed
spec = "numcodecs<0.16" if version("zarr").startswith("2.") else "numcodecs>=0.16"
subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", spec])
