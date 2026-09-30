# Agastya: Mathematical and Physics Formulation

## 1. Overview
Agastya (Quantum-Inspired Green Fleet Optimizer) models vessel propulsion, lifecycle fuel emissions, port operational dynamics, and combinatorial fleet deployment using physics-grounded equations and quantum-inspired multi-objective evolutionary optimization.

---

## 2. Fuel Consumption Physics Model

### 2.1 Propulsion Power and Speed Relation
Traditional maritime models assume an idealized cubic power-speed law ($P \propto v^3$). In real operational hydrodynamics, hull form coefficients, wave-making resistance, and propulsion efficiency dictate an empirical exponent $n$ that varies by vessel type:

$$P_{propulsion}(v, \Delta) = c_{hull} \cdot \left(\frac{\Delta}{\Delta_{design}}\right)^{2/3} \cdot v^n$$

Where:
- $v$: Vessel speed through water (knots).
- $\Delta$: Operational displacement (tonnes), dynamically determined from deadweight cargo load $m_{cargo}$ and ballast displacement $\Delta_{light}$.
- $\Delta_{design}$: Fully laden design displacement.
- $n$: Vessel-specific velocity exponent ($n \approx 3.2 - 3.5$ for high-speed container vessels, $n \approx 2.8 - 3.1$ for full-form bulk carriers and tankers).
- $c_{hull}$: Vessel resistance coefficient.

### 2.2 Low and High Speed Hydrodynamic Clamping
The power-speed polynomial relation degrades outside the design Froude number range ($Fn \approx 0.14 - 0.28$):
- **Very Low Speeds ($v < v_{min} \approx 6.0$ knots)**: Main engine operating below minimum thermal stability; specific fuel consumption sharply increases, and auxiliary steering power dominates. Clamped to minimum safe maneuverability threshold.
- **Very High Speeds ($v > v_{max}$)**: Wave-making resistance increases exponentially due to bow and stern wave interference. Clamped to rated Maximum Continuous Rating (MCR) engine power limit $P_{MCR}$.

$$\tilde{v} = \mathrm{clip}(v, v_{min}, v_{max})$$

### 2.3 Part-Load Specific Fuel Oil Consumption (SFOC)
Engine thermal efficiency varies non-linearly with engine load $L = P_{propulsion} / P_{MCR}$. Internal combustion marine engines are tuned for optimal efficiency around $70\% - 85\%$ MCR:

$$SFOC(L) = SFOC_{base} \cdot \left(1.0 + a_{sfoc} \cdot (L - L_{opt})^2 + \delta_{low\_load}(L)\right)$$

Where:
- $L_{opt} = 0.75$ (optimal engine load fraction).
- $a_{sfoc} \approx 0.35$ (parabolic curvature factor).
- $\delta_{low\_load}(L) = \max\left(0, 0.20 \cdot (0.35 - L)\right)$ captures auxiliary blower activation and incomplete cylinder combustion below $35\%$ load.

### 2.4 Environmental Resistance (Sea State & Weather)
Added resistance in waves and wind is parameterized using the Douglas / Beaufort scale ($B \in [0, 12]$):

$$f_{weather}(B) = 1.0 + k_w \cdot B^2$$

For severe sea states ($B \ge 8$, gale to storm force), added resistance escalates drastically:

$$f_{weather}(B) = \min\left(1.0 + k_w \cdot B^2 + 0.05 \cdot (B - 7)^3,\; 2.50\right)$$

### 2.5 Hull Fouling Degradation
Biofouling increases surface roughness over the inter-docking period $t_{drydock}$ (months since last drydock):

$$f_{fouling}(t_{drydock}) = 1.0 + k_{foul} \cdot \left(\frac{t_{drydock}}{60}\right)^{1.4}$$

### 2.6 Daily Fuel Consumption Rate
Total daily main engine fuel consumption (metric tonnes per day) is computed as:

$$\dot{m}_{fuel} = \frac{P_{propulsion}(\tilde{v}, \Delta) \cdot f_{weather}(B) \cdot f_{fouling}(t_{drydock}) \cdot SFOC(L) \cdot 24}{10^6 \cdot \eta_{shaft}}$$

