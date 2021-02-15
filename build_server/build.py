import json
import subprocess
from pathlib import Path

from build_server.consts import CFG_DIR, GC_DIR, PKGS_DIR


def build_drv(flake_dir: Path, attr: str, gc_root: Path):
    if gc_root.exists():
        gc_root.unlink()

    subprocess.run(
        ['nix', 'build', '-o', gc_root, f'{flake_dir}#{attr}'],
        check=True
    )


def build_package(pkg: str):
    pkg_gc_root = GC_DIR.joinpath(pkg)
    build_drv(PKGS_DIR, pkg, pkg_gc_root)


def build_system(system: str):
    system_gc_root = GC_DIR.joinpath(system)
    build_drv(
        CFG_DIR,
        f'nixosConfigurations.{system}.config.system.build.toplevel',
        system_gc_root
    )


def build_packages():
    nix_search = subprocess.run(
        ['nix', 'search', '--json', PKGS_DIR],
        capture_output=True,
        check=True
    )
    packages = json.loads(nix_search.stdout.decode('utf-8'))
    for package in packages:
        print(f'building: {package}')
        build_package(package)


def build_systems():
    systems = ['laptop', 'desktop']
    for system in systems:
        print(f'building system: {system}')
        build_system(system)
