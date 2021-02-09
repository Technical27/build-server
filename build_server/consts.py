import re
from getpass import getuser
from pathlib import Path

HOME = Path.home()
PKGS_DIR = HOME.joinpath('pkgs')
CFG_DIR = HOME.joinpath('cfg')
NVIM_JSON_PATH = PKGS_DIR.joinpath('neovim-src.json')
LIBUSB_JSON_PATH = PKGS_DIR.joinpath('libusb-src.json')
GC_DIR = Path('/nix/var/nix/gcroots/per-user').joinpath(getuser()).joinpath('build-server')
FAKE_HASH = 'sha256-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA='
HASH_RE = re.compile('\s+got:\s+(sha256-[a-zA-Z0-9/+=]+)')
