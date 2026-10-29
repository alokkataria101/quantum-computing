# Physics Book 2 — Study Notes
**Concepts of Physics, Volume 2 (Chapters 23–47) — H C Verma**

Heat & Thermodynamics (Ch 23–28) · Electricity & Magnetism (Ch 29–40) · Modern Physics (Ch 41–47)

> **How to use these notes.** Each chapter has *Key points*, *Formulas* and *Worked examples* with the arithmetic shown. Formulas are plain text so they read anywhere. Every number in the examples was recomputed while writing these notes.
>
> **Conventions.** `g = 10 m/s²` unless stated. `A·B` dot product, `A×B` cross product. SI units unless stated. `1 eV = 1.6 × 10⁻¹⁹ J`, and the handy shortcut `hc = 1242 eV·nm`.

---

## Contents

| Part | Chapters |
|---|---|
| Heat & thermodynamics | 23 Heat & Temperature · 24 Kinetic Theory · 25 Calorimetry · 26 Laws of Thermodynamics · 27 Specific Heats of Gases · 28 Heat Transfer |
| Electrostatics | 29 Electric Field & Potential · 30 Gauss's Law · 31 Capacitors |
| Current electricity | 32 Current in Conductors · 33 Thermal & Chemical Effects |
| Magnetism | 34 Magnetic Field · 35 Field due to a Current · 36 Permanent Magnets · 37 Magnetic Properties of Matter |
| Induction & AC | 38 Electromagnetic Induction · 39 Alternating Current · 40 EM Waves |
| Modern physics | 41 Current through Gases · 42 Photoelectric Effect · 43 Bohr's Model · 44 X-rays · 45 Semiconductors · 46 The Nucleus · 47 Relativity |
| Reference | Constants · Common mistakes |

---

# PART A — HEAT AND THERMODYNAMICS

## Chapter 23 — Heat and Temperature

**Key points**
- **Zeroth law:** if A and B are each in thermal equilibrium with C, then A and B are in equilibrium with each other — this is what makes temperature meaningful.
- Thermometers use a property that varies with temperature (mercury length, resistance, gas pressure/volume).
- The **constant-volume gas thermometer** is the standard; the **ideal-gas scale** is independent of the gas used. The triple point of water is fixed at **273.16 K**.
- **Celsius ↔ Kelvin:** `T(K) = T(°C) + 273.15`. Fahrenheit: `F = 9C/5 + 32`.
- **Ideal-gas equation:** `pV = nRT`.
- **Thermal expansion:** solids expand in length, area and volume; liquids have volume expansion only (and a real vs apparent coefficient).
- Relations: `β = 2α` (area), `γ = 3α` (volume).

**Formulas**

```
Resistance thermometer:     R_t = R_0 (1 + αt) → t = 100 (R_t − R_0)/(R_100 − R_0)
Constant-volume gas:        T = 273.16 K × (p / p_tp)
Ideal gas:                  pV = nRT = N k T          (R = 8.314 J/mol·K, k = 1.38×10⁻²³ J/K)
Linear expansion:           ΔL = L α ΔT ;   L = L0 (1 + αΔT)
Area / volume:              ΔA = 2α A ΔT ;   ΔV = 3α V ΔT = γ V ΔT
Liquid (apparent):          γ_apparent = γ_liquid − γ_container
Thermal stress (clamped):   σ = Y α ΔT
Pendulum clock:             Δt/t = ½ α ΔT   (loses time when heated)
Density with temperature:   ρ = ρ0 / (1 + γΔT)
```

**Worked example — rails.** A 30 m steel rail (`α = 1.2×10⁻⁵ /°C`) heated by 40 °C: `ΔL = 30 × 1.2×10⁻⁵ × 40 = 1.44×10⁻² m = 1.44 cm` — the reason for expansion gaps.

**Worked example — gas thermometer.** At the triple point `p = 40 kPa`; in a bath `p = 54.6 kPa`: `T = 273.16 × 54.6/40 = 372.9 K ≈ 99.7 °C`.

**Worked example — thermal stress.** Steel rod (`Y = 2×10¹¹ Pa`, `α = 1.2×10⁻⁵`) clamped and heated by 50 °C: `σ = 2×10¹¹ × 1.2×10⁻⁵ × 50 = 1.2×10⁸ Pa` (120 MPa).

**Worked example — pendulum clock.** Brass pendulum, `α = 1.2×10⁻⁵`, temperature up by 20 °C: fractional change `½ × 1.2×10⁻⁵ × 20 = 1.2×10⁻⁴`; in a day it loses `0.00012 × 86 400 ≈ 10.4 s`.

**Remember.** Water is anomalous: it contracts from 0 to 4 °C (maximum density at 4 °C), so lakes freeze from the top.

---

## Chapter 24 — Kinetic Theory of Gases

**Key points**
- **Assumptions:** many identical point-like molecules, random motion, elastic collisions, no intermolecular forces except during collisions, negligible molecular volume.
- Pressure arises from molecular collisions with the wall.
- **Temperature is a measure of average translational KE** of the molecules: `⟨K⟩ = (3/2) k T`, independent of the gas.
- Molecular speeds follow the **Maxwell distribution**: `v_p < v_avg < v_rms`.
- **Vapour:** a gas below its critical temperature. **Saturated vapour** is in dynamic equilibrium with its liquid; its pressure depends on temperature only.
- **Boiling** occurs when the saturated vapour pressure equals the external pressure.
- **Dew point:** temperature at which air becomes saturated. **Relative humidity** = actual vapour pressure / SVP at air temperature.
- **Triple point:** the unique T, p where solid, liquid and gas coexist.
- **Brownian motion** (random jiggling of pollen grains) is direct evidence of molecular motion.

**Formulas**

```
Pressure:                   p = (1/3) ρ v_rms²  = (1/3)(N/V) m v_rms²
RMS speed:                  v_rms = √(3RT/M) = √(3kT/m) = √(3p/ρ)
Average speed:              v_avg = √(8RT/πM)
Most probable speed:        v_p = √(2RT/M)
                            v_p : v_avg : v_rms = 1 : 1.128 : 1.224
Mean KE per molecule:       (3/2) k T      Per mole: (3/2) R T
Internal energy (ideal):    depends on T only
Relative humidity:          RH = (actual vapour pressure / SVP at air temperature) × 100 %
                               = (SVP at dew point) / (SVP at air temperature)
Mean free path:             λ = 1 / (√2 π d² n)
Graham's law (effusion):    rate ∝ 1/√M   (lighter gases effuse faster)
```

**Worked example — rms speed.** Oxygen (`M = 0.032 kg/mol`) at 300 K: `v_rms = √(3×8.314×300/0.032) = 483.6 m/s` (≈ 0.48 km/s).

**Worked example — KE.** At 300 K: `(3/2) × 1.38×10⁻²³ × 300 = 6.2×10⁻²¹ J = 0.039 eV` — the same for every gas.

**Worked example — humidity.** The air is at 20 °C where SVP = 17.5 mm Hg and the actual vapour pressure is 12 mm Hg: `RH = 12/17.5 = 68.6 %`. The dew point is the temperature where SVP = 12 mm Hg (≈ 14 °C).

**Worked example — H₂ vs O₂.** At the same T, `v_rms(H₂)/v_rms(O₂) = √(32/2) = 4`.

---

## Chapter 25 — Calorimetry

**Key points**
- **Heat** is energy in transit due to a temperature difference. Unit: joule (1 cal = 4.18 J ≈ 4.2 J).
- **Principle of calorimetry:** in an isolated system, heat lost by hot bodies = heat gained by cold bodies.
- **Specific heat capacity** `s`: heat per unit mass per degree. **Molar** `C = M s`.
- **Latent heat** is heat absorbed/released during a phase change **without temperature change**.
- Water: `s = 4186 J/kg·K ≈ 1 cal/g·°C`; ice `≈ 2100`; steam `≈ 2000`. `L_fusion = 3.36×10⁵ J/kg` (80 cal/g); `L_vap = 2.26×10⁶ J/kg` (540 cal/g).
- **Joule's experiment** established the mechanical equivalent of heat: `W = JQ`, `J = 4.18 J/cal`.

**Formulas**

```
Heat for temperature change:   Q = m s ΔT = n C ΔT
Phase change:                  Q = m L
Calorimetry:                   Σ (heat lost) = Σ (heat gained)
Water equivalent:              W = m s   (mass of water that absorbs the same heat)
Mixing (no phase change):      T_f = (m1 s1 T1 + m2 s2 T2)/(m1 s1 + m2 s2)
Heating at power P:            t = Q / P
```

**Worked example — mixing.** 100 g water at 80 °C + 200 g water at 20 °C: `T_f = (100×80 + 200×20)/300 = 40 °C`.

