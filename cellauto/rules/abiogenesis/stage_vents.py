"""Alkaline hydrothermal vents — a proton gradient does the work (Russell/Lane).

The metabolism-first school locates the origin of life not in a "soup" energised
by lightning, but at **alkaline hydrothermal vents** like the Lost City field.
Serpentinisation of the ocean crust produces warm, alkaline (pH ~9-11),
hydrogen-rich fluid. On the early Earth the ocean was mildly acidic (CO2-rich,
pH ~5-7). Where alkaline vent fluid meets acidic ocean across the thin
catalytic (FeS) walls of a vent chimney, there is a natural **proton gradient**
of ~3-4 pH units — a built-in proton-motive force, the same kind of gradient
that every living cell uses to make ATP today (chemiosmosis).

Lane & Martin (2012) argue this geochemical gradient, not a hand-set "feed
rate", is the free-energy source that drives the first carbon fixation and
organic synthesis. This stage models exactly that: a proton field with an
alkaline chimney and an acidic ocean held at fixed values (Dirichlet sources);
the steady gradient between them carries a proton-motive force; and organic
matter is synthesised in proportion to the *steepness* of the local gradient —
so synthesis ignites along the chimney wall, the interface, rather than
uniformly. Turn the gradient off (vent and ocean to the same pH) and synthesis
stops: no gradient, no free energy, no chemistry.

References:
    Russell, M. J., & Hall, A. J. (1997). The emergence of life from iron
        monosulphide bubbles… J. Geol. Soc., 154(3), 377-402.
    Martin, W., & Russell, M. J. (2007). On the origin of biochemistry at an
        alkaline hydrothermal vent. Phil. Trans. R. Soc. B, 362, 1887-1925.
    Lane, N., & Martin, W. F. (2012). The origin of membrane bioenergetics.
        Cell, 151(7), 1406-1416.
    Sojo, V., Herschy, B., Whicher, A., Camprubí, E., & Lane, N. (2016). The
        origin of life in alkaline hydrothermal vents. Astrobiology, 16(2),
        181-197.
"""

from __future__ import annotations

import random
from collections.abc import Mapping
from dataclasses import dataclass, field

import numpy as np

from cellauto.rules.abiogenesis.science import laplacian_5pt


@dataclass
class VentState:
    protons: np.ndarray  # proton proxy: 0 = alkaline (vent), 1 = acidic (ocean)
    organic: np.ndarray  # acetate (Wood-Ljungdahl product) (H, W)
    h2: np.ndarray  # dissolved H2 — replenished inside the alkaline chimney
    co2: np.ndarray  # dissolved CO2 — replenished at the acidic ocean edges