---

## 3. Alternative Fuel Lifecycle (Well-to-Wake)

### 3.1 Well-to-Wake GHG Architecture
Total lifecycle emissions include upstream extraction, refining, production, bunkering losses (Well-to-Tank, WTT) and onboard combustion plus exhaust slip (Tank-to-Wake, TTW):

$$GHG_{WTW} = GHG_{WTT} + GHG_{TTW}$$

$$\text{Intensity}_{WTW} \; [g\mathrm{CO}_2\mathrm{e}/\mathrm{MJ}] = \text{Factor}_{WTT} + \text{Factor}_{TTW}$$

### 3.2 Dual-Fuel Pilot Combustion
Alternative fuels (LNG, Methanol, Ammonia, Hydrogen) with compression ignition require a pilot fuel injection (typically MGO / VLSFO) accounting for $\xi_{pilot} \approx 3\% - 5\%$ of total energy:

$$E_{total} = E_{alt} \cdot (1 - \xi_{pilot}) + E_{pilot} \cdot \xi_{pilot}$$

### 3.3 Methane and Nitrous Oxide Slip
- **LNG (Methane Slip)**: Low-pressure dual-fuel (LPDF) Otto-cycle engines release unburned methane ($\mathrm{CH}_4$). Over a 100-year horizon, $GWP_{\mathrm{CH}_4} = 28$:
  $$GHG_{slip,\mathrm{CH}_4} = m_{LNG} \cdot s_{\mathrm{CH}_4} \cdot GWP_{\mathrm{CH}_4}$$
- **Ammonia ($\mathrm{N}_2\mathrm{O}$ Slip)**: Ammonia combustion can produce unreacted nitrous oxide ($\mathrm{N}_2\mathrm{O}$), with $GWP_{\mathrm{N}_2\mathrm{O}} = 273$:
  $$GHG_{slip,\mathrm{N}_2\mathrm{O}} = m_{NH_3} \cdot s_{\mathrm{N}_2\mathrm{O}} \cdot GWP_{\mathrm{N}_2\mathrm{O}}$$

### 3.4 Cryogenic Boil-Off Gas (BOG)
For cryogenic fuels (LNG at $-162^\circ\mathrm{C}$, Liquid $\mathrm{H}_2$ at $-253^\circ\mathrm{C}$, Liquid $\mathrm{NH}_3$ at $-33^\circ\mathrm{C}$), daily boil-off rate $r_{BOG}$ contributes to operational loss:

$$m_{bog} = m_{bunker} \cdot r_{BOG} \cdot t_{voyage}$$

Re-liquefaction or auxiliary gas utilization reduces venting to atmosphere.

### 3.5 Cold Ironing (Onshore Power Supply, OPS)
At berth, auxiliary diesel generators can be replaced by shore power:

$$GHG_{berth} = P_{aux} \cdot t_{berth} \cdot CI_{grid}(port)$$

Where $CI_{grid}$ is the local regional electrical grid carbon intensity ($\mathrm{gCO}_2\mathrm{e}/\mathrm{kWh}$).

---

## 4. Multi-Objective Fleet Optimization Formulation

### 4.1 Decision Vector
For a fleet with $M$ available slots operating over route network $R$:

$$\mathbf{x} = \left[ \{VesselType_k, N_{vessels,k}, v_{k}, Fuel_k, ShorePower_{k,p}\} \right]_{k=1}^M$$

### 4.2 Objective Functions
Minimize simultaneously:
1. **Total Fuel Consumption ($F_1$)**:
   $$f_1(\mathbf{x}) = \sum_{k=1}^M \sum_{leg \in R} m_{fuel, k, leg}$$
2. **Total Operating Cost ($F_2$)**:
   $$f_2(\mathbf{x}) = \sum_{k=1}^M \left( C_{fuel, k} + C_{carbon, k} + C_{shore, k} + C_{opex, k} + C_{pilot, k} \right)$$
   Where $C_{carbon} = GHG_{total} \cdot P_{carbon}$ ($P_{carbon} \in [\$0, \$300] / \text{tCO}_2\text{e}$).