**Worked example — ice.** 100 g ice at 0 °C into 200 g water at 40 °C (`s = 4.2 J/g°C`, `L = 336 J/g`):
Heat to melt all the ice `= 100×336 = 33 600 J`; heat available cooling the water to 0 °C `= 200×4.2×40 = 33 600 J`. These are exactly equal, so the final result is **0 °C, with all ice just melted**.

**Worked example — kettle.** Heat 1 kg water by 80 °C with a 1 kW heater: `Q = 4186×80 = 3.35×10⁵ J` → `t = 335 s ≈ 5.6 min`.

**Worked example — equivalent.** 100 g of ice at 0 °C dropped into 400 g of water at 50 °C: heat available `= 400×4.2×50 = 84 000 J`; melting needs 33 600 J, leaving `50 400 J` to warm 500 g of water: `ΔT = 50 400/(500×4.2) = 24 °C`. Final T = **24 °C**.

---

## Chapter 26 — Laws of Thermodynamics

**Key points**
- **First law:** `ΔQ = ΔU + ΔW` — energy conservation (heat added = increase in internal energy + work done *by* the gas).
- **Sign convention:** `Q > 0` heat given *to* the system; `W > 0` work done *by* the system.
- Work done by a gas = **area under the p–V curve**. Cyclic process: `ΔU = 0`, so `Q = W`.
- Standard processes: isothermal (`T` const), isochoric (`V` const, `W = 0`), isobaric (`p` const), adiabatic (`Q = 0`).
- **Second law (Kelvin–Planck):** no engine can convert heat entirely into work in a cycle. **(Clausius):** heat does not flow spontaneously from cold to hot.
- **Reversible** processes are idealised (quasi-static, no friction). Real processes are irreversible and increase **entropy**.
- **Carnot engine** has the maximum efficiency between two temperatures; it depends only on the two temperatures.

**Formulas**

```
First law:                   ΔQ = ΔU + ΔW
Work by gas:                 W = ∫ p dV
   Isobaric:                 W = p (V2 − V1)
   Isothermal (ideal gas):   W = n R T ln(V2/V1) = n R T ln(p1/p2)
   Isochoric:                W = 0
Internal energy (ideal):     ΔU = n Cv ΔT
Heat engine efficiency:      η = W/Q_in = 1 − Q_out/Q_in
Carnot engine:               η = 1 − T_c/T_h   (Kelvin temperatures)
                             Q_c/Q_h = T_c/T_h
Refrigerator (COP):          COP = Q_c/W = T_c/(T_h − T_c) (Carnot)
Entropy change:              ΔS = ∫ dQ/T   (reversible)
   Phase change:             ΔS = m L / T
   Heating (const s):        ΔS = m s ln(T2/T1)
```

**Worked example — isothermal.** 1 mol ideal gas at 300 K doubles its volume: `W = 8.314×300×ln 2 = 1729 J`; `ΔU = 0` so `Q = 1729 J` (all heat becomes work).

**Worked example — Carnot.** Source 500 K, sink 300 K: `η = 1 − 300/500 = 40 %`. If it takes in 1000 J, work out = 400 J, heat rejected = 600 J.

**Worked example — entropy.** 1 kg of ice melting at 273 K: `ΔS = 3.36×10⁵/273 = 1231 J/K`.

**Worked example — cycle.** A rectangular cycle on a p–V diagram, `Δp = 2×10⁵ Pa`, `ΔV = 1×10⁻³ m³`: `W_net = area = 2×10⁵ × 1×10⁻³ = 200 J`.

**Worked example — refrigerator.** Freezer at 260 K in a 300 K room: `COP = 260/(300 − 260) = 6.5`.

---

## Chapter 27 — Specific Heat Capacities of Gases

**Key points**
- A gas has two principal molar specific heats: `Cv` (constant volume) and `Cp` (constant pressure); `Cp > Cv` because at constant pressure some heat goes into expansion work.
- **Mayer's relation:** `Cp − Cv = R`.
- `γ = Cp/Cv` depends on molecular structure.
- **Equipartition of energy:** each *quadratic* degree of freedom carries `½ kT` per molecule (`½ RT` per mole).
- **Isothermal** (slow, heat exchange): `pV = const`. **Adiabatic** (no heat exchange): `pV^γ = const`.
- An adiabatic curve is steeper than an isotherm on a p–V diagram.
- In an adiabatic expansion the gas does work at the expense of its internal energy, so it **cools**; in a *free* expansion into vacuum an ideal gas does no work and its temperature stays the same.

**Degrees of freedom and heat capacities**

| Gas | f | Cv | Cp | γ |
|---|---|---|---|---|
| Monatomic (He, Ne, Ar) | 3 | 3R/2 | 5R/2 | 5/3 ≈ 1.67 |
| Diatomic (rigid; O₂, N₂) | 5 | 5R/2 | 7R/2 | 7/5 = 1.40 |
| Polyatomic (nonlinear) | 6 | 3R | 4R | 4/3 ≈ 1.33 |

**Formulas**

```
Mayer's relation:             Cp − Cv = R
Gamma:                        γ = Cp/Cv = 1 + 2/f
Cv = f R/2 ;   Cp = (f/2 + 1) R
Internal energy:              U = n (f/2) R T = n Cv T
Isothermal:                   p V = constant
Adiabatic:                    p V^γ = constant ;  T V^(γ−1) = constant ;  p^(1−γ) T^γ = constant
Work in adiabatic process:    W = (p1V1 − p2V2)/(γ − 1) = n R (T1 − T2)/(γ − 1)
Speed of sound in a gas:      v = √(γ p / ρ)
```

**Worked example — heat added at constant pressure.** 1 mol of monatomic gas heated by 10 K:
at constant V: `Q = Cv ΔT = 1.5×8.314×10 = 124.7 J` (= ΔU);
at constant p: `Q = Cp ΔT = 2.5×8.314×10 = 207.9 J`.
Difference `= 83.1 J = RΔT` = the work done at constant pressure ✓.

**Worked example — adiabatic compression.** Diatomic gas (`γ = 1.4`) at 300 K compressed to half its volume: `T2 = 300 × 2^0.4 = 395.9 K`; work done on the gas `= nR(T2 − T1)/(γ − 1) = 8.314×95.9/0.4 = 1992 J` (for 1 mol).

**Worked example — γ from degrees of freedom.** Diatomic: `γ = 1 + 2/5 = 1.4` ✓.

---

## Chapter 28 — Heat Transfer

**Key points**
- Three modes: **conduction** (through matter, no bulk motion), **convection** (bulk fluid motion), **radiation** (EM waves, needs no medium).
- Conduction in steady state: rate of heat flow ∝ area × temperature gradient.
- **Thermal resistance** adds in series; conductance adds in parallel — a direct analogue of Ohm's law.
- **Blackbody:** perfect absorber and emitter. **Kirchhoff's law:** good absorbers are good emitters.
- **Stefan–Boltzmann law:** power radiated ∝ T⁴. **Wien's displacement law:** peak wavelength ∝ 1/T.
- **Newton's law of cooling:** rate of cooling ∝ temperature difference (for small differences).
- **Prevost's theory of exchange:** every body radiates and absorbs; net flow is from hot to cold.

**Formulas**

```
Conduction:                    dQ/dt = K A (T1 − T2)/L          (K = thermal conductivity)
Thermal resistance:            R = L/(K A) ;  dQ/dt = ΔT/R
   Series:                     R = R1 + R2 + ...
   Parallel:                   1/R = 1/R1 + 1/R2 + ...
Stefan–Boltzmann:              P = e σ A T⁴         (σ = 5.67×10⁻⁸ W/m²K⁴, e = emissivity)
   Net radiation:              P_net = e σ A (T⁴ − T0⁴)
Wien's displacement law:       λ_max T = b = 2.898×10⁻³ m·K
Newton's law of cooling:       dT/dt = −k (T − T0)
   Solution:                   T − T0 = (T_i − T0) e^(−kt)
   (for small ΔT):             (T1 − T2)/t = k [ (T1+T2)/2 − T0 ]
Heat to melt via conduction:   mL = K A ΔT t / d
```

**Worked example — series rods.** Two rods in series, each `A = 1 m²` and `L = 1 m`, with `K1 = 1` and `K2 = 8 W/m·K`, between 100 °C and 0 °C:
`R = 1/1 + 1/8 = 1.125 K/W` ; `Q = 100/1.125 = 88.9 W` ; the junction temperature is `100 − 88.9 × 1 = 11.1 °C` (the poor conductor takes most of the temperature drop).

**Worked example — Wien.** The Sun's surface at ≈ 5800 K peaks at `λ = 2.898×10⁻³/5800 = 500 nm` (green).

**Worked example — Stefan.** A blackbody (`e = 1`) of area 1 m² at 1000 K radiates `5.67×10⁻⁸ × 10¹² = 5.67×10⁴ W`. Doubling T multiplies power by 16.

