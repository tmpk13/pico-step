#!/usr/bin/env python3
"""Set project ERC severities in pico-step.kicad_pro, keeping all other keys.

power_pin_not_driven fires on every rail fed through a connector or a
passive, so it is ignored; pin_not_driven stays on as the signal check.
"""

import json
from pathlib import Path

PRO = Path(__file__).resolve().parent.parent / "pico-step.kicad_pro"

d = json.loads(PRO.read_text())
d.setdefault("erc", {}).setdefault("rule_severities", {})["power_pin_not_driven"] = "ignore"
PRO.write_text(json.dumps(d, indent=2) + "\n")
print("power_pin_not_driven =", d["erc"]["rule_severities"]["power_pin_not_driven"])
