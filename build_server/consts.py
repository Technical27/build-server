import re
import os
from pathlib import Path

PKGS_DIR = Path(os.getenv('PKGS_DIR'))
CFG_DIR = Path(os.getenv('CFG_DIR'))

NVIM_JSON_PATH = PKGS_DIR.joinpath('neovim-src.json')
LIBUSB_JSON_PATH = PKGS_DIR.joinpath('libusb-src.json')
FIREFOX_JSON_PATH = PKGS_DIR.joinpath('firefox-src.json')

GC_DIR = Path(os.getenv('GC_DIR'))
FAKE_HASH = 'sha256-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA='
HASH_RE = re.compile('\s+got:\s+(sha256-[a-zA-Z0-9/+=]+)')
