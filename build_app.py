import os
import sys
import shutil
import subprocess
import platform
import argparse


def parse_args():
    parser = argparse.ArgumentParser(
        description="Build komoot-takeout with PyInstaller"
    )
    parser.add_argument(
        "--macos-arch",
        choices=["x86_64", "arm64", "universal2"],
        default=os.environ.get("MACOS_TARGET_ARCH", "universal2"),
        help=(
            "Target architecture for macOS builds. "
            "Defaults to MACOS_TARGET_ARCH env var or universal2."
        ),
    )
    parser.add_argument(
        "--clean-only",
        action="store_true",
        help="Clean dist/build/spec artifacts and exit.",
    )
    return parser.parse_args()


def clean_previous_builds():
    for artifact in ("dist", "build", "komoot-takeout.spec"):
        if os.path.exists(artifact):
            print(f"Cleaning {artifact}...")
            if os.path.isdir(artifact):
                shutil.rmtree(artifact)
            else:
                os.remove(artifact)


def get_executable_name():
    if platform.system().lower() == "windows":
        return "komoot-takeout.exe"
    return "komoot-takeout"


def maybe_create_macos_zip(dist_executable, arch):
    if platform.system().lower() != "darwin":
        return

    zip_name = f"komoot-takeout-macos-{arch}.zip"
    zip_path = os.path.join("dist", zip_name)
    if os.path.exists(zip_path):
        os.remove(zip_path)

    # zip command preserves executable permissions better than shutil.make_archive.
    subprocess.check_call(["zip", "-j", zip_path, dist_executable])
    print(f"Created release archive: {zip_path}")

def main():
    """Build the application with PyInstaller"""
    args = parse_args()
    print("Building komoot-takeout with PyInstaller...")

    clean_previous_builds()
    if args.clean_only:
        print("Clean complete.")
        return
    
    # Determine data separator based on OS
    separator = ';' if platform.system().lower() == 'windows' else ':'
    
    # Build command
    cmd = [
        'pyinstaller',
        '--noconfirm',
        '--clean',
        '--name=komoot-takeout',
        '--onefile', 
        '--windowed',
        f'--add-data=templates/index.html{separator}templates',
        '--hidden-import=flask',
        '--hidden-import=komoot_adapter',
        '--hidden-import=bs4',
        '--hidden-import=gpxpy',
        '--hidden-import=webview',
        '--hidden-import=requests', 
        '--hidden-import=zipfile',
        '--hidden-import=concurrent.futures',
        '--hidden-import=komootgpx',
        'pywebview_app.py'
    ]

    if platform.system().lower() == 'darwin':
        cmd.append(f'--target-architecture={args.macos_arch}')
        print(f"macOS target architecture: {args.macos_arch}")
    
    print(f"Running build command...")
    
    # Run PyInstaller
    subprocess.check_call(cmd)

    executable_name = get_executable_name()
    dist_executable = os.path.join('dist', executable_name)
    if not os.path.exists(dist_executable):
        raise FileNotFoundError(f"Expected executable not found: {dist_executable}")

    maybe_create_macos_zip(dist_executable, args.macos_arch)
    
    print("\nBuild completed successfully!")
    print(f"Executable can be found in {dist_executable}")

if __name__ == "__main__":
    main()