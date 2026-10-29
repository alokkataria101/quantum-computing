# Physics Book 1 — Study Notes
**Concepts of Physics, Volume 1 (Chapters 1–22) — H C Verma**

Mechanics (Ch 1–14) · Waves & Wave Optics (Ch 15–17) · Optics (Ch 18–22)

> **How to use these notes.** Each chapter has *Key points*, *Formulas* and a *Worked example* with the arithmetic shown, so you can re-check it. Formulas are written in plain text so they read anywhere. The numbers in the examples were recomputed while writing these notes.
>
> **Conventions.** `g = 10 m/s²` is used in most of the book's numerical problems (9.8 m/s² where stated). `A·B` is the dot product, `A×B` the cross product. SI units unless stated.

---

## Contents

| Part | Chapters |
|---|---|
| Foundations | 1 Introduction · 2 Physics & Mathematics |
| Motion & forces | 3 Kinematics · 4 The Forces · 5 Newton's Laws · 6 Friction · 7 Circular Motion |
| Energy & momentum | 8 Work & Energy · 9 Centre of Mass, Momentum, Collision · 10 Rotational Mechanics |
| Gravity, oscillations, matter | 11 Gravitation · 12 SHM · 13 Fluid Mechanics · 14 Properties of Matter |
| Waves | 15 Waves on a String · 16 Sound · 17 Light Waves |
| Optics | 18 Geometrical Optics · 19 Optical Instruments · 20 Dispersion · 21 Speed of Light · 22 Photometry |
| Reference | Constants · Common mistakes |

---

# PART A — FOUNDATIONS

## Chapter 1 — Introduction to Physics

**Key points**
- Physics studies matter, energy and their interactions; it is built on measurement, so every quantity needs a **unit**.
- **SI base units (7):** metre (m), kilogram (kg), second (s), ampere (A), kelvin (K), mole (mol), candela (cd).
- **Dimensions** express a quantity in terms of `[M] [L] [T]` (and `[A] [K]`...). Only quantities with the same dimensions can be added, subtracted or equated.
- **Uses of dimensional analysis:** (1) check a formula, (2) convert units, (3) derive a relation (up to a constant).
- **Order of magnitude** = nearest power of 10; used for quick estimates.

**Common dimensions**

```
Velocity            [L T⁻¹]            Force        [M L T⁻²]
Acceleration        [L T⁻²]            Energy/Work  [M L² T⁻²]
Pressure            [M L⁻¹ T⁻²]        Power        [M L² T⁻³]
Momentum / Impulse  [M L T⁻¹]          Angular mom. [M L² T⁻¹]
Density             [M L⁻³]            Frequency    [T⁻¹]
```

**Worked example — derive the pendulum period**
Assume `T = k · l^a · m^b · g^c`. Dimensions: `T¹ = L^a · M^b · (L T⁻²)^c`.
- M: `b = 0` · T: `−2c = 1 → c = −1/2` · L: `a + c = 0 → a = 1/2`
- So `T = k √(l/g)` (the constant `k = 2π` comes from experiment/theory).

**Worked example — unit conversion**
`1 N = 1 kg·m/s² = (1000 g)(100 cm)/s² = 10⁵ g·cm/s² = 10⁵ dyne`.

---

## Chapter 2 — Physics and Mathematics

**Key points**
- **Scalar:** magnitude only (mass, time, work). **Vector:** magnitude + direction (force, velocity).
- Vector addition uses the **parallelogram/triangle law**; subtraction is `A − B = A + (−B)`.
- **Dot product** gives a scalar; **cross product** gives a vector ⟂ to both (right-hand rule).
- **Calculus basics** are used throughout: derivatives give rates, integrals give accumulations; `dy/dx = 0` gives maxima/minima.
- **Significant digits & errors:** report only what the instrument justifies.

**Formulas**

```
Resultant of A, B at angle θ:   R = √(A² + B² + 2AB cosθ)
Direction from A:               tan α = B sinθ / (A + B cosθ)
Resolution:                     Ax = A cosθ ,  Ay = A sinθ
Dot product:                    A·B = AB cosθ = AxBx + AyBy + AzBz
Cross product:                  |A×B| = AB sinθ ;  i×j = k, j×k = i, k×i = j
Differentiation:                d(xⁿ)/dx = n xⁿ⁻¹ ; d(sin x)/dx = cos x ; d(eˣ)/dx = eˣ
Integration:                    ∫xⁿ dx = xⁿ⁺¹/(n+1) + C (n ≠ −1) ; ∫dx/x = ln x
Maxima / minima:                dy/dx = 0 ; d²y/dx² < 0 → max, > 0 → min
Errors:  Z = A ± B              ΔZ = ΔA + ΔB
         Z = A·B or A/B         ΔZ/Z = ΔA/A + ΔB/B
         Z = Aⁿ                 ΔZ/Z = n·ΔA/A
```

**Worked example — vectors.** `A = 3`, `B = 4` at 90°: `R = √(9 + 16) = 5`.
Dot product of `A=2`, `B=5` at 60°: `2×5×cos60° = 5`.

**Worked example — error propagation.** Length `5.0 ± 0.1 m`, breadth `2.0 ± 0.1 m`.
Area = 10 m²; relative error = `0.1/5.0 + 0.1/2.0 = 0.02 + 0.05 = 0.07` → area = **10 ± 0.7 m²**.

**Worked example — maximum.** Maximise `y = 12x − x²`: `dy/dx = 12 − 2x = 0 → x = 6`; `d²y/dx² = −2 < 0` so it is a maximum, `y_max = 36`.

**Significant-digit rules.** Addition/subtraction → keep the fewest *decimal places*. Multiplication/division → keep the fewest *significant figures*.

---

# PART B — MOTION AND FORCES

## Chapter 3 — Rest and Motion: Kinematics

**Key points**
- Rest/motion is **relative to a frame of reference**.
- **Distance** (scalar, path length) ≥ **|displacement|** (vector, straight line start → end).
- Average speed = total distance / total time. Average velocity = displacement / time.
- **Uniform acceleration** equations apply only when `a` is constant.
- The **area under a v–t graph = displacement**; **slope of v–t = acceleration**; slope of x–t = velocity.
- Projectile motion: horizontal velocity constant, vertical motion has `a = −g`; the two are independent.

**Formulas**

