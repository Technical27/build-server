import os
import re
from pathlib import Path
from typing import Tuple

from pygit2 import Signature


def load_env() -> Tuple[Path, Path, Path, str, str, str]:
    pkgs_dir = os.getenv('PKGS_DIR')
    cfg_dir = os.getenv('CFG_DIR')
    gc_dir = os.getenv('GC_DIR')
    gh_token = os.getenv('GITHUB_TOKEN')
    amo_user = os.getenv('MOZILLA_ADDONS_USER')
    amo_secret = os.getenv('MOZILLA_ADDONS_SECRET')

    assert pkgs_dir is not None, 'PKGS_DIR is undefined'
    assert cfg_dir is not None, 'CFG_DIR is undefined'
    assert gc_dir is not None, 'GC_DIR is undefined'
    assert gh_token is not None, 'GITHUB_TOKEN is undefined'
    assert amo_user is not None, 'MOZILLA_ADDONS_USER is undefined'
    assert amo_secret is not None, 'MOZILLA_ADDONS_SECRET is undefined'

    return Path(pkgs_dir), Path(cfg_dir), Path(gc_dir), gh_token, amo_user, amo_secret

PKGS_DIR, CFG_DIR, GC_DIR, GITHUB_TOKEN, MOZILLA_ADDONS_USER, MOZILLA_ADDONS_SECRET = load_env()

NVIM_JSON_PATH = PKGS_DIR.joinpath('neovim-src.json')
FIREFOX_JSON_PATH = PKGS_DIR.joinpath('firefox-src.json')

FAKE_HASH = 'sha256-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA='
HASH_RE = re.compile(r'\s+got:\s+(sha256-[a-zA-Z0-9/+=]+)')
SIGNATURE = Signature(
    'Aamaruvi Yogamani',
    '38222826+Technical27@users.noreply.github.com'
)