3. **Lifecycle Well-to-Wake Emissions ($F_3$)**:
   $$f_3(\mathbf{x}) = \sum_{k=1}^M GHG_{WTW, k}$$

### 4.3 Constraints
1. **Cargo Demand**:
   $$\sum_{k=1}^M Capacity_k \cdot Trips_k(\mathbf{x}) \ge D_{required}$$
2. **Schedule Reliability & Transit Windows**:
   $$T_{transit, k} + T_{port, k} \le T_{deadline, k} - T_{weather\_buffer}$$
3. **Port Bunkering Fuel Availability**:
   $$FuelAvailability(Port_p, Fuel_k) = 1 \quad \forall p \in Ports_k$$
4. **Shore Power Grid Compatibility**:
   $$ShorePower_{k,p} \le PortShoreReadiness(Port_p)$$
5. **Fleet Emission Cap**:
   $$\sum_{k=1}^M GHG_{WTW, k} \le Cap_{GHG}$$

---

## 5. Quantum-Inspired Metaheuristics

### 5.1 Q-Bit Representation
Each discrete decision variable is encoded using a vector of quantum bits (Q-bits):

$$\mathbf{q}_j = \begin{bmatrix} \alpha_j \\ \beta_j \end{bmatrix} = \begin{bmatrix} \cos(\theta_j) \\ \sin(\theta_j) \end{bmatrix}$$

Subject to normalization $|\alpha_j|^2 + |\beta_j|^2 = 1$. The state $|\psi_j\rangle = \alpha_j|0\rangle + \beta_j|1\rangle$ defines the probability $|\beta_j|^2$ of observing state $1$.

### 5.2 Quantum Rotation Gate Update
Q-bits are updated via the unitary quantum rotation operator $U(\Delta\theta_j)$:

$$\begin{bmatrix} \alpha_j(t+1) \\ \beta_j(t+1) \end{bmatrix} = \begin{bmatrix} \cos\Delta\theta_j & -\sin\Delta\theta_j \\ \sin\Delta\theta_j & \cos\Delta\theta_j \end{bmatrix} \begin{bmatrix} \alpha_j(t) \\ \beta_j(t) \end{bmatrix}$$

The rotation magnitude and sign $\Delta\theta_j = s(\alpha_j, \beta_j) \cdot \Delta\theta_0$ steer the probability towards the corresponding bit in the non-dominated Pareto archive.

### 5.3 Catastrophe ($H_\epsilon$) Operator
To avoid premature quantum convergence when $|\alpha_j|^2 \to 0$ or $|\beta_j|^2 \to 0$, if diversity falls below threshold $\delta_{div}$, an $H_\epsilon$ gate resets angles toward the maximum superposition state $\theta = \pi/4$:

$$\theta_j \leftarrow \theta_j \cdot (1 - \epsilon) + \frac{\pi}{4} \cdot \epsilon$$

### 5.4 Quantum-Behaved Particle Swarm Optimization (QI-PSO)
In QI-PSO, particles move in a delta-potential well centered at the local attractor $p_{i,d}$:

$$p_{i,d} = \phi \cdot pbest_{i,d} + (1 - \phi) \cdot gbest_d, \quad \phi \sim U(0, 1)$$

Position update:

$$x_{i,d}(t+1) = p_{i,d} \pm \beta_{contraction} \cdot |mbest_d - x_{i,d}(t)| \cdot \ln(1 / u)$$

Where $mbest = \frac{1}{N} \sum_{i=1}^N pbest_i$ is the mean best position across the swarm, and $u \sim U(0, 1)$.

---

## 6. Algorithmic Performance Metrics
- **Hypervolume ($HV$)**: Volume in objective space dominated by Pareto front $P^*$ bounded by reference point $\mathbf{r}_{ref}$:
  $$HV(P^*, \mathbf{r}_{ref}) = \Lambda\left( \bigcup_{\mathbf{y} \in P^*} [\mathbf{y}, \mathbf{r}_{ref}] \right)$$
- **Spacing / Spread Metric ($S$)**: Uniformity of distribution of non-dominated vectors:
  $$S = \sqrt{\frac{1}{|P^*| - 1} \sum_{i=1}^{|P^*|} (d_i - \bar{d})^2}$$