```
v = u + at
s = ut + ½at²
v² = u² + 2as
s(nth second) = u + a(2n − 1)/2

Projectile (speed u, angle θ above horizontal):
  Time of flight   T = 2u sinθ / g
  Max height       H = u² sin²θ / (2g)
  Range            R = u² sin 2θ / g       (max at θ = 45°, R_max = u²/g)
  Trajectory       y = x tanθ − g x² / (2u² cos²θ)

Relative velocity:   v(A rel. B) = vA − vB
River crossing (river v_r, boat-in-water v_b, width d):
  Shortest time:   t = d / v_b  (head straight across), drift = v_r · t
  Shortest path:   needs v_b > v_r ; sinθ = v_r / v_b (upstream), t = d / √(v_b² − v_r²)
```

**Worked example — projectile.** `u = 20 m/s`, `θ = 30°`, `g = 10`:
- `T = 2×20×0.5/10 = 2 s`
- `H = 400×0.25/(2×10) = 5 m`
- `R = 400×sin60°/10 = 40×0.866 = 34.6 m`

**Worked example — ball thrown up** at `4.0 m/s`: at the top `v = 0`, so `H = u²/2g = 16/20 = 0.8 m`.

**Worked example — river.** Width 100 m, `v_r = 3 m/s`, `v_b = 5 m/s`.
Shortest time: `t = 100/5 = 20 s`, drift `= 3×20 = 60 m`.
Shortest path: `t = 100/√(25 − 9) = 100/4 = 25 s`.

---

## Chapter 4 — The Forces

**Key points**
- Four fundamental forces: **gravitational**, **electromagnetic**, **strong (nuclear)**, **weak**.
- Gravity is the weakest but acts over long range and is always attractive; it dominates astronomical scales.
- Electromagnetic force is far stronger than gravity (for two protons it is about 10³⁶ times larger) and explains contact forces, friction, tension, normal reaction.
- Nuclear force: very strong, very short range (~fm). Weak force is responsible for β-decay.
- **Contact forces** (normal, friction, tension) are really electromagnetic in origin.

**Formulas**

```
Gravitation:   F = G m1 m2 / r²          G = 6.67 × 10⁻¹¹ N·m²/kg²
Coulomb:       F = k q1 q2 / r²          k = 1/(4πε0) = 9 × 10⁹ N·m²/C²
Weight:        W = mg
```

**Worked example — Coulomb.** Two `1 μC` charges `10 cm` apart:
`F = 9×10⁹ × (10⁻⁶)(10⁻⁶) / (0.1)² = 9×10⁻³ / 10⁻² = 0.9 N`.

---

## Chapter 5 — Newton's Laws of Motion

**Key points**
- **First law:** a body keeps its state of rest or uniform motion unless a net force acts (defines inertial frames).
- **Second law:** `F_net = dp/dt = ma`. Direction of acceleration = direction of net force.
- **Third law:** forces come in equal-and-opposite *pairs acting on different bodies*, so they never cancel on one body.
- **Free-body diagrams (FBDs):** isolate one body, draw all forces on it, write `ΣF = ma` along chosen axes.
- **Pseudo force:** in a frame accelerating with `a0`, add `−m·a0` to every body.
- **Inertia** is resistance to change of motion; mass is the measure.
- **Constraint:** a taut inextensible string forces connected bodies to have equal speed along it.

**Formulas**

```
F = ma ;  p = mv ;  F = dp/dt ;  Impulse J = F·Δt = Δp
Weight in a lift (acceleration a up):      N = m(g + a)   (down: N = m(g − a))
Block on smooth incline:                   a = g sinθ ;  N = mg cosθ
Atwood machine:                            a = (m1 − m2)g / (m1 + m2)
                                           T = 2 m1 m2 g / (m1 + m2)
Pseudo force in frame with accel a0:       F_pseudo = −m a0
```

**Worked example — Atwood.** `m1 = 3 kg`, `m2 = 1 kg`, `g = 10`:
`a = (3 − 1)×10/4 = 5 m/s²` ; `T = 2×3×1×10/4 = 15 N`.
Check on m1: `mg − T = 30 − 15 = 15 N = 3 × 5` ✓.

**Worked example — lift.** A 60 kg person in a lift accelerating up at 2 m/s²: `N = 60 × (10 + 2) = 720 N`. In free fall `N = 0` (weightlessness).

---

## Chapter 6 — Friction

**Key points**
- Friction is the tangential component of the contact force between surfaces.
- **Static friction** adjusts itself up to a maximum: `f ≤ μs N`. **Kinetic friction** is constant: `fk = μk N`, with `μk < μs`.
- Friction does not depend on contact area (for the laws of friction at this level).
- **Angle of repose:** the incline angle at which a block just starts to slide: `tanθ = μs`.
- Friction opposes *relative (or attempted relative) motion*, not motion itself — it can be the force that accelerates you (walking, a car).
- Measure `μ` in the laboratory with an inclined plane.

**Formulas**

```
Limiting (max) static friction:   fs,max = μs N
Kinetic friction:                 fk = μk N
Angle of repose:                  tan θ = μs
Block on rough incline (sliding): a = g (sinθ − μk cosθ)
Minimum force to drag a block:    F_min = μ mg / √(1 + μ²)  at tanφ = μ (φ above horizontal)
```

**Worked example.** 5 kg block on a rough floor, `μk = 0.2`, pushed with 20 N:
`fk = 0.2 × 50 = 10 N` ; `a = (20 − 10)/5 = 2 m/s²`.

**Worked example — repose.** `μs = 0.5` → `θ = tan⁻¹ 0.5 = 26.6°`. Block stays at rest for any angle below that.

**Worked example — minimum drag force.** `m = 5 kg`, `μ = 0.5`: `F_min = 0.5×50/√1.25 = 25/1.118 = 22.4 N` (less than the 25 N needed for a horizontal pull).

---

## Chapter 7 — Circular Motion

**Key points**
- **Angular variables:** `θ`, `ω = dθ/dt`, `α = dω/dt`. Link to linear: `v = rω`, `a_t = rα`.
- In uniform circular motion speed is constant but **velocity changes direction** — there is a centripetal acceleration `a_c = v²/r` towards the centre.
- **Centripetal force** is not a new force; it is the *net inward force* supplied by tension, gravity, friction, normal etc.
- **Banking** of roads lets the normal force supply part (or all) of the centripetal force.
- **Centrifugal force** is a pseudo force felt in the rotating frame.
- Because the Earth rotates, apparent weight is slightly less at the equator.

**Formulas**

