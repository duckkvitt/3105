"""Build the read-only diagnostic IPA on macOS; requires no signing secrets."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import traceback
import zipfile

ROOT = Path(__file__).resolve().parents[1]
BUNDLE_ID = "com.apple.mobile.MobileHouseArrest"
IPA_NAME = "3105_iOS18.7.11_18.7.12_ChanDoan_R1_chua_ky.ipa"


def command(build_dir: Path) -> list[str]:
    return [
        "/usr/bin/xcodebuild", "-project", str(ROOT / "ThreeOneOSFive.xcodeproj"),
        "-target", "3105", "-configuration", "Release", "-sdk", "iphoneos",
        "-arch", "arm64", f"CONFIGURATION_BUILD_DIR={build_dir}",
        "SWIFT_ACTIVE_COMPILATION_CONDITIONS=$(inherited) IOS187_DIAGNOSTICS",
        "CODE_SIGNING_ALLOWED=NO", "CODE_SIGNING_REQUIRED=NO", "CODE_SIGN_IDENTITY=",
        "build",
    ]


def validate_ipa(path: Path) -> dict:
    with zipfile.ZipFile(path) as package:
        names = set(package.namelist())
        if "Payload/3105.app/Info.plist" not in names:
            raise RuntimeError("IPA is missing Payload/3105.app/Info.plist")
        if "Payload/3105.app/3105" not in names:
            raise RuntimeError("IPA is missing the app executable")
    return {
        "ipa": path.name,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "bytes": path.stat().st_size,
        "bundle_id": BUNDLE_ID,
        "build_mode": "IOS187_DIAGNOSTICS",
        "ios_targets": ["18.7.11", "18.7.12"],
        "requested_test_device": "iPhone XS Max / iOS 18.7.12",
        "kernel_execution": "disabled_by_swift_compile_condition",
        "probe": "existing MCM route; root directory read only",
        "write_test": "not_run",
        "device_test": "not_run",
        "full_ios_support_verified": False,
        "signed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--print-command", action="store_true", help="Show build arguments without running Xcode")
    args = parser.parse_args()
    if args.print_command:
        print(json.dumps(command(ROOT / "build" / "ios187-products"), indent=2))
        return 0
    if sys.platform != "darwin" or not Path("/usr/bin/xcodebuild").is_file():
        parser.error("macOS with Xcode is required. From Windows, use the included GitHub Actions workflow.")

    artifacts = ROOT / "build" / "ios187-artifacts"
    artifacts.mkdir(parents=True, exist_ok=True)
    # Fresh products prevent accidentally packaging an older, normal 3105 build.
    with tempfile.TemporaryDirectory(prefix="3105-ios187-") as temporary:
        temporary_path = Path(temporary)
        products = temporary_path / "products"
        with (artifacts / "xcodebuild.log").open("w", encoding="utf-8") as log_file:
            process = subprocess.Popen(command(products), cwd=ROOT, stdout=subprocess.PIPE,
                                       stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")
            assert process.stdout is not None
            for line in process.stdout:
                print(line, end="")
                log_file.write(line)
            if process.wait() != 0:
                raise RuntimeError("Xcode build failed; see xcodebuild.log. No IPA was created.")

        app = products / "3105.app"
        if not (app / "Info.plist").is_file() or not (app / "3105").is_file():
            raise RuntimeError("Xcode reported success but did not produce the expected 3105.app bundle")

        payload = temporary_path / "Payload"
        payload.mkdir()
        shutil.copytree(app, payload / "3105.app", symlinks=True)
        ipa = artifacts / IPA_NAME
        # Package the untouched Xcode product.  Editing Info.plist after an
        # unsigned build introduced a runner-dependent failure and is not
        # needed: IOS187_DIAGNOSTICS is compiled into the executable.
        subprocess.run(["/usr/bin/ditto", "-c", "-k", "--keepParent", str(payload), str(ipa)], check=True)
        report = validate_ipa(ipa)
        report["xcode"] = subprocess.check_output(["/usr/bin/xcodebuild", "-version"], text=True).strip()
        (artifacts / "build_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        (artifacts / "SHA256SUMS.txt").write_text(f"{report['sha256']}  {ipa.name}\n", encoding="utf-8")
        print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        artifacts = ROOT / "build" / "ios187-artifacts"
        artifacts.mkdir(parents=True, exist_ok=True)
        (artifacts / "failure_report.txt").write_text(
            "Post-build packaging failed.\\n\\n" + traceback.format_exc(), encoding="utf-8"
        )
        raise error
