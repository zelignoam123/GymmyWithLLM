"""Diagnostic: connect to CoppeliaSim and check which pypot-expected joints exist in the loaded scene.

Run with the venv's python:
    .venv/bin/python probe_joints.py
"""
import json
from pypot.vrep.io import VrepIO

EXPECTED = [
    "l_elbow_y", "head_y", "r_arm_z", "head_z",
    "r_shoulder_x", "r_shoulder_y", "r_elbow_y",
    "l_arm_z", "abs_z", "bust_y", "bust_x",
    "l_shoulder_x", "l_shoulder_y",
]

io = VrepIO("127.0.0.1", 19997)
print("Connected to CoppeliaSim on 19997.")
print()
print(f"{'joint':<20} {'handle':<10} status")
print("-" * 45)
missing = []
for name in EXPECTED:
    try:
        h = io.get_object_handle(name)
        ok = h > 0
        print(f"{name:<20} {h!s:<10} {'OK' if ok else 'MISSING'}")
        if not ok:
            missing.append(name)
    except Exception as e:
        print(f"{name:<20} {'?':<10} ERROR: {e}")
        missing.append(name)
print()
if missing:
    print("MISSING joints:", missing)
else:
    print("All expected joints found. The 'No value' error is coming from something else.")
io.close()