```
v = rω ;  a_c = v²/r = ω²r ;  T = 2π/ω = 2πr/v ;  f = 1/T
Tangential acceleration:             a_t = rα
Flat road, max safe speed:           v_max = √(μ r g)
Banked road (no friction):           tanθ = v² / (r g)
Banked with friction:                v²/(rg) = (μ + tanθ)/(1 − μ tanθ)
Vertical circle (string, mass m):
   top:     T + mg = m v²/r      → min speed at top   v_top = √(gr)
   bottom:  T − mg = m v²/r      → min speed at bottom v_bot = √(5gr)
Conical pendulum:                    T_period = 2π √(L cosθ / g)
Apparent g at latitude λ:            g' ≈ g − ω²R cos²λ
```

**Worked example — banking.** `v = 20 m/s`, `r = 40 m`, `g = 10`: `tanθ = 400/(40×10) = 1 → θ = 45°`.

**Worked example — flat curve.** `μ = 0.4`, `r = 40 m`: `v_max = √(0.4×40×10) = √160 = 12.6 m/s` (≈ 45 km/h).

**Worked example — loop.** Radius 1 m: minimum speed at the top `√(10×1) = 3.16 m/s`; at the bottom `√(5×10×1) = 7.07 m/s`.

**Worked example — Earth's rotation.** At the equator `ω = 7.27×10⁻⁵ rad/s`, `R = 6.4×10⁶ m`: `ω²R = 0.034 m/s²` — a ~0.35 % reduction in apparent `g`.

---

# PART C — ENERGY, MOMENTUM, ROTATION

## Chapter 8 — Work and Energy

**Key points**
- **Work** is force times displacement along the force: `W = F·d`. It is a scalar and can be negative.
- **Work–energy theorem:** net work on a body = change in kinetic energy.
- **Conservative force:** work depends only on end points (gravity, spring, electrostatic). Friction is non-conservative.
- If only conservative forces act, **mechanical energy is conserved**: `K + U = constant`.
- Force = negative gradient of potential energy: `F = −dU/dx`; equilibrium where `dU/dx = 0` (stable if `d²U/dx² > 0`).
- **Mass-energy equivalence:** `E = mc²`.

**Formulas**

```
Work:                    W = F·d = F d cosθ ;   W = ∫F·dx
Kinetic energy:          K = ½ m v² = p²/2m
Work–energy theorem:     W_net = ΔK
Gravitational PE:        U = m g h
Spring PE:               U = ½ k x²       (spring force F = −kx)
Power:                   P = dW/dt = F·v ;  1 hp = 746 W
Mass-energy:             E = Δm c²
Conservative force:      F = −dU/dx
```

**Worked example — free fall.** Drop 2 kg from 5 m: `v = √(2gh) = √100 = 10 m/s`. `K = ½×2×100 = 100 J = mgh = 2×10×5` ✓.

**Worked example — spring.** `k = 200 N/m` compressed `0.10 m` launches a `0.5 kg` block:
`U = ½×200×0.01 = 1 J` ; `v = √(2U/m) = √4 = 2 m/s`.

**Worked example — power.** Engine pulling with 2000 N at 20 m/s: `P = F·v = 40 000 W = 40 kW`.

---

## Chapter 9 — Centre of Mass, Linear Momentum, Collision

**Key points**
- **Centre of mass (COM)** moves as if all mass were concentrated there and all external forces acted on it: `F_ext = M a_cm`.
- Without external force, **total momentum is conserved**, and COM velocity is constant.
- **Elastic collision:** momentum *and* kinetic energy conserved. **Inelastic:** momentum conserved, KE lost. **Perfectly inelastic:** bodies stick.
- **Coefficient of restitution** `e = (speed of separation)/(speed of approach)`; `e = 1` elastic, `e = 0` perfectly inelastic.
- **Rocket** thrust comes from expelling mass: momentum conservation applied to a variable-mass system.
- **Impulse** = area under F–t graph = change in momentum.

**Formulas**

```
COM:                    x_cm = Σ m_i x_i / Σ m_i
Momentum conservation:  m1u1 + m2u2 = m1v1 + m2v2
Elastic, 1-D:
   v1 = [(m1 − m2)u1 + 2 m2 u2] / (m1 + m2)
   v2 = [(m2 − m1)u2 + 2 m1 u1] / (m1 + m2)
   (equal masses simply exchange velocities)
Perfectly inelastic:    v = (m1u1 + m2u2)/(m1 + m2)
   KE lost = ½ μ (u1 − u2)² ,  μ = m1m2/(m1 + m2)
Restitution:            e = (v2 − v1)/(u1 − u2)
Bounce from height h:   h' = e² h
Rocket:                 v = v0 + u_rel ln(m0/m)
Impulse:                J = ∫F dt = Δp
```

**Worked example — elastic.** `m1 = 2 kg` at `6 m/s` hits `m2 = 4 kg` at rest:
`v1 = (2−4)×6/6 = −2 m/s` ; `v2 = 2×2×6/6 = 4 m/s`.
Momentum: `12 = 2(−2) + 4(4) = 12` ✓. KE: `36 J = 4 + 32` ✓.

**Worked example — sticking.** Same masses, perfectly inelastic: `v = 12/6 = 2 m/s`. `KE_lost = 36 − ½×6×4 = 24 J`; formula: `½ × (8/6) × 36 = 24 J` ✓.

**Worked example — COM.** 1 kg at `x = 0` and 3 kg at `x = 4 m`: `x_cm = (0 + 12)/4 = 3 m`.

**Worked example — bounce.** `e = 0.5`, dropped from `4 m` → rebounds to `0.25 × 4 = 1 m`.

---

## Chapter 10 — Rotational Mechanics

**Key points**
- Rotation mirrors translation: `x→θ`, `v→ω`, `a→α`, `m→I`, `F→τ`, `p→L`.
- **Torque** `τ = r × F`; Newton's law for rotation: `τ = Iα`.
- **Moment of inertia** depends on mass *and* its distribution relative to the axis.
- **Angular momentum** `L = Iω` is conserved when net external torque is zero (skater, diver).
- **Equilibrium:** `ΣF = 0` and `Στ = 0`.
- **Rolling without slipping:** `v_cm = ωR`; the contact point is instantaneously at rest; friction is static and does no work.
- Rolling KE = translation + rotation.

**Moment of inertia (about axis through centre unless stated)**

```
Thin ring / hollow cylinder        M R²
Solid disc / solid cylinder        ½ M R²
Solid sphere                       (2/5) M R²
Hollow thin sphere                 (2/3) M R²
Thin rod, axis through centre ⟂    M L² / 12
Thin rod, axis through end ⟂       M L² / 3
Parallel-axis theorem              I = I_cm + M d²
Perpendicular-axis (planar body)   I_z = I_x + I_y
```

