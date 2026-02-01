#!/usr/bin/env python3
"""
SSTS Demo — Sequence and Resistance Posture
Illustrative only. Not evidence.
"""

import matplotlib.pyplot as plt

# Fixed parameters
tau = 0.620
band = 0.050
alpha = 0.400

# Two deterministic paths ending at same endpoint
score_endpoint = 0.62

# Resistance values from documented example
s_clean = 0.0
s_fatigue = 0.033424

effective_clean = score_endpoint - alpha * s_clean
effective_fatigue = score_endpoint - alpha * s_fatigue

labels = ["Clean Path", "Fatigue Path"]
scores = [effective_clean, effective_fatigue]

plt.figure()
plt.bar(labels, scores)
plt.axhline(tau - band)
plt.axhline(tau + band)
plt.ylabel("Effective Score")
plt.title("SSTS History-Dependent Admissibility Posture")
plt.tight_layout()
plt.show()
