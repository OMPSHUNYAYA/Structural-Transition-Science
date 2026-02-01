#!/usr/bin/env python3
"""
SSTS Demo — Gate Partition Visualization
Illustrative only. Not evidence.
"""

import numpy as np
import matplotlib.pyplot as plt

# Fixed SSTS parameters (as documented)
tau = 0.620
band = 0.050

def gate(score):
    if score < tau - band:
        return 0  # DENY
    elif score > tau + band:
        return 2  # ALLOW
    else:
        return 1  # ABSTAIN

# Structural grid (2D slice with c fixed)
grid = np.linspace(0.0, 1.0, 101)
c_fixed = 0.62

Z = np.zeros((len(grid), len(grid)))

for i, g in enumerate(grid):
    for j, a in enumerate(grid):
        score = (g + a + c_fixed) / 3.0
        Z[j, i] = gate(score)

plt.figure()
plt.imshow(
    Z,
    origin="lower",
    extent=[0, 1, 0, 1],
)
plt.xlabel("g (alignment)")
plt.ylabel("a (access)")
plt.title("SSTS Gate Partition (c fixed at 0.62)")
plt.colorbar(ticks=[0, 1, 2], label="DENY / ABSTAIN / ALLOW")
plt.tight_layout()
plt.show()