**Formulas**

```
Rotational kinematics:     ω = ω0 + αt ; θ = ω0 t + ½αt² ; ω² = ω0² + 2αθ
Torque / dynamics:         τ = r F sinθ ;  τ = Iα
Angular momentum:          L = Iω ;  τ = dL/dt
Rotational KE:             K = ½ I ω²
Power:                     P = τ ω ;  Work W = τ θ
Rolling (k = radius of gyration, I = M k²):
   K_total = ½ M v² (1 + k²/R²)
   Acceleration down incline  a = g sinθ / (1 + k²/R²)
```

**Worked example — angular acceleration.** Disc `M = 2 kg`, `R = 0.5 m`: `I = ½×2×0.25 = 0.25 kg·m²`. Torque 5 N·m: `α = 5/0.25 = 20 rad/s²`.

**Worked example — rod.** 1 kg, 1.2 m rod about its end: `I = 1×1.44/3 = 0.48 kg·m²`.

**Worked example — conservation of L.** Skater pulls arms in: `I` from 4 to 2 kg·m², `ω1 = 2 rad/s`: `ω2 = 4×2/2 = 4 rad/s`.

**Worked example — rolling.** Solid sphere on a 30° incline: `a = g sinθ/(1 + 2/5) = 10×0.5×5/7 = 3.57 m/s²` — slower than a frictionless slide (5 m/s²) because some energy goes into rotation. Order at the bottom: sphere > disc > ring (smaller `k²/R²` wins).

---

# PART D — GRAVITATION, OSCILLATIONS, MATTER

## Chapter 11 — Gravitation

**Key points**
- Every two masses attract: `F = G m1 m2/r²` (inverse-square, central, conservative).
- `g` varies with height (decreases), depth (decreases linearly to zero at centre), latitude and Earth's rotation.
- **Gravitational potential** is negative: zero at infinity, more negative closer to the mass.
- **Kepler's laws:** (1) orbits are ellipses with the Sun at a focus; (2) equal areas in equal times (conservation of angular momentum); (3) `T² ∝ a³`.
- In a satellite everything is in free fall → **weightlessness**.
- **Escape velocity** does not depend on the mass of the projectile.
- A **black hole** has escape speed ≥ `c`.
- Inertial mass and gravitational mass are equal (equivalence principle).

**Formulas**

```
Force:                   F = G M m / r²
Surface gravity:         g = G M / R²
g at height h:           g_h = g R² / (R + h)²   ≈ g (1 − 2h/R) for h ≪ R
g at depth d:            g_d = g (1 − d/R)
Potential energy:        U = −G M m / r ;  Potential V = −G M / r
Orbital speed:           v_o = √(G M / r)      (near surface √(gR) ≈ 7.9 km/s)
Time period:             T = 2π √(r³ / G M)
Escape speed:            v_e = √(2 G M / R) = √(2 g R) ≈ 11.2 km/s  (= √2 · v_o)
Satellite energy:        K = GMm/2r ; U = −GMm/r ; E = −GMm/2r (binding energy = +GMm/2r)
Kepler III:              T² ∝ r³   (T1/T2)² = (r1/r2)³
Schwarzschild radius:    R_s = 2 G M / c²
```

**Worked example — escape speed.** `v_e = √(2 × 9.8 × 6.4×10⁶) = √(1.254×10⁸) = 11 200 m/s`.

**Worked example — orbital speed near Earth.** `√(9.8 × 6.4×10⁶) = √(6.27×10⁷) = 7.92 km/s`.

**Worked example — g at height.** At `h = R`: `g_h = g/4 = 2.45 m/s²`.

**Worked example — Kepler III.** A planet at 4× Earth's orbital radius: `T = 4^{3/2} = 8 years`.

**Worked example — black hole.** For the Sun: `R_s = 2×6.67×10⁻¹¹×1.99×10³⁰ / (3×10⁸)² ≈ 2.95 km`.

**Remember.** Geostationary satellite: `T = 24 h`, orbit radius ≈ 42 400 km (height ≈ 36 000 km), moves west-to-east above the equator.

---

## Chapter 12 — Simple Harmonic Motion

**Key points**
- **SHM:** restoring force/acceleration proportional to displacement and opposite to it: `a = −ω² x`.
- Displacement is sinusoidal; speed is maximum at the mean position, zero at extremes; acceleration is max at extremes.
- Total energy is constant: KE ↔ PE exchange; `E = ½ k A²`.
- Period of a spring-mass is independent of `g` and amplitude; pendulum period (small angle) is independent of mass and amplitude.
- **Damped** oscillations: amplitude decays exponentially. **Forced** oscillations: amplitude peaks at **resonance** (driving ≈ natural frequency).

**Formulas**

```
Equation of motion:       d²x/dt² = −ω² x
Solution:                 x = A sin(ωt + φ)
Velocity:                 v = ω √(A² − x²) ;  v_max = Aω
Acceleration:             a = −ω² x ;  a_max = Aω²
Period / frequency:       T = 2π/ω ,  f = 1/T
Spring-mass:              ω = √(k/m) ,  T = 2π √(m/k)
   springs in series:  1/k = 1/k1 + 1/k2 ;  in parallel: k = k1 + k2
Simple pendulum:          T = 2π √(l/g)
Physical pendulum:        T = 2π √(I/(m g d))
Torsional pendulum:       T = 2π √(I/C)
Energy:                   E = ½ k A² = ½ m ω² A²  (K = ½ k (A² − x²), U = ½ k x²)
Superposition (same f):   A = √(A1² + A2² + 2 A1A2 cosφ)
Damped:                   A(t) = A0 e^(−bt/2m)
```

**Worked example — spring.** `k = 100 N/m`, `m = 1 kg`, `A = 0.1 m`:
`ω = 10 rad/s` ; `T = 0.628 s` ; `v_max = 1 m/s` ; `E = ½×100×0.01 = 0.5 J = ½×1×1²` ✓.

**Worked example — pendulum.** `l = 1 m`, `g = 9.8`: `T = 2π√(1/9.8) = 2.007 s`. A "seconds pendulum" (T = 2 s) is ≈ 0.993 m long.

**Worked example — speed at a point.** `A = 0.1 m`, `ω = 10`: at `x = 0.06 m`, `v = 10√(0.01 − 0.0036) = 10×0.08 = 0.8 m/s`.