**Worked example — Newton's cooling.** Water cools from 80 °C to 60 °C in 10 min in a 20 °C room, ΔT: 60 → 40. `ln(60/40) = k×10 → k = 0.0405 /min`. Time to cool from 60 °C to 40 °C (ΔT 40 → 20): `t = ln(2)/0.0405 = 17.1 min`.

---

# PART B — ELECTROSTATICS

## Chapter 29 — Electric Field and Potential

**Key points**
- **Charge** is quantised (`e = 1.6×10⁻¹⁹ C`), conserved, and of two kinds.
- **Coulomb's law:** force between point charges ∝ `q₁q₂/r²`.
- **Electric field** `E = F/q₀` is the force per unit positive test charge; field lines start on + and end on −, never cross; crowded lines → strong field.
- **Potential** `V` is work per unit charge to bring it from infinity; scalar; `E = −dV/dx`.
- **Dipole:** two equal and opposite charges; dipole moment `p = q d` (from − to +). In a field it experiences a torque `τ = p × E`.
- **Conductors:** field inside is zero; charges sit on the surface; the surface is an equipotential.

**Formulas**

```
Coulomb's law:                  F = (1/4πε0) q1 q2 / r²    1/4πε0 = 9×10⁹ N·m²/C²
Electric field (point charge):  E = (1/4πε0) q / r²
Potential (point charge):       V = (1/4πε0) q / r
Potential energy of 2 charges:  U = (1/4πε0) q1 q2 / r
Field–potential relation:       E = −dV/dr ;   V = −∫ E·dr
Work in moving a charge:        W = q (V_B − V_A)
Electron/proton in a field:     F = qE ;  a = qE/m
Dipole:  axial field            E = (1/4πε0) 2p/r³   (far from the dipole)
         equatorial field       E = (1/4πε0) p/r³
         potential (axial)      V = (1/4πε0) p cosθ / r²
         torque                 τ = p E sinθ
         potential energy       U = −p·E = −p E cosθ
Charged ring on axis:           E = k Q x/(R² + x²)^(3/2)
```

**Worked example — Coulomb field.** A `2 μC` charge at 30 cm: `E = 9×10⁹ × 2×10⁻⁶/0.09 = 2.0×10⁵ N/C`.

**Worked example — potential.** At 30 cm from the same charge: `V = 9×10⁹ × 2×10⁻⁶/0.3 = 6.0×10⁴ V`.

**Worked example — electron accelerated.** From rest through 100 V: `½mv² = eV` → `v = √(2×1.6×10⁻¹⁹×100/9.1×10⁻³¹) = 5.9×10⁶ m/s`.

**Worked example — dipole.** `p = 2×10⁻⁸ C·m` in `E = 5×10⁴ N/C` at 30°: `τ = pE sin30° = 2×10⁻⁸ × 5×10⁴ × 0.5 = 5×10⁻⁴ N·m`.

---

## Chapter 30 — Gauss's Law

**Key points**
- **Electric flux** `Φ = ∮E·dA` — the number of field lines through a surface.
- **Gauss's law:** total flux through any *closed* surface = `q_enclosed/ε0`. It is another form of Coulomb's law and is most useful when symmetry lets `E` come out of the integral (spherical, cylindrical, planar).
- Only the enclosed charge contributes to the total flux, but all charges contribute to `E` at a point.
- **Solid angle** (in steradian) is the 3-D analogue of angle; the full sphere subtends `4π` sr.

**Formulas**

```
Flux:                          Φ = ∮ E·dA = q_enc / ε0
Point charge:                  E = q/(4πε0 r²)
Infinite line (λ per length):  E = λ/(2πε0 r)
Infinite sheet (σ per area):   E = σ/(2ε0)          (non-conducting sheet)
Conducting surface:            E = σ/ε0             (just outside)
Parallel plates (opposite):    E = σ/ε0 between, 0 outside
Uniformly charged sphere (R, total Q):
   outside  (r ≥ R):           E = Q/(4πε0 r²)
   inside   (r < R):           E = Q r/(4πε0 R³)
Thin spherical shell:          E = 0 inside ;  E = Q/(4πε0 r²) outside
Solid angle:                   Ω = A / r²    ( sphere = 4π sr)
```

**Worked example — line charge.** `λ = 2 nC/m` at `r = 0.5 m`: `E = 2×9×10⁹ × 2×10⁻⁹/0.5 = 72 N/C` (using `1/(2πε0) = 18×10⁹`).

**Worked example — sheet.** `σ = 1 μC/m²`: `E = 10⁻⁶/(2×8.85×10⁻¹²) = 5.6×10⁴ N/C`.

**Worked example — flux.** A charge of `8.85 nC` inside a closed surface: `Φ = 8.85×10⁻⁹/8.85×10⁻¹² = 1000 N·m²/C`.

**Worked example — shell.** A conducting shell of radius 10 cm carrying `+10 nC`: outside at 20 cm, `E = 9×10⁹×10⁻⁸/0.04 = 2250 N/C`; inside, `E = 0`.

---

## Chapter 31 — Capacitors

**Key points**
- A **capacitor** stores charge and energy; `C = Q/V` depends only on geometry (and the dielectric), not on `Q` or `V`.
- **Parallel-plate:** `C = ε0 A/d`. Inserting a **dielectric** multiplies capacitance by `K` (and the field/voltage across it drops by `K` at fixed charge).
- **Series:** same charge, voltages divide; capacitance falls. **Parallel:** same voltage, capacitances add.
- Energy is stored *in the electric field*: `u = ½ ε0 E²` per unit volume.
- Connecting a charged capacitor to an uncharged one conserves **charge** (not energy); some energy is lost as heat/radiation.
- **Corona discharge** occurs at sharp points where the field is very high. A **Van de Graaff** generator reaches high voltage by transferring charge to the inside of a hollow conductor.

**Formulas**

```
Definition:                  C = Q/V
Parallel plate:              C = ε0 A / d ;   with dielectric C = K ε0 A / d
Spherical conductor:         C = 4πε0 R
Concentric spheres:          C = 4πε0 ab/(b − a)
Cylindrical:                 C = 2πε0 L / ln(b/a)
Series:                      1/C = 1/C1 + 1/C2 + ... ;  charge same
Parallel:                    C = C1 + C2 + ... ;  voltage same
Energy stored:               U = ½ C V² = ½ Q V = Q²/2C
Energy density:              u = ½ ε0 E²  (vacuum), ½ K ε0 E² (dielectric)
Force between plates:        F = Q²/(2 ε0 A) = ½ ε0 E² A
Sharing charge (two caps):   V_common = (Q1 + Q2)/(C1 + C2)
Energy lost on sharing:      ΔU = C1C2 (V1 − V2)² / 2(C1 + C2)
Dielectric slab, thickness t, in plate gap d:  C = ε0 A/(d − t + t/K)
```

**Worked example — parallel plates.** `A = 0.01 m²`, `d = 1 mm`: `C = 8.854×10⁻¹² × 0.01/10⁻³ = 8.85×10⁻¹¹ F = 88.5 pF`.

**Worked example — combinations.** `2 μF` and `3 μF`: in series `C = 6/5 = 1.2 μF`; in parallel `C = 5 μF`.

**Worked example — energy.** `C = 10 μF` at 100 V: `U = ½×10⁻⁵×10⁴ = 0.05 J`.

**Worked example — sharing.** `C1 = 4 μF` charged to `100 V` joined to an uncharged `C2 = 1 μF`: common `V = (400 μC)/(5 μF) = 80 V`; energy before `= 0.02 J`, after `= ½×5×10⁻⁶×6400 = 0.016 J`; lost `0.004 J`; formula: `4×1×10⁻¹² × 10⁴/(2×5×10⁻⁶) = 4×10⁻³ J` ✓.

**Worked example — dielectric.** Inserting a `K = 4` dielectric (battery connected, V fixed) multiplies `C` by 4 and the stored energy by 4; if the battery is disconnected (Q fixed), the voltage falls to a quarter and the energy to a quarter.

---

# PART C — CURRENT ELECTRICITY

## Chapter 32 — Electric Current in Conductors

**Key points**
- **Current** `I = dq/dt` (ampere); **current density** `J = I/A`.
- **Drift speed** of electrons is tiny (mm/s) even though the signal travels at near light speed because the field is established throughout the wire at once.
- **Ohm's law:** `V = IR`. **Resistivity** depends on the material and temperature, not geometry.
- **EMF** is the work done per unit charge by a source; terminal voltage `V = ε − Ir` when delivering current.
- **Kirchhoff's laws:** (1) junction rule — algebraic sum of currents at a node is zero (charge conservation); (2) loop rule — algebraic sum of potential differences around any loop is zero (energy conservation).
- **Wheatstone bridge** balances when `P/Q = R/S`. **Potentiometer** measures EMF with no current drawn.
- **Ammeter** = galvanometer + low shunt in parallel; **voltmeter** = galvanometer + high resistance in series.
- Discharging/charging an RC circuit is exponential, with time constant `τ = RC`.

**Formulas**

