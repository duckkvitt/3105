"""Static checks for the read-only iOS 18.7 diagnostic overlay.

This does not replace an Xcode build or physical-device test. It catches a
missing project entry, missing compile condition, or a workflow that cannot
produce the intended unsigned artifact.
"""
from __future__ import annotations

from pathlib import Path
import py_compile
import sys


ROOT = Path(__file__).resolve().parents[1]


def require(path: Path, fragment: str) -> None:
    text = path.read_text(encoding="utf-8")
    if fragment not in text:
        raise AssertionError(f"{path.relative_to(ROOT)} is missing: {fragment}")


def main() -> int:
    app = ROOT / "ThreeOneOSFive/App.swift"
    diagnostic = ROOT / "ThreeOneOSFive/views/IOS187DiagnosticsView.swift"
    kernel = ROOT / "ThreeOneOSFive/helpers/KernelExploit.swift"
    project = ROOT / "ThreeOneOSFive.xcodeproj/project.pbxproj"
    workflow = ROOT / ".github/workflows/ios187-diagnostic.yml"
    build = ROOT / "scripts/build_ios187_diagnostic.py"

    for path in [app, diagnostic, kernel, project, workflow, build]:
        if not path.is_file():
            raise AssertionError(f"Missing required overlay file: {path.relative_to(ROOT)}")

    require(app, "#if !IOS187_DIAGNOSTICS")
    require(diagnostic, "#if IOS187_DIAGNOSTICS")
    require(diagnostic, "@main\nstruct IOS187DiagnosticsApp")
    require(diagnostic, "let kernelExecution = \"disabled\"")
    require(diagnostic, "let writeTest = \"not_run\"")
    require(diagnostic, "static var isExpectedTestDevice")
    require(kernel, "#if IOS187_DIAGNOSTICS\n        return false")
    require(kernel, "#if IOS187_DIAGNOSTICS\n        log(\"diagnostic: kernel execution disabled\")")
    require(project, "3105M100 /* IOS187DiagnosticsView.swift */")
    require(project, "3105M200 /* IOS187DiagnosticsView.swift in Sources */")
    require(workflow, "workflow_dispatch:")
    require(workflow, "runs-on: macos-15")
    require(workflow, "python3 scripts/build_ios187_diagnostic.py")
    require(build, "IOS187_DIAGNOSTICS")
    require(build, "CODE_SIGNING_ALLOWED=NO")
    require(build, "full_ios_support_verified\": False")
    py_compile.compile(str(build), doraise=True)
    print("PASS: iOS 18.7 diagnostic overlay static checks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