---

## Chapter 13 — Fluid Mechanics

**Key points**
- Fluids (liquids & gases) flow and take the shape of the container; static fluids cannot support shear.
- **Pressure** at depth `h`: `P = P0 + ρ g h` (depends only on depth, not shape of vessel).
- **Pascal's law:** pressure applied to an enclosed fluid is transmitted undiminished → hydraulic lift.
- **Archimedes:** buoyant force = weight of fluid displaced. A body floats when its density < fluid density.
- **Continuity** (incompressible): `A v = constant`. **Bernoulli:** energy conservation per unit volume along a streamline for steady, non-viscous, incompressible flow.
- Faster flow ⇒ lower pressure (lift on a wing, spray bottle, Venturi meter).
- Atmospheric pressure ≈ `1.013 × 10⁵ Pa` = 76 cm Hg.

**Formulas**

```
Pressure:               P = F/A ;  P = P0 + ρ g h
Hydraulic lift:         F2 = F1 (A2 / A1)
Buoyant force:          B = ρ_fluid · V_displaced · g
Floating fraction:      V_submerged / V = ρ_body / ρ_fluid
Continuity:             A1 v1 = A2 v2
Bernoulli:              P + ½ ρ v² + ρ g h = constant
Torricelli (efflux):    v = √(2 g h)
```

**Worked example — depth.** At 10 m in water: `ρgh = 1000×10×10 = 1.0×10⁵ Pa`; absolute pressure = `2.0×10⁵ Pa` (about 2 atm).

**Worked example — hydraulic lift.** `A2/A1 = 100`, `F1 = 50 N` → `F2 = 5000 N` (work is the same: the small piston moves 100× further).

**Worked example — ice.** `ρ_ice/ρ_water = 0.9` → 90 % of an iceberg is submerged.

**Worked example — continuity.** Pipe narrows from 4 cm to 2 cm diameter: area ÷4, so speed ×4.

**Worked example — Bernoulli.** Horizontal pipe, `v1 = 2 m/s`, `v2 = 4 m/s`, water: `ΔP = ½×1000×(16 − 4) = 6000 Pa` (pressure is lower in the faster section).

**Worked example — Torricelli.** Hole 5 m below the water surface: `v = √(2×10×5) = 10 m/s`.

---

## Chapter 14 — Some Mechanical Properties of Matter

**Key points**
- **Elasticity:** ability to regain shape. **Hooke's law:** stress ∝ strain within the elastic limit.
- Three moduli: **Young's** (longitudinal), **Bulk** (volume), **Shear/rigidity**.
- **Surface tension** arises from cohesive forces; surface energy = `T × area`.
- Small drops and bubbles are spherical to minimise surface area; **excess pressure** inside them is inversely proportional to radius.
- **Capillarity:** liquids rise (wetting, `θ < 90°`) or fall (non-wetting) in thin tubes.
- **Viscosity:** internal friction between fluid layers. **Stokes' law** gives the drag on a small sphere; a falling sphere reaches **terminal velocity**.
- Poiseuille flow through a narrow tube: flow ∝ `r⁴`. Flow turns turbulent above a **critical velocity** (Reynolds number ≈ 2000 for pipes).

**Formulas**

```
Stress = F/A ;  Strain = ΔL/L (longitudinal)
Young's modulus:         Y = (F/A)/(ΔL/L) = F L /(A ΔL)
Bulk modulus:            B = −ΔP /(ΔV/V) ;  compressibility = 1/B
Shear modulus:           η = (F/A)/θ
Poisson's ratio:         σ = (lateral strain)/(longitudinal strain)
Elastic energy density:  u = ½ × stress × strain = ½ Y (strain)²
Surface tension:         T = F/l ;  surface energy = T · ΔA
Excess pressure:         drop 2T/R ; soap bubble (two surfaces) 4T/R
Capillary rise:          h = 2 T cosθ / (r ρ g)
Viscous force:           F = η A (dv/dx)
Poiseuille:              Q = π P r⁴ / (8 η l)
Stokes' law:             F = 6 π η r v
Terminal velocity:       v_t = 2 r² (ρ − σ) g / (9 η)
Reynolds number:         R = ρ v D / η
```

**Worked example — stretching a wire.** Steel `Y = 2×10¹¹ Pa`, `L = 2 m`, `d = 1 mm`, `F = 100 N`:
`A = π(0.5×10⁻³)² = 7.85×10⁻⁷ m²` ; stress `= 1.27×10⁸ Pa` ; strain `= 6.4×10⁻⁴` ; **ΔL = 1.27 mm**.

**Worked example — capillary.** Water (`T = 0.072 N/m`), `r = 0.5 mm`, `θ = 0`:
`h = 2×0.072 / (0.5×10⁻³ × 1000 × 9.8) = 0.144/4.9 = 2.9 cm`.

**Worked example — soap bubble.** `R = 1 cm`, `T = 0.03 N/m`: `ΔP = 4×0.03/0.01 = 12 Pa`.

**Worked example — terminal velocity.** Steel ball (`r = 1 mm`, `ρ = 7800`) in glycerine (`σ = 1260`, `η = 0.83 Pa·s`):
`v_t = 2×10⁻⁶×(7800 − 1260)×9.8/(9×0.83) ≈ 1.7×10⁻² m/s`.

---

# PART E — WAVES

## Chapter 15 — Wave Motion and Waves on a String

**Key points**
- A wave transports **energy and momentum without transporting matter**.
- **Transverse** (particle motion ⟂ propagation; strings, EM) vs **longitudinal** (parallel; sound).
- Wave speed on a string depends only on the string's tension and linear density.
- **Superposition:** displacements add. Equal-frequency waves give interference (constructive/destructive).
- **Reflection:** from a fixed end the wave inverts (phase π); from a free end no inversion.
- **Standing waves** form from two identical counter-propagating waves: nodes (zero) and antinodes (max).
- Polarisation exists only for transverse waves.

**Formulas**

```
Wave equation:          y = A sin(kx − ωt) ;   k = 2π/λ ,  ω = 2π f
Speed:                  v = f λ = ω/k
Speed on a string:      v = √(T/μ)     (μ = mass per unit length)
Power transmitted:      P = ½ μ ω² A² v      (Intensity ∝ A²)
Phase / path:           φ = (2π/λ) × path difference
Interference:           A_res = 2A cos(φ/2) (equal amplitudes)
   constructive φ = 2nπ ; destructive φ = (2n+1)π
Standing wave, string fixed at both ends (length L):
   f_n = n v/(2L) ,  n = 1,2,3...   (harmonics; fundamental n = 1)
   λ_n = 2L/n
Fixed-free string:      f = (2n−1) v/(4L)
Laws of vibration:      f ∝ 1/L ;  f ∝ √T ;  f ∝ 1/√μ
```

