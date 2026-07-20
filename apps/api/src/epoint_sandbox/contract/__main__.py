"""Contract capture CLI."""

import argparse
import json
import os
import sys
from pathlib import Path

from epoint_sandbox.contract.capture import capture, compare
from epoint_sandbox.contract.probes import by_tier

RECORDINGS = Path(__file__).resolve().parents[3] / "contract-recordings"

PRODUCTION_URL = "https://epoint.az"
SANDBOX_URL = "http://localhost:8181"


def _credentials(target: str) -> tuple[str, str]:
    prefix = "EPOINT_PROD" if target == "production" else "EPOINT_SANDBOX"
    public = os.environ.get(f"{prefix}_PUBLIC_KEY")
    private = os.environ.get(f"{prefix}_PRIVATE_KEY")

    if target == "sandbox":
        public = public or "i000000001"
        private = private or "sandbox_private_key_0000000001"

    if not public or not private:
        sys.exit(
            f"Set {prefix}_PUBLIC_KEY and {prefix}_PRIVATE_KEY before capturing against {target}."
        )
    return public, private


def cmd_capture(args: argparse.Namespace) -> int:
    target = args.against
    base_url = args.url or (PRODUCTION_URL if target == "production" else SANDBOX_URL)
    public, private = _credentials(target)

    if target == "production" and args.tier == "B":
        print("Tier B creates real transactions and moves real money.")
        if input("Type 'yes' to continue: ").strip().lower() != "yes":
            return 1

    out_dir = RECORDINGS / target
    probes = by_tier(args.tier)
    print(f"Capturing {len(probes)} tier {args.tier} probes from {base_url}")

    recordings = capture(base_url, public, private, args.tier, out_dir)

    for recording in recordings:
        keys = sorted(recording.body) if isinstance(recording.body, dict) else "non-dict"
        print(f"  {recording.http_status}  {recording.probe:32} {keys}")

    print(f"\nWrote {len(recordings)} recordings to {out_dir}")
    return 0


def cmd_compare(args: argparse.Namespace) -> int:
    reference = RECORDINGS / args.reference
    candidate = RECORDINGS / args.candidate

    if not reference.exists():
        sys.exit(f"No recordings at {reference}. Capture them first.")
    if not candidate.exists():
        sys.exit(f"No recordings at {candidate}. Capture them first.")

    differences = compare(reference, candidate)
    if not differences:
        print(f"{args.candidate} matches {args.reference} on every recorded probe.")
        return 0

    print(f"{len(differences)} divergence(s) between {args.reference} and {args.candidate}:\n")
    for difference in differences:
        print(json.dumps(difference, indent=2, ensure_ascii=False))
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(prog="epoint_sandbox.contract")
    sub = parser.add_subparsers(dest="command", required=True)

    cap = sub.add_parser("capture", help="record probe responses from a host")
    cap.add_argument("--against", choices=["sandbox", "production"], default="sandbox")
    cap.add_argument("--tier", choices=["A", "B"], default="A")
    cap.add_argument("--url", help="override the base URL")
    cap.set_defaults(func=cmd_capture)

    cmp_ = sub.add_parser("compare", help="diff two sets of recordings")
    cmp_.add_argument("--reference", default="production")
    cmp_.add_argument("--candidate", default="sandbox")
    cmp_.set_defaults(func=cmd_compare)

    args = parser.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
