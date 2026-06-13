import os
import sys
import shutil
import subprocess
import platform
import argparse
import tempfile


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
    project_root = os.path.dirname(os.path.abspath(__file__))
    for artifact in (
        os.path.join(project_root, "dist"),
        os.path.join(project_root, "build"),
        os.path.join(project_root, "komoot-takeout.spec"),
    ):
        if os.path.exists(artifact):
            print(f"Cleaning {os.path.relpath(artifact, project_root)}...")
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
    zip_path = os.path.join(os.path.dirname(dist_executable), zip_name)
    if os.path.exists(zip_path):
        os.remove(zip_path)

    # zip command preserves executable permissions better than shutil.make_archive.
    subprocess.check_call(["zip", "-j", zip_path, dist_executable])
    print(f"Created release archive: {zip_path}")

def main():
    """Build the application with PyInstaller"""
    args = parse_args()
    project_root = os.path.dirname(os.path.abspath(__file__))
    dist_dir = os.path.join(project_root, 'dist')
    build_dir = os.path.join(project_root, 'build')
    spec_dir = project_root
    entry_script = os.path.join(project_root, 'pywebview_app.py')
    index_template = os.path.join(project_root, 'templates', 'index.html')

    print("Building komoot-takeout with PyInstaller...")

    clean_previous_builds()
    if args.clean_only:
        print("Clean complete.")
        return
    
    # Determine data separator based on OS
    separator = ';' if platform.system().lower() == 'windows' else ':'
    
    # Build command
    cmd = [
        sys.executable,
        '-m',
        'PyInstaller',
        '--noconfirm',
        '--clean',
        f'--distpath={dist_dir}',
        f'--workpath={build_dir}',
        f'--specpath={spec_dir}',
        f'--paths={project_root}',
        '--name=komoot-takeout',
        '--onefile', 
        '--windowed',
        f'--add-data={index_template}{separator}templates',
        '--hidden-import=flask',
        '--hidden-import=komoot_adapter',
        '--hidden-import=bs4',
        '--hidden-import=gpxpy',
        '--hidden-import=webview',
        '--hidden-import=requests', 
        '--hidden-import=zipfile',
        '--hidden-import=concurrent.futures',
        '--hidden-import=komootgpx',
        entry_script
    ]

    if platform.system().lower() == 'darwin':
        cmd.append(f'--target-architecture={args.macos_arch}')
        print(f"macOS target architecture: {args.macos_arch}")
    
    print(f"Running build command...")
    
    # Run PyInstaller
    with tempfile.TemporaryDirectory(prefix='komoot-takeout-pyi-') as tmp_cwd:
        subprocess.check_call(cmd, cwd=tmp_cwd)

    executable_name = get_executable_name()
    dist_executable = os.path.join(dist_dir, executable_name)
    if not os.path.exists(dist_executable):
        raise FileNotFoundError(f"Expected executable not found: {dist_executable}")

    maybe_create_macos_zip(dist_executable, args.macos_arch)
    
    print("\nBuild completed successfully!")
    print(f"Executable can be found in {dist_executable}")

if __name__ == "__main__":
    main()