**Worked example.** String `μ = 0.01 kg/m`, `T = 100 N`: `v = √(100/0.01) = 100 m/s`.
For `L = 1 m`: fundamental `f1 = 100/2 = 50 Hz`; overtones 100 Hz, 150 Hz...

**Worked example — path difference.** Two sources, path difference `λ/4` → phase `π/2`; resultant amplitude for equal `A`: `2A cos(π/4) = 1.41 A`.

---

## Chapter 16 — Sound Waves

**Key points**
- Sound is a **longitudinal pressure wave**; needs a medium. Described equally by displacement or pressure (90° out of phase).
- Speed depends on the medium: fastest in solids, then liquids, slowest in gases. In gases it rises with temperature (`v ∝ √T`) and is **independent of pressure** at constant T.
- **Newton** assumed isothermal compression (gave 280 m/s — too low); **Laplace** correctly used **adiabatic** (`γ` factor).
- **Intensity level** is logarithmic (decibel). Human hearing range ≈ 20 Hz – 20 kHz; threshold `I0 = 10⁻¹² W/m²`.
- **Beats:** two close frequencies produce periodic loudness changes at `|f1 − f2|`.
- **Doppler effect:** apparent frequency changes with relative motion of source/observer.
- Organ pipes: open at both ends has all harmonics; closed at one end only odd harmonics.
- A **sonic boom** occurs for sources faster than sound (Mach number > 1).

**Formulas**

```
Speed in gas:              v = √(γ P / ρ) = √(γ R T / M)
Speed in solid / liquid:   v = √(Y/ρ)  /  v = √(B/ρ)
Temperature:               v ∝ √T
Intensity:                 I = P0² / (2 ρ v)
Loudness level:            β = 10 log10(I / I0)   (decibels) ,  I0 = 10⁻¹² W/m²
Beats:                     f_beat = |f1 − f2|
Doppler (v = sound speed; v_o, v_s along line observer→source positive for
         observer moving TOWARDS source and source moving TOWARDS observer):
   f' = f (v + v_o)/(v − v_s)
Open pipe (length L):      f_n = n v/(2L)  (n = 1, 2, 3...)
Closed pipe:               f_n = (2n − 1) v/(4L)
Mach number:               M = v_source / v_sound ;  sin θ = 1/M (Mach cone)
```

**Worked example — speed in air.** At 27 °C: `v = √(1.4×8.314×300/0.029) = √(1.204×10⁵) = 347 m/s`. Cross-check with `v ∝ √T` from 332 m/s at 0 °C: `332×√(300/273) = 348 m/s` ✓.

**Worked example — Doppler.** Source 500 Hz approaches a stationary observer at 30 m/s, `v = 330`: `f' = 500×330/(330 − 30) = 550 Hz`.

**Worked example — decibels.** `I = 10⁻⁶ W/m²` → `β = 10 log(10⁶) = 60 dB`. Doubling the intensity adds ≈ 3 dB; ×10 adds 10 dB.

**Worked example — pipes.** `L = 0.5 m`, `v = 340 m/s`: open pipe `f1 = 340/(2×0.5) = 340 Hz`; closed pipe `f1 = 340/(4×0.5) = 170 Hz`.

**Worked example — beats.** 256 Hz and 260 Hz tuning forks → 4 beats per second.

---

## Chapter 17 — Light Waves