@dataclass
class AbiogenesisStageVents:
    name: str = "abiogenesis-hydrothermal-vent"
    renderer_kind: str = "field"
    vent_alkalinity: float = 0.05  # clamped proton level inside the chimney
    ocean_acidity: float = 0.95  # clamped proton level at the ocean edges
    diffusion_H: float = 0.6  # proton diffusion (sets how sharp the interface is)
    diffusion_O: float = 0.08
    k_synth: float = 6.0  # WL mass-action rate prefactor (compensates for the 2-reactant product term)
    decay: float = 0.04  # organic decay
    dt: float = 0.2
    substeps_per_frame: int = 4
    # Real-thermodynamic calibration. The simulation's abstract proton field
    # (0 = alkaline, 1 = acidic) maps linearly to pH; defaults are the
    # Lost-City-style alkaline vent (~pH 10) versus the early-Earth ocean
    # (~pH 5.5, Krissansen-Totton et al. 2018). At 25 °C the Nernst factor is
    # 2.303 RT/F ≈ 59.16 mV per pH unit; one proton crossing the interface
    # carries Faraday = 96.485 kJ·mol⁻¹·V⁻¹ of free energy. With the defaults
    # ΔpH ≈ 4.5, PMF ≈ 266 mV, ΔG ≈ −26 kJ/mol — exactly the range Lane &
    # Martin (2012) argue can drive abiotic carbon fixation.
    pH_alkaline: float = 10.0
    pH_acidic: float = 5.5
    # Wood-Ljungdahl (acetyl-CoA pathway) calibration. The most ancient
    # carbon-fixation pathway and the only one that does not require external
    # ATP input — its net reaction
    #     2 CO2 + 4 H2  →  CH3COOH + 2 H2O      (ΔG° ≈ −95 kJ/mol)
    # is exergonic at the right pH (Russell & Martin 2004; Sojo et al. 2016).
    # In the model H2 is fed at the alkaline chimney (real Lost-City fluid
    # carries millimolar H2 from serpentinisation), CO2 at the acidic ocean
    # edges (Hadean atmosphere), and the reaction is gated by the PMF + the
    # 2:1 stoichiometry.
    pathway: str = "wood_ljungdahl"
    wl_delta_G_kJmol: float = -95.0
    wl_h2_per_acetate: float = 2.0  # normalised stoich (real biology: 4)
    wl_co2_per_acetate: float = 1.0  # normalised stoich (real biology: 2)
    h2_feed_level: float = 1.0  # clamped H2 inside the chimney
    # CO2 was dissolved everywhere in the Hadean ocean (Krissansen-Totton
    # et al. 2018); model it as a global feed toward `co2_feed_level` at rate
    # `co2_feed_rate`, rather than a Dirichlet edge clamp, so H2 emerging from
    # the chimney has CO2 to react with throughout the grid.
    co2_feed_level: float = 0.7
    co2_feed_rate: float = 0.05
    diffusion_feedstock: float = 0.20
    rng: random.Random = field(default_factory=random.Random)

    # Physical constants for the readouts (25 °C).
    _NERNST_MV_PER_PH = 59.16  # 2.303 · R · T / F at 298 K, in millivolts
    _FARADAY_KJ_PER_MOL_PER_V = 96.485  # kJ·mol⁻¹·V⁻¹

    def proton_to_pH(self, proton: float) -> float:
        """Linear map from the simulation's proton proxy [0, 1] to actual pH."""
        return float(self.pH_alkaline + (self.pH_acidic - self.pH_alkaline) * proton)

    def delta_pH(self) -> float:
        """ΔpH = pH_alkaline − pH_acidic — the gap that does thermodynamic work."""
        return float(self.pH_alkaline - self.pH_acidic)

    def pmf_mV(self) -> float:
        """Proton-motive force in millivolts. For a purely chemical gradient
        (no membrane potential), PMF = (2.303 RT/F) · ΔpH ≈ 59.16 mV per pH
        unit at 25 °C. With the defaults this is ~266 mV, comfortably above
        the ~150 mV ATP synthase needs and right in the Lane-Martin range
        for the alkaline-vent origin-of-life hypothesis."""
        return self._NERNST_MV_PER_PH * self.delta_pH()

    def delta_G_kJ_per_mol(self) -> float:
        """Free energy available per proton crossing the gradient, in kJ/mol.
        ΔG = −F · PMF (the sign convention: protons flowing *down* the
        gradient release this much energy per mole)."""
        return -self._FARADAY_KJ_PER_MOL_PER_V * (self.pmf_mV() / 1000.0)

    def _chimney_cols(self, width: int) -> tuple[int, int]:
        half = max(1, width // 12)
        c = width // 2
        return c - half, c + half

    def init_state(self, width: int, height: int) -> VentState:
        protons = np.full((height, width), self.ocean_acidity, dtype=np.float32)
        organic = np.zeros((height, width), dtype=np.float32)
        h2 = np.zeros((height, width), dtype=np.float32)
        co2 = np.zeros((height, width), dtype=np.float32)
        self._apply_sources(protons, h2, co2)
        return VentState(protons=protons, organic=organic, h2=h2, co2=co2)

    def _apply_sources(
        self,
        protons: np.ndarray,
        h2: np.ndarray | None = None,
        co2: np.ndarray | None = None,
    ) -> None:
        # Dirichlet boundary conditions. Protons (and CO2 from the atmosphere)
        # are pinned at the acidic ocean edges; protons stay alkaline and H2
        # is replenished by serpentinisation inside the chimney.
        lo, hi = self._chimney_cols(protons.shape[1])
        protons[:, lo:hi] = self.vent_alkalinity
        protons[:, :1] = self.ocean_acidity
        protons[:, -1:] = self.ocean_acidity
        if h2 is not None:
            h2[:, lo:hi] = self.h2_feed_level
        # CO2 is fed globally in step() (Hadean ocean is CO2-saturated
        # everywhere); no Dirichlet boundary needed.

    def step(self, state: VentState) -> VentState:
        H, org = state.protons, state.organic
        h2, co2 = state.h2, state.co2
        for _ in range(self.substeps_per_frame):
            H = H + self.dt * self.diffusion_H * laplacian_5pt(H)
            np.clip(H, 0.0, 1.0, out=H)
            # Diffuse feedstocks. CO2 also gets a global feed toward
            # `co2_feed_level` (Hadean ocean reservoir); H2 is replenished
            # only inside the alkaline chimney by _apply_sources.
            h2 = h2 + self.dt * self.diffusion_feedstock * laplacian_5pt(h2)
            co2 = co2 + self.dt * (
                self.diffusion_feedstock * laplacian_5pt(co2)
                + self.co2_feed_rate * (self.co2_feed_level - co2)
            )
            self._apply_sources(H, h2, co2)
            # Proton-motive force ∝ steepness of the proton gradient.
            gy, gx = np.gradient(H)
            pmf = np.hypot(gx, gy).astype(np.float32)
            # Wood-Ljungdahl mass-action rate, capped by 2:1 stoichiometry —
            # the reaction can't run faster than its limiting reagent allows.
            mass_action = self.k_synth * pmf * h2 * co2
            stoich_cap = np.minimum(h2 / self.wl_h2_per_acetate, co2 / self.wl_co2_per_acetate)
            rate = np.minimum(mass_action, stoich_cap / max(self.dt, 1e-6))
            rate = np.clip(rate, 0.0, None)
            # Update feedstocks and acetate.
            h2 = h2 - self.dt * self.wl_h2_per_acetate * rate
            co2 = co2 - self.dt * self.wl_co2_per_acetate * rate
            org = org + self.dt * (
                self.diffusion_O * laplacian_5pt(org) + rate * (1.0 - org) - self.decay * org
            )
            np.clip(h2, 0.0, 1.0, out=h2)
            np.clip(co2, 0.0, 1.0, out=co2)
            np.clip(org, 0.0, 1.0, out=org)
        state.protons, state.organic, state.h2, state.co2 = H, org, h2, co2
        return state

    def _pmf(self, state: VentState) -> np.ndarray:
        gy, gx = np.gradient(state.protons)
        return np.hypot(gx, gy).astype(np.float32)

    def render_cell(self, state: VentState, x: int, y: int) -> tuple[str, str]:
        o = float(state.organic[y, x])
        if o > 0.3:
            g = int(np.clip(o * 255, 0, 255))
            return f"#00{g:02x}b4", "rect"
        h = float(state.protons[y, x])  # 0 alkaline .. 1 acidic
        r = int(40 + h * 170)
        b = int(160 - h * 120)
        return f"#{r:02x}5a{b:02x}", "rect"

    def render_rgb(self, state: VentState) -> np.ndarray:
        h = state.protons  # 0 alkaline (blue) .. 1 acidic (orange)
        r = (40 + h * 170).astype(np.float32)
        g = np.full_like(h, 90.0)
        b = (160 - h * 120).astype(np.float32)
        # Organic synthesis glows teal-green over the pH backdrop.
        o = state.organic
        r = r * (1 - o)
        g = g * (1 - o) + 235 * o
        b = b * (1 - o) + 180 * o
        return np.clip(np.stack([r, g, b], axis=-1), 0, 255).astype(np.uint8)

    def population(self, state: VentState) -> Mapping[str, int]:
        gradient_pmf = self._pmf(state)
        organic_cells = int((state.organic > 0.3).sum())
        interface = int((gradient_pmf > 0.05).sum())
        return {
            "organic_cells": organic_cells,
            "interface_cells": interface,
            # Field-gradient magnitude (abstract units, ×1000).
            "mean_grad_x1000": int(round(float(gradient_pmf.mean()) * 1000)),
            # Real-thermodynamic readouts derived from the configured pH gap.
            "delta_pH_x10": int(round(self.delta_pH() * 10)),
            "pmf_mV": int(round(self.pmf_mV())),
            "delta_G_x10_kJmol": int(round(self.delta_G_kJ_per_mol() * 10)),
            # Wood-Ljungdahl pathway state.
            "wl_delta_G_kJmol": int(round(self.wl_delta_G_kJmol)),
            "acetate_yield_x100": int(round(float(state.organic.mean()) * 100)),
            "h2_pool_x100": int(round(float(state.h2.mean()) * 100)),
            "co2_pool_x100": int(round(float(state.co2.mean()) * 100)),
        }

    def serialize_state(self, state: VentState) -> dict:
        return {
            "protons": np.round(state.protons, 4).tolist(),
            "organic": np.round(state.organic, 4).tolist(),
            "h2": np.round(state.h2, 4).tolist(),
            "co2": np.round(state.co2, 4).tolist(),
        }

    def deserialize_state(self, data: dict) -> VentState:
        h, w = len(data["protons"]), len(data["protons"][0])
        # Older snapshots (v3.3 and earlier) did not carry the H2/CO2 feedstocks.
        # Re-seed them from the boundary conditions so playback still works.
        h2_data = data.get("h2")
        co2_data = data.get("co2")
        h2 = (
            np.array(h2_data, dtype=np.float32) if h2_data is not None else np.zeros((h, w), dtype=np.float32)
        )
        co2 = (
            np.array(co2_data, dtype=np.float32)
            if co2_data is not None
            else np.zeros((h, w), dtype=np.float32)
        )
        if h2_data is None or co2_data is None:
            protons = np.array(data["protons"], dtype=np.float32)
            self._apply_sources(protons, h2, co2)
        return VentState(
            protons=np.array(data["protons"], dtype=np.float32),
            organic=np.array(data["organic"], dtype=np.float32),
            h2=h2,
            co2=co2,
        )

    def to_config(self) -> dict:
        return {
            "vent_alkalinity": self.vent_alkalinity,
            "ocean_acidity": self.ocean_acidity,
            "diffusion_H": self.diffusion_H,
            "diffusion_O": self.diffusion_O,
            "k_synth": self.k_synth,
            "decay": self.decay,
            "dt": self.dt,
            "substeps_per_frame": self.substeps_per_frame,
            "pH_alkaline": self.pH_alkaline,
            "pH_acidic": self.pH_acidic,
            "pathway": self.pathway,
            "wl_delta_G_kJmol": self.wl_delta_G_kJmol,
            "h2_feed_level": self.h2_feed_level,
            "co2_feed_level": self.co2_feed_level,
            "diffusion_feedstock": self.diffusion_feedstock,
        }
