#!/usr/bin/env python3
"""Give freerouting 2.1 a dummy profile so its CLI run can finish.

With an empty profile email the router shows a modal User Settings
dialog after autorouting and never writes the session file. The
settings live in /tmp/freerouting/freerouting.json (created on the
first run). Telemetry and contact stay off.
"""

import json
import os
import sys

PATH = "/tmp/freerouting/freerouting.json"


def main() -> int:
    if not os.path.exists(PATH):
        print(f"{PATH} missing, run freerouting once first")
        return 0
    d = json.load(open(PATH))
    profile = d.setdefault("profile", {})
    if profile.get("email"):
        return 0
    profile["email"] = "none@localhost"
    profile["allow_telemetry"] = False
    profile["allow_contact"] = False
    json.dump(d, open(PATH, "w"), indent=2)
    print("freerouting profile set")
    return 0


if __name__ == "__main__":
    sys.exit(main())