**Key points**
- Light shows **interference, diffraction, polarisation** → wave nature (Huygens' principle explains propagation).
- **Interference** needs **coherent** sources (constant phase difference); the Young's experiment splits one wavefront.
- **Optical path** = refractive index × geometrical path.
- **Thin-film** colours come from interference between reflections at the two surfaces (note the phase change of π on reflection from a denser medium).
- **Diffraction:** bending around obstacles/slits. **Fraunhofer** (far field) vs **Fresnel** (near field).
- **Resolution** is limited by diffraction (Rayleigh criterion).
- **Polarisation:** confirms light is transverse; **Brewster's law** gives the polarising angle; **Malus' law** for analysers.

**Formulas**

```
Young's double slit (slit separation d, screen distance D):
   Path difference at angle θ:   Δ = d sinθ ≈ d y / D
   Bright fringes:               Δ = nλ ;  Dark: Δ = (n + ½)λ
   Fringe width:                 β = λ D / d
   Intensity:                    I = 4 I0 cos²(φ/2) ,  I_max = 4 I0 , I_min = 0
Optical path:                    μ × geometric path ;  extra film of thickness t adds (μ − 1) t
Thin film (reflected light):     2 μ t cos r = (2n + 1) λ/2   → bright
Single-slit diffraction:         a sinθ = nλ (minima, n = 1, 2...)
   Central maximum width:        2 λ D / a
Rayleigh criterion:              θ_min = 1.22 λ / D
Brewster's law:                  tan i_p = μ
Malus' law:                      I = I0 cos²θ
```

**Worked example — fringe width.** `λ = 600 nm`, `D = 1.5 m`, `d = 0.3 mm`: `β = 600×10⁻⁹×1.5/0.3×10⁻³ = 3×10⁻³ m = 3 mm`.

**Worked example — single slit.** `a = 0.1 mm`, `λ = 500 nm`, `D = 1 m`: central max width `= 2×500×10⁻⁹×1/10⁻⁴ = 1 cm`.

**Worked example — Brewster.** Glass `μ = 1.5`: `i_p = tan⁻¹ 1.5 = 56.3°`. At this angle the reflected light is fully plane-polarised.

**Worked example — Malus.** Unpolarised light `I0` through a polariser → `I0/2`; through a second analyser at 60° → `(I0/2)·cos²60° = I0/8`.

**Worked example — resolution.** Telescope `D = 0.1 m`, `λ = 550 nm`: `θ = 1.22×550×10⁻⁹/0.1 = 6.7×10⁻⁶ rad`.

---

# PART F — OPTICS

## Chapter 18 — Geometrical Optics

**Key points**
- **Rays** travel in straight lines in a uniform medium. Reflection: angle of incidence = angle of reflection. Refraction: Snell's law.
- **Cartesian sign convention** used in the book: distances measured from the pole/optical centre; **along the incident light = positive**; against it = negative; heights above the axis positive.
- **Total internal reflection** needs light going from denser to rarer medium with angle above the **critical angle** (optical fibres, diamond sparkle).
- **Prism:** deviation depends on angle of incidence and is minimum at symmetric passage.
- **Real image** forms where rays actually meet (can be on a screen); **virtual** where they appear to meet.
- **Lens power** `P = 1/f` in dioptre (f in metres).

**Formulas**

```
Mirror equation:        1/v + 1/u = 1/f = 2/R         (f = R/2)
Magnification:          m = −v/u    (mirror) ;   m = v/u (lens)
Snell's law:            μ1 sin i = μ2 sin r
Critical angle:         sin C = 1/μ  (relative to air) ;  C = sin⁻¹(μ2/μ1)
Apparent depth:         real depth / apparent depth = μ
Prism:                  μ = sin[(A + δ_min)/2] / sin(A/2)
Thin prism:             δ = (μ − 1) A
Single spherical surface: μ2/v − μ1/u = (μ2 − μ1)/R
Thin lens:              1/v − 1/u = 1/f
Lens maker's formula:   1/f = (μ − 1)(1/R1 − 1/R2)
Power:                  P = 1/f (metres) ;  combined lenses in contact: P = P1 + P2
Two thin lenses separated by d:  1/F = 1/f1 + 1/f2 − d/(f1 f2)
```

**Worked example — concave mirror.** `f = −10 cm`, object at `u = −30 cm`:
`1/v = 1/f − 1/u = −1/10 + 1/30 = −2/30 → v = −15 cm`; `m = −v/u = −(−15)/(−30) = −0.5`. **Real, inverted, half-size.**

**Worked example — convex lens.** `f = +20 cm`, `u = −30 cm`: `1/v = 1/20 − 1/30 = 1/60 → v = +60 cm`; `m = v/u = 60/(−30) = −2`. **Real, inverted, twice the size.**

**Worked example — critical angle.** Water (`μ = 1.33`): `C = sin⁻¹(1/1.33) = 48.8°`.

**Worked example — prism.** `A = 60°`, `μ = 1.5`: `sin[(60 + δ)/2] = 1.5 × sin30° = 0.75 → (60 + δ)/2 = 48.6° → δ_min ≈ 37.2°`.

**Worked example — lens maker.** Biconvex `μ = 1.5`, `R1 = +20`, `R2 = −20` cm: `1/f = 0.5×(1/20 + 1/20) = 0.05 → f = 20 cm`.

**Worked example — lens combination.** `+5 D` and `−2 D` in contact → `3 D` → `f = 33.3 cm`.

---

## Chapter 19 — Optical Instruments

**Key points**
- The eye's **near point** is 25 cm (normal), **far point** is at infinity. The lens power is adjusted by the ciliary muscles (accommodation).
- **Angular magnification** compares the angle subtended with and without the instrument.
- **Simple microscope (magnifier):** a convex lens used with the object inside its focal length.
- **Compound microscope:** two lenses (objective of short `f`, eyepiece); magnifications multiply.
- **Telescope** views distant objects: astronomical (inverted image, high magnification), terrestrial (erect).
- **Defects of vision:** myopia (short-sightedness, corrected by *concave* lens), hypermetropia (long-sightedness, corrected by *convex* lens), presbyopia, astigmatism.
- **Resolving power** limited by diffraction (see Ch 17).

**Formulas**

```
Simple microscope:        M = 1 + D/f   (image at near point, D = 25 cm)
                          M = D/f       (image at infinity, relaxed eye)
Compound microscope:      M ≈ (v0/u0)(1 + D/fe) ≈ (L/f0)(D/fe) for long tubes
Astronomical telescope:   M = f0 / fe      (normal adjustment)
                          Tube length L = f0 + fe
Myopia correction:        lens focal length = − (far point distance)
Hypermetropia:            1/f = 1/v − 1/u  with u = −25 cm, v = −(near point)
```

**Worked example — magnifier.** `f = 5 cm`: `M = 1 + 25/5 = 6` (image at near point); `M = 25/5 = 5` (at infinity).

**Worked example — telescope.** `f0 = 100 cm`, `fe = 5 cm`: `M = 20`; tube length `105 cm`.

**Worked example — myopia.** Far point 80 cm → lens `f = −80 cm`, power `= −1.25 D`.

**Worked example — hypermetropia.** Near point 100 cm, want to read at 25 cm: `1/f = −1/100 + 1/25 = 3/100 → f = +33.3 cm`, power `+3 D`.

---

## Chapter 20 — Dispersion and Spectra

**Key points**
- **Dispersion:** splitting of white light into colours because refractive index depends on wavelength (violet bends most, red least).
- **Cauchy's relation:** `μ = A + B/λ²` (normal dispersion).
- **Dispersive power** `ω` measures the spread relative to mean deviation.
- An **achromatic combination** (crown + flint prisms/lenses) removes colour spread while keeping net deviation/power; a **direct-vision** combination removes net deviation but keeps dispersion.
- **Emission spectra** (line, band, continuous) vs **absorption spectra** (dark lines in a continuous background; Fraunhofer lines in sunlight).
- **Spectrometer** measures angles of prisms/deviation.
- **Rainbow:** refraction + total internal reflection inside raindrops. **Primary** bow ≈ 42° (red outside), **secondary** ≈ 51° (colours reversed, fainter).

**Formulas**

```
Thin-prism deviation:      δ = (μ − 1) A
Angular dispersion:        δv − δr = (μv − μr) A
Dispersive power:          ω = (μv − μr)/(μy − 1)
Cauchy's relation:         μ = A + B/λ²
Achromatic doublet (thin lenses in contact):  ω1/f1 + ω2/f2 = 0
Achromatic prism pair:     (μv − μr)₁ A1 = (μv − μr)₂ A2   (prisms placed in opposite sense)
```

**Worked example — dispersive power.** `μv = 1.53`, `μr = 1.51`, `μy = 1.52`: `ω = 0.02/0.52 = 0.038`.

**Worked example — thin prism.** `A = 5°`, `μy = 1.52`: mean deviation `δ = 0.52 × 5° = 2.6°`; violet–red separation `= 0.02 × 5° = 0.1°`.

**Worked example — achromatic lens.** If crown glass has `ω1 = 0.02`, flint `ω2 = 0.04`, then `f2 = −2 f1` (a concave flint lens of twice the focal length) removes colour fringes.

---

## Chapter 21 — Speed of Light

**Key points**
- `c ≈ 3 × 10⁸ m/s` (exactly 299 792 458 m/s by definition of the metre).
- **Römer** first estimated it from delays in Jupiter's moon eclipses (astronomical method).
- Terrestrial methods: **Fizeau** (toothed wheel), **Foucault** (rotating mirror), **Michelson** (rotating octagonal mirror) — each reduces to timing a round trip.
- In a medium of refractive index `n`, speed is `c/n`.
- Nothing can exceed `c` in vacuum (Ch 47 of Volume 2).

**Formulas**

```
Fizeau (N teeth, wheel speed n rev/s, distance d):  c = 4 N n d
Michelson (octagonal mirror, n rev/s, distance d): c = 16 n d
In a medium:                                        v = c/μ
```

**Worked example — Fizeau.** `d = 8633 m`, `N = 720`, first eclipse at `n = 12.6 rev/s`:
`c = 4×720×12.6×8633 = 3.13×10⁸ m/s`.

**Worked example — Michelson.** `d = 35.4 km`, `n = 528 rev/s`: `c = 16×528×35 400 = 2.99×10⁸ m/s`.

**Worked example — in glass.** `μ = 1.5`: `v = 3×10⁸/1.5 = 2×10⁸ m/s`.

---

## Chapter 22 — Photometry

**Key points**
- Photometry measures light *as perceived by the human eye* (radiometry measures energy).
- **Luminous flux** (lumen) = radiant power weighted by eye sensitivity. The book's reference: a **1 W source of 555 nm** (peak sensitivity) emits **685 lumen**.
- **Luminosity (relative)** falls off on both sides of 555 nm; it is ~0.6 at 600 nm.
- **Luminous intensity** (candela) = flux per unit solid angle. A point source's flux is spread over `4π` sr.
- **Illuminance** (lux) = flux per unit area on a surface.
- **Inverse-square law** and **Lambert's cosine law** govern illuminance from a point source.
- **Luminous efficiency** = lumen per watt.

**Formulas**

```
Luminous flux:           Φ  (lumen) ;  1 W at 555 nm = 685 lm
Flux of a source of power P and relative luminosity L:  Φ = 685 · L · P
Luminous intensity:      I = Φ / ω  (candela = lumen/steradian)
Isotropic source:        Φ_total = 4π I
Illuminance:             E = Φ / A  (lux = lumen/m²)
Inverse-square law:      E = I / r²
Lambert's cosine law:    E = I cosθ / r²   (θ from surface normal)
Luminous efficiency:     η = Φ / P  (lm/W)
```

**Worked example — from the book.** A 10 W source at 600 nm (relative luminosity 0.6): `Φ = 0.6 × 685 × 10 = 4110 lumen`.

**Worked example — illuminance.** 100 cd source, 2 m directly above: `E = 100/4 = 25 lux`. If the light falls on the surface at `θ = 60°` from the normal: `E = 100×0.5/4 = 12.5 lux`.

**Worked example — total flux.** `I = 100 cd` isotropic → `Φ = 4π × 100 = 1257 lm`.

---

# APPENDIX — Reference

## Universal constants (from the book's Appendix B)

| Quantity | Symbol | Value |
|---|---|---|
| Constant of gravitation | G | 6.67259 × 10⁻¹¹ N·m²/kg² |
| Speed of light in vacuum | c | 2.99792458 × 10⁸ m/s (exact) |
| Avogadro constant | N_A | 6.0221367 × 10²³ mol⁻¹ |
| Gas constant | R | 8.314510 J/K·mol |
| Boltzmann constant | k | 1.380658 × 10⁻²³ J/K |
| Stefan–Boltzmann constant | σ | 5.67051 × 10⁻⁸ W/m²·K⁴ |
| Wien's constant | b | 2.897756 × 10⁻³ m·K |
| Charge of proton | e | 1.602 × 10⁻¹⁹ C |
| Mass of electron | m_e | 9.109 × 10⁻³¹ kg |
| Mass of proton | m_p | 1.6726 × 10⁻²⁷ kg |
| Mass of neutron | m_n | 1.6749 × 10⁻²⁷ kg |
| Permeability of vacuum | μ0 | 4π × 10⁻⁷ T·m/A |
| Permittivity of vacuum | ε0 | 8.854 × 10⁻¹² C²/N·m² |
| Faraday constant | F | 96 485 C/mol |
| Planck constant | h | 6.626 × 10⁻³⁴ J·s = 4.136 × 10⁻¹⁵ eV·s |
| Rydberg constant | R | 1.0974 × 10⁷ m⁻¹ |
| Bohr radius | a0 | 5.29 × 10⁻¹¹ m |

(Some exponents in the PDF's Appendix B text come out wrong in the extracted text, e.g. the proton charge and Wien's constant; the values above are the standard, correct ones.)

**Astronomical:** mass of Sun 1.99 × 10³⁰ kg · radius of Sun 6.95 × 10⁸ m · mass of Earth 5.98 × 10²⁴ kg · radius of Earth 6.37 × 10⁶ m · mass of Moon 7.36 × 10²² kg · Earth–Sun distance 1.50 × 10¹¹ m · Earth–Moon distance 3.84 × 10⁸ m · escape speed from Earth 11.2 km/s · from Moon 2.38 km/s.

## Common mistakes to avoid

1. **Mixing units** (cm with m, grams with kg). Convert first, then substitute.
2. **Using constant-acceleration formulas** when `a` varies.
3. **Treating the third-law pair as cancelling** — they act on *different* bodies.
4. **Forgetting `g` convention** in a problem (10 vs 9.8) — use what the question states.
5. **Sign convention in optics:** use the Cartesian convention consistently; `u` is usually negative for a real object.
6. **Centripetal force drawn as an extra force** on the FBD — it is the *result* of other forces.
7. **Pendulum/spring formulas** apply to *small* oscillations; the spring period does not depend on `g` or amplitude.
8. **Decibel arithmetic** — it is logarithmic: 10× intensity = +10 dB, not 10× the dB value.
9. **Dimensional check** every final formula; if the dimensions are wrong, the formula is wrong.

---
*How these notes were made: from the chapter and section list of `physics-book-1.pdf` (Concepts of Physics, Vol. 1), with the standard formulas for each topic and a few facts spot-checked against the book's text (the 685 lm/W luminous flux example, the constants appendix, the section titles). The book's own full derivations and its exercise problems are not reproduced here. Every worked example was recomputed independently; use them as practice and compare with the book's treatment.*