```
Current:                  I = dq/dt = n e A v_d
Drift speed:              v_d = I /(n e A)
Ohm's law:                V = I R
Resistance:               R = ρ L / A ;   conductivity σ = 1/ρ
Temperature dependence:   R_T = R_0 [1 + α (T − T0)]
Combinations:             Series  R = R1 + R2 ... ;  Parallel 1/R = 1/R1 + 1/R2 ...
EMF & terminal voltage:   V = ε − I r   (discharging) ; V = ε + I r (charging)
Power:                    P = V I = I² R = V²/R
Max power transfer:       when R_load = r (internal resistance), P_max = ε²/4r
Batteries:  n in series   ε_eq = nε , r_eq = n r
            m in parallel ε_eq = ε , r_eq = r/m
Wheatstone bridge:        P/Q = R/S
Shunt:                    S = I_g G /(I − I_g)       (galvanometer resistance G)
Series multiplier:        R = V/I_g − G
Potentiometer:            ε1/ε2 = l1/l2
RC charging:              q = Q0 (1 − e^(−t/RC)) ;  discharging q = Q0 e^(−t/RC)
```

**Worked example — drift speed.** 1 A in a copper wire of cross-section `1 mm²` (`n = 8.5×10²⁸ m⁻³`): `v_d = 1/(8.5×10²⁸ × 1.6×10⁻¹⁹ × 10⁻⁶) = 7.3×10⁻⁵ m/s = 0.073 mm/s`.

**Worked example — resistance.** Copper (`ρ = 1.7×10⁻⁸ Ω·m`), 10 m long, `1 mm²`: `R = 1.7×10⁻⁸ × 10/10⁻⁶ = 0.17 Ω`.

**Worked example — terminal voltage.** `ε = 12 V`, `r = 1 Ω`, load `5 Ω`: `I = 12/6 = 2 A`; terminal `V = 12 − 2×1 = 10 V`.

**Worked example — max power.** With `ε = 12 V`, `r = 1 Ω`, set `R = 1 Ω`: `I = 6 A`, `P = 36 W` (= 144/4).

**Worked example — Wheatstone.** `P = 10`, `Q = 20`, `R = 30` Ω → balanced `S = QR/P = 20×30/10 = 60 Ω`.

**Worked example — shunt.** Galvanometer `G = 100 Ω`, full scale `I_g = 1 mA`, make a `1 A` ammeter: `S = 0.001×100/0.999 = 0.1001 Ω`.

**Worked example — voltmeter.** Same galvanometer to read 10 V full scale: `R = 10/0.001 − 100 = 9900 Ω` in series.

---

## Chapter 33 — Thermal and Chemical Effects of Electric Current

**Key points**
- **Joule heating:** `H = I² R t` (also `V I t`, `V² t / R`). Heating is the basis of heaters, fuses and filament lamps.
- **Thermoelectric effects:** **Seebeck** (two metals with junctions at different temperatures produce an EMF), **Peltier** (current causes heating/cooling at a junction — reversible), **Thomson** (heating/cooling along a conductor with a temperature gradient).
- **Electrolysis:** passing current through an electrolyte decomposes it.
- **Faraday's laws:** (1) mass deposited `∝` charge passed; (2) for the same charge, masses deposited `∝` chemical equivalents (`atomic mass / valency`).
- A **voltameter/coulombmeter** measures charge through the mass deposited.
- **Primary cells** cannot be recharged (Daniell, Leclanché, dry cell); **secondary** cells can (lead–acid accumulator).

**Formulas**

```
Joule's law:             H = I² R t = V I t = (V²/R) t         (in joules ; ÷4.18 for calories)
Fuse / heater power:     P = V²/R
Thermoelectric EMF:      ε = a T + ½ b T²   (T = temperature difference)
Faraday's 1st law:       m = Z q = Z I t         (Z = electrochemical equivalent)
Faraday's 2nd law:       Z = E / F , where E = M/n (equivalent weight), F = 96 485 C/mol
Combined:                m = (M / n F) · I t
Cell efficiency etc.:    η = useful energy / total energy
```

**Worked example — heater.** A 1 kW immersion heater runs 5 minutes: `H = 1000×300 = 3×10⁵ J = 72 000 cal`.

**Worked example — electrolysis of copper.** 2 A for 1 hour deposits Cu (`M = 63.5`, `n = 2`): `m = (63.5/(2×96 485)) × (2 × 3600) = 2.37 g` (charge = 7200 C).

**Worked example — power.** A 220 V bulb rated 100 W has `R = 220²/100 = 484 Ω`; at 110 V it draws `110²/484 = 25 W`.

**Worked example — second law.** The same charge through silver nitrate (`M = 108`, `n = 1`) and copper sulphate (`M = 63.5`, `n = 2`): masses are in the ratio of equivalent weights, `108 : 31.75 = 3.4 : 1`. So the same 7200 C that deposits 2.37 g of copper deposits `7200 × 108/96 485 = 8.06 g` of silver (ratio 3.4 ✓).

---

# PART D — MAGNETISM

## Chapter 34 — Magnetic Field

**Key points**
- A **moving charge** (or a current) experiences a force in a magnetic field; the force is perpendicular to both velocity and `B`, so it does **no work** and changes only the direction of motion.
- Direction: right-hand rule (positive charge); reverse for negative charge.
- Unit: tesla (T) = N/(A·m). `1 gauss = 10⁻⁴ T`.
- A charged particle in a uniform `B` follows a **circle** (if `v ⟂ B`) or a **helix** (if oblique). Period is independent of speed.
- A current loop has a **magnetic moment** `μ = N I A` and experiences a torque in a field (the principle of the motor and the moving-coil meter).
- With both `E` and `B`, a **velocity selector** passes particles with `v = E/B`.

**Formulas**

```
Lorentz force:             F = q (E + v × B)
Magnetic force:            F = q v B sinθ
On a current element:      F = I L × B  → F = B I L sinθ
Circular motion (v ⟂ B):   r = m v/(q B) = √(2 m K)/(q B) ;  T = 2π m/(q B) ; f = qB/(2π m)
Helix (angle θ to B):      pitch = (2π m/qB) v cosθ ;  radius = m v sinθ/(q B)
Velocity selector:         q E = q v B → v = E/B
Magnetic moment:           μ = N I A  (direction by right-hand rule)
Torque on a loop:          τ = μ × B → τ = N I A B sinθ
Potential energy:          U = −μ·B
Cyclotron:                 f = qB/(2π m) ; K_max = q² B² R²/(2m)
Hall voltage:              V_H = B I /(n e t)
```

**Worked example — proton circle.** A proton at `10⁶ m/s` in `B = 0.1 T`: `r = 1.67×10⁻²⁷×10⁶/(1.6×10⁻¹⁹×0.1) = 0.104 m`; period `T = 2π m/(qB) = 6.6×10⁻⁷ s`.

**Worked example — cyclotron.** In `B = 1 T`, protons circulate at `f = 1.6×10⁻¹⁹×1/(2π×1.67×10⁻²⁷) = 15.2 MHz`.

**Worked example — force on a wire.** 2 A in a 0.5 m wire ⟂ to `B = 0.2 T`: `F = 0.2×2×0.5 = 0.2 N`.

**Worked example — coil torque.** 100 turns, 0.01 m² area, 1 A in `B = 0.5 T`, plane ∥ field (θ = 90° to the normal): `τ = 100×1×0.01×0.5 = 0.5 N·m`.

**Worked example — velocity selector.** `E = 10⁴ V/m`, `B = 0.1 T` selects `v = 10⁵ m/s`.

---

## Chapter 35 — Magnetic Field due to a Current

**Key points**
- **Biot–Savart law** gives the field from a current element. **Ampere's law** is used for symmetric currents (long wire, solenoid, toroid).
- A long straight wire's field circles it (right-hand grip rule) and falls as `1/r`.
- Parallel currents **attract**; antiparallel currents **repel**. This defines the ampere.
- A circular loop gives field `μ0 I/2R` at its centre; a **solenoid** gives a uniform interior field `μ0 n I` and almost zero outside.
- A **toroid** confines the field inside its windings.

**Formulas**

```
Biot–Savart:                dB = (μ0/4π) I dl sinθ / r²      μ0/4π = 10⁻⁷ T·m/A
Infinite straight wire:     B = μ0 I /(2π r)
Finite wire (angles α,β):   B = (μ0 I /4π d)(sinα + sinβ)
Circular loop centre:       B = μ0 N I /(2 R)
Loop on axis (distance x):  B = μ0 N I R² /[2 (R² + x²)^(3/2)]
Arc (angle θ) at centre:    B = μ0 I θ /(4π R)
Ampere's law:               ∮ B·dl = μ0 I_enclosed
Solenoid (n turns/length):  B = μ0 n I   (long, inside) ;  ends ≈ μ0 n I/2
Toroid:                     B = μ0 N I /(2π r)
Force between parallel wires (per unit length):  F/L = μ0 I1 I2 /(2π d)
Moving charge:              B = (μ0/4π) q v sinθ / r²
```

**Worked example — straight wire.** 10 A at `5 cm`: `B = 2×10⁻⁷×10/0.05 = 4×10⁻⁵ T` (comparable to Earth's field).

**Worked example — loop.** 5 A in a circular loop of radius `0.1 m` (N = 1): `B = 4π×10⁻⁷×5/(2×0.1) = 3.14×10⁻⁵ T`.

**Worked example — solenoid.** 1000 turns/m, 2 A: `B = 4π×10⁻⁷×1000×2 = 2.5×10⁻³ T`.

**Worked example — parallel wires.** 10 A each, 1 m apart: `F/L = 2×10⁻⁷×100/1 = 2×10⁻⁵ N/m` (attractive).

**Worked example — Ampere's law.** Inside a long wire of radius `R` with uniform current: `B(r) = μ0 I r/(2π R²)` rising linearly from zero at the axis to `μ0 I/2πR` at the surface.

---

## Chapter 36 — Permanent Magnets

**Key points**
- Magnets have two poles that can never be isolated; field lines form closed loops (no monopoles).
- A bar magnet behaves like a **current loop/solenoid**; its field at far points is like that of a dipole.
- **Earth's magnetism:** the field is described by three elements — declination, **dip** (inclination) and horizontal component `B_H`; at a *neutral point* the magnet's field cancels the horizontal field of Earth.
- A magnet in a uniform field feels a **torque** (no net force) and oscillates; the period depends on `B`.
- **Tangent galvanometer** and **moving-coil galvanometer** measure current; shunts extend the range.
- **Gauss's law for magnetism:** net magnetic flux through any closed surface is zero.
- **Tangent law:** a magnet in two perpendicular fields rests at `tanθ = B2/B1`.

**Formulas**

```
Dipole moment of a magnet:   M = m (pole strength) × 2l ;  unit A·m²
Axial field of magnet:       B = (μ0/4π) 2M / d³           (end-on)
Equatorial field:            B = (μ0/4π) M / d³            (broadside)
Torque in a field:           τ = M B sinθ ;  U = −M·B
Oscillation period:          T = 2π √(I /(M B))
Earth's field components:    B_H = B cosδ ; B_V = B sinδ ; tanδ = B_V/B_H
Tangent galvanometer:        B_H tanθ = μ0 n I /(2 r) → I = (2 r B_H /μ0 n) tanθ
Moving-coil galvanometer:    N I A B = k φ  → I = (k /NAB) φ
Gauss for magnetism:         ∮ B·dA = 0
```

**Worked example — bar magnet.** `M = 2 A·m²`: at 0.3 m on the axis, `B = 10⁻⁷×2×2/0.027 = 1.48×10⁻⁵ T`; on the equatorial line `7.4×10⁻⁶ T` (half as much).

**Worked example — tangent galvanometer.** `B_H = 3.6×10⁻⁵ T`, one turn of radius `0.1 m`, deflection `45°`: `I = 2×0.1×3.6×10⁻⁵/(4π×10⁻⁷) = 0.573 A`.

**Worked example — dip.** `B_H = 0.3 G`, `B_V = 0.3 G` → `tanδ = 1`, `δ = 45°`.

**Worked example — oscillation.** Doubling `B` reduces the period by `1/√2`.

---

## Chapter 37 — Magnetic Properties of Matter

**Key points**
- Materials respond to a magnetic field through **magnetisation** `I` (dipole moment per unit volume).
- **Diamagnetic** — weakly repelled, `χ` small and negative, independent of T (bismuth, copper, water).
- **Paramagnetic** — weakly attracted, `χ` small positive, decreases with T (**Curie's law**, `χ ∝ 1/T`) (aluminium, oxygen).
- **Ferromagnetic** — strongly attracted, `χ` large and positive, shows **hysteresis** and a **Curie temperature** above which it becomes paramagnetic (iron, cobalt, nickel).
- **Hysteresis loop:** shows retentivity and coercivity. **Soft iron** (narrow loop, low loss) for transformers/electromagnets; **steel** (wide loop) for permanent magnets.
- Relations among `B`, `H`, `I`, `χ`, `μ_r` are listed below.

**Formulas**

```
Magnetisation:         I = M_total / V
Magnetic intensity:    H = B/μ0 − I   → B = μ0 (H + I)
Susceptibility:        χ = I / H
Relative permeability: μ_r = 1 + χ ;   μ = μ0 μ_r ;  B = μ H
Curie's law:           χ = C / T
Curie–Weiss law:       χ = C /(T − T_c)   (above T_c)
Energy loss per cycle: area of B–H loop (per unit volume)
```

**Worked example.** Iron with `μ_r = 5000` in a solenoid of `n = 1000 /m`, `I = 0.5 A`: `H = nI = 500 A/m`; `B = μ0 μ_r H = 4π×10⁻⁷×5000×500 = 3.14 T`.

**Worked example — Curie's law.** A paramagnetic salt has `χ = 2×10⁻³` at 300 K; at 150 K, `χ = 4×10⁻³`.

**Worked example — which material for what.** Transformer core → soft iron (small hysteresis loss). Compass needle → steel (retains magnetism).

---

# PART E — INDUCTION, AC, EM WAVES

## Chapter 38 — Electromagnetic Induction

**Key points**
- **Faraday's law:** a changing magnetic flux through a circuit induces an EMF equal to the rate of change of flux.
- **Lenz's law:** the induced current opposes the change that produced it (energy conservation; gives the minus sign).
- **Motional EMF:** a conductor of length `l` moving at `v` across `B` has `ε = B l v`.
- **Eddy currents:** circulating currents induced in bulk conductors — used in induction furnaces and magnetic braking, and a source of loss in transformer cores (laminations reduce it).
- **Self-inductance** `L`: EMF induced in a coil by its own changing current. **Mutual inductance** `M`: EMF induced in one coil by the other.
- In an **LR circuit**, the current grows/decays exponentially with time constant `τ = L/R`.
- A coil stores energy in its magnetic field.

**Formulas**

```
Flux:                   Φ = ∫ B·dA = B A cosθ
Faraday's law:          ε = −N dΦ/dt
Motional EMF:           ε = B l v ;   rotating rod: ε = ½ B ω l²
Rotating coil:          ε = N B A ω sin(ωt)
Self-inductance:        ε = −L dI/dt ;   L = N Φ / I
Solenoid:               L = μ0 n² A l = μ0 N² A / l
Mutual inductance:      ε2 = −M dI1/dt ;  M = N2 Φ2 / I1
LR growth:              I = I0 (1 − e^(−Rt/L)) ,  τ = L/R
LR decay:               I = I0 e^(−Rt/L)
Energy in inductor:     U = ½ L I²   ;  energy density u = B²/(2 μ0)
Inductors in series:    L = L1 + L2 (no coupling) ; parallel 1/L = 1/L1 + 1/L2
```

**Worked example — Faraday.** A coil of 100 turns, flux changing by 0.01 Wb in 0.2 s: `ε = 100×0.01/0.2 = 5 V`.

**Worked example — motional EMF.** A rod 0.5 m moving at 4 m/s in `B = 0.2 T`: `ε = 0.2×0.5×4 = 0.4 V`.

**Worked example — rotating rod.** A 1 m rod rotating at `ω = 10 rad/s` in `B = 0.1 T`: `ε = ½×0.1×10×1 = 0.5 V`.

**Worked example — solenoid inductance.** `n = 1000 /m`, `A = 10⁻⁴ m²`, `l = 0.5 m`: `L = 4π×10⁻⁷ × 10⁶ × 10⁻⁴ × 0.5 = 6.3×10⁻⁵ H`.

**Worked example — LR circuit.** `L = 1 H`, `R = 10 Ω`: `τ = 0.1 s`; at `t = 0.1 s`, current is `63 %` of the final value.

**Worked example — energy.** `L = 2 H`, `I = 3 A`: `U = ½×2×9 = 9 J`.

---

## Chapter 39 — Alternating Current

**Key points**
- AC varies sinusoidally: `I = I0 sin ωt`. The **RMS** value is the DC equivalent for heating: `I_rms = I0/√2`.
- **Phase:** in a resistor, `V` and `I` are in phase; in an inductor, `V` leads `I` by 90°; in a capacitor, `V` lags `I` by 90° (**"CIVIL"**: in C, I leads V; in L, V leads I).
- **Reactance** opposes AC: `X_L = ωL` (grows with frequency); `X_C = 1/ωC` (falls with frequency).
- In a series **LCR** circuit the **impedance** `Z = √(R² + (X_L − X_C)²)`; resonance occurs at `X_L = X_C`, when the current is maximum.
- **Power** in AC depends on the phase: only the resistive part dissipates energy. A pure L or C absorbs no net power (**wattless current**).
- **Transformer:** step-up/step-down by turns ratio (ideally power in = power out).
- **DC motor** and **dynamo** are the reverse/forward energy conversions.

**Formulas**

```
Instantaneous:           V = V0 sin ωt ,  I = I0 sin(ωt − φ)
RMS values:              V_rms = V0/√2 ≈ 0.707 V0 ;  I_rms = I0/√2
Reactance:               X_L = ωL = 2π f L ;   X_C = 1/(ωC) = 1/(2π f C)
Impedance (series LCR):  Z = √[R² + (X_L − X_C)²]
Phase:                   tanφ = (X_L − X_C)/R
Resonance:               ω0 = 1/√(LC) ,   f0 = 1/(2π√(LC)) ; Z = R
Quality factor:          Q = ω0 L / R = 1/(R) √(L/C) = f0 / bandwidth
Average power:           P = V_rms I_rms cosφ   (cosφ = R/Z = power factor)
Transformer:             V_s/V_p = N_s/N_p = I_p/I_s (ideal)
Efficiency:              η = P_out/P_in
AC generator EMF:        ε = N B A ω sin ωt ;  ε_0 = N B A ω
```

**Worked example — RMS.** The mains of 220 V rms has a peak `V0 = 220×√2 = 311 V`.

**Worked example — series LCR.** `R = 30 Ω`, `X_L = 80 Ω`, `X_C = 40 Ω`: `Z = √(900 + 1600) = 50 Ω`; `cosφ = 30/50 = 0.6`. With 100 V rms, `I = 2 A`, `P = 100×2×0.6 = 120 W` (= `I²R = 4×30` ✓).

**Worked example — resonance.** `L = 1 mH`, `C = 1 μF`: `f0 = 1/(2π√(10⁻⁹)) = 5033 Hz`.

**Worked example — generator.** 100 turns, `A = 0.05 m²`, `B = 0.1 T`, 50 Hz: `ε_0 = 100×0.1×0.05×2π×50 = 157 V`.

**Worked example — transformer.** 220 V in, `N_p = 1000`, `N_s = 100`: `V_s = 22 V`; if the secondary delivers `2 A`, the primary draws `0.2 A` (ideal).

---

## Chapter 40 — Electromagnetic Waves

**Key points**
- **Maxwell's displacement current** `I_d = ε0 dΦ_E/dt` completes Ampere's law so that current is continuous even across a capacitor gap.
- **Maxwell's four equations** (Gauss for E, Gauss for B, Faraday, Ampere–Maxwell) predict transverse electromagnetic waves travelling at `c = 1/√(μ0 ε0)`.
- In an EM wave `E ⟂ B ⟂ direction of propagation`; they are in phase and `E/B = c`.
- Waves carry **energy** (intensity ∝ `E²`) and **momentum** (radiation pressure).
- **Spectrum** (low f → high f): radio, microwave, infrared, visible (red → violet), ultraviolet, X-rays, gamma rays. All travel at `c` in vacuum.

**Formulas**

```
Displacement current:       I_d = ε0 dΦ_E/dt
Speed in vacuum:            c = 1/√(μ0 ε0) = 3×10⁸ m/s
Relation:                   c = E/B = fλ
Energy density:             u = ½ ε0 E² + B²/(2 μ0) = ε0 E² (E and B parts equal)
Intensity:                  I = ½ ε0 c E0² = c ε0 E_rms²   (average)
Poynting vector:            S = E × B / μ0
Momentum of absorbed light: p = U / c ;   radiation pressure = I / c (absorbed), 2I / c (reflected)
In a medium:                v = 1/√(με) = c/n
```

**Worked example — intensity.** An EM wave with `E0 = 300 V/m` (rms ≈ 212 V/m): `I = ½ε0 c E0² = 0.5×8.85×10⁻¹²×3×10⁸×9×10⁴ = 119.5 W/m²`.

**Worked example — B from E.** `B0 = E0/c = 300/3×10⁸ = 10⁻⁶ T`.

**Worked example — radiation pressure.** Sunlight `1370 W/m²` fully absorbed: `P = 1370/3×10⁸ = 4.6×10⁻⁶ Pa` (tiny but real — comet tails).

**Worked example — wavelength.** A 100 MHz FM signal: `λ = c/f = 3×10⁸/10⁸ = 3 m`.

---

# PART F — MODERN PHYSICS

## Chapter 41 — Electric Current through Gases

**Key points**
- Gases are normally insulators; they conduct when **ionised**. At low pressure and high voltage they glow (discharge tube).
- **Cathode rays** (electron streams) travel in straight lines, are deflected by `E` and `B`, and carry negative charge — **Thomson's** measurement of `e/m` discovered the electron.
- **Canal (positive) rays** are positive ions.
- **Thermionic emission:** hot metal surfaces eject electrons (Richardson's law).
- **Diode valve:** one-way conduction (rectifier). **Triode:** grid controls the plate current, giving amplification.
- Valve parameters: plate resistance `r_p`, transconductance `g_m`, amplification factor `μ`, related by `μ = r_p g_m`.

**Formulas**

```
Thomson's e/m:           v = E/B (selector) and r = m v/(e B)  →  e/m = E /(B² r)
Accelerated through V:   v = √(2 (e/m) V)
Specific charge of electron: e/m = 1.76×10¹¹ C/kg
Richardson's law:        J = A T² e^(−W/kT)
Child's (¾ power) law:   I_p = k V_p^(3/2)
Plate resistance:        r_p = (ΔV_p / ΔI_p) at constant grid voltage
Transconductance:        g_m = ΔI_p / ΔV_g at constant plate voltage
Amplification factor:    μ = −ΔV_p / ΔV_g at constant plate current
Relation:                μ = r_p × g_m
Voltage gain (triode):   A_v = −μ R_L /(R_L + r_p)
```

**Worked example — electron speed.** Accelerated through `1000 V`: `v = √(2×1.76×10¹¹×1000) = 1.88×10⁷ m/s` (6 % of `c`).

**Worked example — radius in B.** Same electron in `B = 1 mT`: `r = v/((e/m) B) = 1.88×10⁷/(1.76×10¹¹×10⁻³) = 0.107 m`.

**Worked example — triode.** `r_p = 10 kΩ`, `g_m = 2 mA/V` → `μ = 10×10³ × 2×10⁻³ = 20`.

---

## Chapter 42 — Photoelectric Effect and Wave–Particle Duality

**Key points**
- **Photoelectric effect:** light above a **threshold frequency** ejects electrons from a metal; below threshold, *no* emission however intense.
- **Classical wave theory fails** to explain: the threshold, the instantaneous emission, and the independence of the stopping potential from intensity.
- **Einstein:** light consists of photons with `E = hf`. One photon is absorbed by one electron: `hf = φ + K_max`.
- **Intensity** controls the *number* of photoelectrons (saturation current); **frequency** controls their maximum KE (stopping potential).
- **De Broglie:** matter has a wavelength `λ = h/p`. Electron diffraction (Davisson–Germer) confirms it.
- Photons carry momentum `p = h/λ = E/c`.

**Formulas**

```
Photon energy:           E = h f = h c / λ = 1242 eV·nm / λ(nm)
Einstein's equation:     h f = φ + K_max       (φ = work function)
Threshold:               f0 = φ/h ;  λ0 = hc/φ
Stopping potential:      e V_s = K_max = h f − φ
Photon momentum:         p = h/λ = E/c
De Broglie wavelength:   λ = h/p = h/(m v)
  Electron via V volts:  λ = h/√(2 m e V) = 12.27 / √V  Å
Intensity → number:      N = I /(h f) photons/s·m²
```

**Worked example — photon energy.** Green light 500 nm: `E = 1242/500 = 2.48 eV`.

**Worked example — photoelectric.** Light of 400 nm on a metal with `φ = 2.0 eV`: `E = 1242/400 = 3.105 eV` ; `K_max = 3.105 − 2.0 = 1.1 eV` ; stopping potential `= 1.1 V` ; threshold wavelength `= 1242/2.0 = 621 nm`.

**Worked example — de Broglie.** An electron accelerated through 100 V: `λ = 12.27/√100 = 1.23 Å` — comparable to atomic spacing, hence crystal diffraction.

**Worked example — photon count.** A 1 W laser at 632.8 nm: photon energy `= 1242/632.8 = 1.963 eV = 3.14×10⁻¹⁹ J`; rate `= 1/3.14×10⁻¹⁹ = 3.2×10¹⁸ photons/s`.

**Worked example — which colour?** Sodium (`φ = 2.3 eV`): threshold `λ0 = 1242/2.3 = 540 nm` — red light (700 nm) cannot eject electrons however bright; blue (450 nm) can.

---

## Chapter 43 — Bohr's Model and Physics of the Atom

**Key points**
- **Rutherford** nuclear model: dense, positive nucleus with electrons around it. Classically it should collapse (accelerating charges radiate) — **Bohr** fixed this with quantisation.
- **Hydrogen spectrum:** line series — Lyman (UV, `n→1`), Balmer (visible, `n→2`), Paschen (IR, `n→3`).
- **Bohr's postulates:** (1) electrons move in stable circular orbits (no radiation); (2) allowed orbits have **angular momentum** `mvr = nh/2π`; (3) a photon is emitted/absorbed when an electron jumps, `hf = E_i − E_f`.
- Ground-state energy of hydrogen = **−13.6 eV**; the energy needed to remove it is the **ionisation energy**.
- Bohr's model works for hydrogen-like ions (He⁺, Li²⁺) but fails for multi-electron atoms and fine details.
- **Quantum mechanics:** the electron is described by a wave function whose square gives probability density. Quantum numbers `n, l, m_l, m_s` label states.
- **Laser:** light amplification by stimulated emission — needs population inversion; light is coherent, monochromatic, directional.

**Formulas**

```
Radius of nth orbit:        r_n = a0 n²/Z ;   a0 = 0.529 Å
Speed in nth orbit:         v_n = (Z/n) × 2.19×10⁶ m/s   (= c Z α / n, α = 1/137)
Energy of nth level:        E_n = −13.6 Z² / n² eV
Photon from n2 → n1:        hf = E_n2 − E_n1 = 13.6 Z² (1/n1² − 1/n2²) eV
Spectral lines:             1/λ = R Z² (1/n1² − 1/n2²) ,  R = 1.097×10⁷ m⁻¹
Series limits:              Lyman n1 = 1 ; Balmer n1 = 2 ; Paschen n1 = 3 ; Brackett n1 = 4
Angular momentum:           L = n h/2π = n ħ
Number of lines:            n(n − 1)/2 for transitions among n levels
Excitation/ionisation:      E_ion = 13.6 Z² eV (from ground state)
```

**Worked example — Hα line.** Balmer `n=3 → n=2`: `1/λ = 1.097×10⁷ × (1/4 − 1/9) = 1.524×10⁶ m⁻¹` → `λ = 656 nm` (red).

**Worked example — Lyman α.** `n=2 → 1`: `ΔE = 13.6×(1 − 1/4) = 10.2 eV` ; `λ = 1242/10.2 = 121.8 nm` (UV).

**Worked example — energy levels.** Hydrogen: `E1 = −13.6`, `E2 = −3.4`, `E3 = −1.51`, `E4 = −0.85 eV`.

**Worked example — He⁺ (Z = 2).** `E1 = −13.6×4 = −54.4 eV`; orbit radius `a0/2 = 0.265 Å`.

**Worked example — lines.** An electron excited to `n = 4` can return in `4×3/2 = 6` different ways, giving 6 spectral lines.

---

## Chapter 44 — X-rays

**Key points**
- Produced when fast electrons strike a metal target (Coolidge tube). The spectrum has two parts: a **continuous** spectrum (bremsstrahlung) with a sharp **minimum wavelength**, and **characteristic** lines specific to the target element.
- **Soft** X-rays are low-energy (low voltage); **hard** are high-energy (penetrating).
- **Duane–Hunt:** the cutoff wavelength depends only on accelerating voltage.
- **Moseley's law:** `√f ∝ (Z − b)`, so the atomic number determines the characteristic lines (basis for ordering the periodic table).
- **Bragg's law** gives the angles for X-ray diffraction by crystal planes.
- **Uses:** medical imaging, crystallography, security; **hazard:** ionising radiation.

**Formulas**

```
Minimum wavelength:      λ_min = h c / (e V) = 12 400 / V(volts)  Å   (= 12.4 / V(kV) Å)
Characteristic Kα:       f = (3/4) R c (Z − 1)²      (Moseley, b = 1)
Moseley's law:           √f = a (Z − b)
Bragg's law:             2 d sinθ = n λ
Intensity attenuation:   I = I0 e^(−μ x) ;  half-value layer x_½ = 0.693/μ
```

**Worked example — cutoff.** 30 kV tube: `λ_min = 12 400/30 000 = 0.413 Å`.

**Worked example — Bragg.** Plane spacing `d = 2.0 Å`, X-rays of `λ = 1.5 Å`, first order: `sinθ = 1.5/(2×2.0) = 0.375` → `θ = 22.0°`. Second order (`n = 2`) would need `sinθ = 0.75`, `θ = 48.6°`.

**Worked example — Moseley (Kα of copper, Z = 29).** `f = 0.75 × 1.097×10⁷ × 3×10⁸ × 28² = 1.94×10¹⁸ Hz` → `λ = c/f = 1.55 Å` (the observed Cu Kα is 1.54 Å).

**Worked example — attenuation.** If `μ = 0.5 cm⁻¹`, a 2 cm thick absorber transmits `e⁻¹ = 37 %`.

---

## Chapter 45 — Semiconductors and Semiconductor Devices

**Key points**
- **Energy bands:** valence band (filled), conduction band (empty at 0 K); the gap `E_g` decides the material. Conductors: bands overlap; insulators: large gap (> ~3 eV); semiconductors: small gap (Si 1.1 eV, Ge 0.67 eV).
- **Intrinsic** semiconductor: pure; electrons and holes in equal numbers `n_i`. Conductivity rises with temperature.
- **Doping:** n-type (donors, e.g. P in Si; majority electrons), p-type (acceptors, e.g. B in Si; majority holes).
- **Mass-action law:** `n p = n_i²`.
- **p–n junction:** diffusion makes a depletion region with a built-in barrier. Forward bias lowers the barrier (conducts); reverse bias widens it (tiny leakage).
- **Diode** rectifies AC; **Zener** diode regulates voltage in reverse breakdown.
- **Transistor** (npn/pnp): current gain `β = I_C/I_B`; used as switch and amplifier.
- **Logic gates:** AND, OR, NOT (basics), NAND/NOR (universal), XOR.

**Formulas**

```
Current by carriers:       I = e (n_e v_e + n_h v_h) A
Conductivity:              σ = e (n_e μ_e + n_h μ_h)
Intrinsic:                 n_e = n_h = n_i
Mass-action law:           n_e n_h = n_i²
Wavelength for band gap:   λ_max = 1242 / E_g(eV)  nm  (max λ that excites an electron)
Transistor (CE):           I_E = I_B + I_C ;  β = I_C/I_B ;  α = I_C/I_E ;  β = α/(1 − α)
Voltage gain (CE):         A_v = β R_C / R_in
Half-wave rectifier:       V_dc = V_peak/π , efficiency ≈ 40.6 %
Full-wave rectifier:       V_dc = 2 V_peak/π , efficiency ≈ 81.2 %
```

**Truth tables**

| A | B | AND | OR | NAND | NOR | XOR |
|---|---|---|---|---|---|---|
| 0 | 0 | 0 | 0 | 1 | 1 | 0 |
| 0 | 1 | 0 | 1 | 1 | 0 | 1 |
| 1 | 0 | 0 | 1 | 1 | 0 | 1 |
| 1 | 1 | 1 | 1 | 0 | 0 | 0 |

NOT: `0 → 1`, `1 → 0`.

**Worked example — band gap.** Silicon (1.1 eV) absorbs photons of `λ ≤ 1242/1.1 = 1129 nm` (visible and near-IR) — so it makes solar cells.

**Worked example — mass-action.** Si `n_i = 1.5×10¹⁶ m⁻³` doped with `10²² m⁻³` donors: `n_e ≈ 10²²`, so holes `n_h = (1.5×10¹⁶)²/10²² = 2.25×10¹⁰ m⁻³`.

**Worked example — transistor.** `I_B = 20 μA`, `β = 49` → `I_C = 0.98 mA`; `I_E = 1.0 mA`; `α = 0.98` ✓ (`β = 0.98/0.02 = 49`).

**Worked example — rectifier.** A transformer secondary of 10 V peak: half-wave `V_dc = 3.18 V`, full-wave `6.37 V`.

---

## Chapter 46 — The Nucleus

**Key points**
- The nucleus has **Z protons** and **N neutrons**; mass number `A = Z + N`. **Isotopes** share Z; **isobars** share A; **isotones** share N.
- Nuclear radius `R = R₀ A^(1/3)` with `R₀ ≈ 1.1 fm`, so **nuclear density is constant** (~ 2×10¹⁷ kg/m³) for all nuclei.
- Atomic mass unit: `1 u = 931.5 MeV/c²`.
- **Binding energy** = energy released when the nucleus forms = mass defect × `c²`. **Binding energy per nucleon** peaks near Fe (~8.8 MeV), which explains why fission (heavy nuclei) and fusion (light nuclei) both release energy.
- **Nuclear forces:** strong, short-range, charge-independent, saturating.
- **Radioactive decay** is spontaneous and random: α (He nucleus), β⁻ (electron + antineutrino), β⁺, γ (photon).
- **Decay law:** the number of nuclei falls exponentially; **half-life** `T_½` and **mean life** `τ`.
- **Fission:** a heavy nucleus (U-235) splits after absorbing a neutron, releasing ~200 MeV and more neutrons → chain reaction (controlled in a reactor with moderator and control rods; uncontrolled in a bomb).
- **Fusion:** light nuclei combine (powers the Sun); needs very high temperature.

**Formulas**

```
Nuclear radius:          R = R0 A^(1/3) ,  R0 = 1.1 fm
Mass defect:             Δm = Z m_p + (A − Z) m_n − m_nucleus
Binding energy:          B = Δm × 931.5 MeV (Δm in u)
Radioactive decay law:   N = N0 e^(−λt) ,  A = λ N = A0 e^(−λt)  (activity)
Half-life:               T_½ = 0.693/λ ;   mean life τ = 1/λ = 1.44 T_½
After n half-lives:      N = N0 / 2ⁿ
Alpha decay:             ZXᴬ → Z−2Yᴬ⁻⁴ + ₂He⁴
Beta-minus:              ZXᴬ → Z+1Yᴬ + e⁻ + antineutrino
Q-value of a reaction:   Q = (m_reactants − m_products) c²
Activity units:          1 curie = 3.7×10¹⁰ Bq ;  1 Bq = 1 decay/s
```

**Worked example — binding energy of ⁴He.** `Δm = 2(1.007825) + 2(1.008665) − 4.00260 = 0.03038 u` → `B = 0.03038×931 = 28.3 MeV` → `7.07 MeV per nucleon`.

**Worked example — nuclear radius.** `A = 64`: `R = 1.1×64^(1/3) = 1.1×4 = 4.4 fm`.

**Worked example — half-life.** 80 g sample with `T_½ = 10 days`: after 30 days (3 half-lives) → `80/8 = 10 g`.

**Worked example — decay constant.** `T_½ = 1 h` → `λ = 0.693/3600 = 1.93×10⁻⁴ s⁻¹`.

**Worked example — fission energy.** Complete fission of 1 kg of U-235 (200 MeV per nucleus): `N = 1000/235 × 6.02×10²³ = 2.56×10²⁴` nuclei → `E = 2.56×10²⁴ × 200 × 1.6×10⁻¹³ = 8.2×10¹³ J` ≈ 20 kilotons of TNT.

**Worked example — decay chain.** ²³⁸U (Z=92) → α → ²³⁴Th (Z=90) → β⁻ → ²³⁴Pa (Z=91).

---

## Chapter 47 — The Special Theory of Relativity

**Key points**
- **Principle of relativity:** the laws of physics are the same in all inertial frames.
- **Einstein's second postulate:** the speed of light in vacuum is the same for all inertial observers. This conflicts with the Galilean addition of velocities, forcing a revision of space and time.
- **Time dilation:** a moving clock runs slow. **Length contraction:** lengths along the motion shrink. **Simultaneity** is relative.
- **Relativistic momentum and energy:** `p = γ m v`, `E = γ m c²`. Nothing with mass can reach `c`.
- **Rest energy** `E₀ = mc²`: mass is a form of energy — the origin of nuclear energy release.
- **Twin paradox:** the travelling twin, who changes frames, ages less.
- Everyday speeds make `γ ≈ 1`, so Newtonian mechanics remains accurate there.

**Formulas**

```
Lorentz factor:             γ = 1/√(1 − v²/c²)
Time dilation:              Δt = γ Δt0      (Δt0 = proper time)
Length contraction:         L = L0 /γ      (along the direction of motion)
Velocity addition:          u' = (u + v)/(1 + u v/c²)
Relativistic momentum:      p = γ m0 v
Relativistic energy:        E = γ m0 c² ;   K = (γ − 1) m0 c²
Energy–momentum relation:   E² = p²c² + m0²c⁴
Mass-energy:                E0 = m0 c²
```

| v/c | γ |
|---|---|
| 0.1 | 1.005 |
| 0.6 | 1.25 |
| 0.8 | 1.667 |
| 0.9 | 2.294 |
| 0.99 | 7.09 |

**Worked example — time dilation.** A spaceship at `0.8c`: `γ = 1/√(1 − 0.64) = 1.667`. A 10-year trip (Earth frame) takes `10/1.667 = 6 years` on the ship — the travelling twin returns 4 years younger.

**Worked example — length contraction.** A 100 m spaceship at `0.6c` (`γ = 1.25`) appears `100/1.25 = 80 m` to a stationary observer.

**Worked example — velocity addition.** Two rockets each at `0.8c` moving towards each other: relative speed `= 1.6c/(1 + 0.64) = 0.976c` (< c).

**Worked example — kinetic energy.** An electron at `0.6c`: `K = (γ − 1) m c² = 0.25 × 0.511 MeV = 0.128 MeV`.

**Worked example — mass–energy.** Converting 1 g of mass: `E = 10⁻³ × (3×10⁸)² = 9×10¹³ J` — about the energy released by 20 kt of TNT.

---

# APPENDIX — Reference

## Constants

| Quantity | Symbol | Value |
|---|---|---|
| Speed of light | c | 3.00 × 10⁸ m/s |
| Planck constant | h | 6.626 × 10⁻³⁴ J·s = 4.136 × 10⁻¹⁵ eV·s |
| `hc` | | 1242 eV·nm = 12 400 eV·Å |
| Elementary charge | e | 1.602 × 10⁻¹⁹ C |
| Electron mass | m_e | 9.109 × 10⁻³¹ kg (0.511 MeV/c²) |
| Proton mass | m_p | 1.6726 × 10⁻²⁷ kg |
| Neutron mass | m_n | 1.6749 × 10⁻²⁷ kg |
| Atomic mass unit | u | 1.6605 × 10⁻²⁷ kg = 931.5 MeV/c² |
| Boltzmann constant | k | 1.381 × 10⁻²³ J/K |
| Gas constant | R | 8.314 J/mol·K |
| Avogadro number | N_A | 6.022 × 10²³ mol⁻¹ |
| Permittivity of vacuum | ε0 | 8.854 × 10⁻¹² C²/N·m² |
| Permeability of vacuum | μ0 | 4π × 10⁻⁷ T·m/A |
| Coulomb constant | 1/4πε0 | 9 × 10⁹ N·m²/C² |
| Faraday constant | F | 96 485 C/mol |
| Stefan–Boltzmann constant | σ | 5.67 × 10⁻⁸ W/m²K⁴ |
| Wien's constant | b | 2.898 × 10⁻³ m·K |
| Rydberg constant | R | 1.097 × 10⁷ m⁻¹ |
| Bohr radius | a0 | 0.529 Å |
| Electron specific charge | e/m | 1.76 × 10¹¹ C/kg |

## Common mistakes to avoid

1. **Celsius vs kelvin.** Gas laws, Carnot efficiency, Stefan's law and Wien's law need **kelvin**.
2. **Sign of work in the first law.** `W > 0` when the gas does work on its surroundings; for compression `W < 0`.
3. **Using `Cp` for `ΔU`.** `ΔU = n Cv ΔT` for an ideal gas in *any* process.
4. **Adiabatic ≠ isothermal.** Adiabatic: `pV^γ = const`, T changes. Isothermal: `pV = const`, T fixed.
5. **Potential is a scalar, field is a vector.** Add potentials algebraically; add fields as vectors.
6. **Gauss's law** gives total flux from *enclosed* charge only; use a surface that makes `E` constant.
7. **Series vs parallel capacitors** are the *opposite* of resistors.
8. **Capacitor connected to a battery** keeps `V` fixed; **disconnected** it keeps `Q` fixed. Know which before changing the dielectric or plate separation.
9. **Magnetic force does no work** — it changes direction but not speed.
10. **RMS vs peak** in AC: ratings and meters use RMS; capacitors/insulation must handle the peak (`√2` larger).
11. **Power factor.** Only `V_rms I_rms cosφ` is real power.
12. **Photoelectric effect:** if `f < f₀`, increasing intensity does *nothing*. Stopping potential depends on frequency, not intensity.
13. **Energy-level problems:** hydrogen-like `Z²/n²` scaling; check whether the question wants energy, wavelength or number of lines.
14. **Nuclear problems:** use the mass defect with atomic masses consistently; keep `A` and `Z` balanced on both sides of a reaction.
15. **Relativity:** `γ` always ≥ 1; the *proper* time/length is the one measured in the object's own rest frame.

---
*How these notes were made: from the chapter and section list of `physics-book-2.pdf` (Concepts of Physics, Vol. 2), with the standard formulas for each topic and a few facts spot-checked against the book's text (the nuclear radius `R = R0 A^(1/3)`, `R0 = 1.1 fm`, `1 u = 931 MeV/c²`, the ⁴He binding-energy example, `hc = 1242 eV·nm`, and the Faraday constant). The book's own full derivations and its exercise problems are not reproduced here. Every worked example was recomputed independently; use them as practice and compare with the book's treatment.*
