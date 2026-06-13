# Shipping Route Optimizer

> **Accurate results without lying to ourselves**

A transparent shipping analytics and voyage decision-support platform built with Python and Streamlit.

This project began as a route optimizer using Dijkstra, A* and brute-force validation, but has now expanded into a broader commercial shipping platform covering route optimization, voyage economics, vessel selection, speed optimization, fleet allocation, congestion, laytime, stowage and chartering decision support.

---

## Project Purpose

The goal of this project is to model realistic shipping decisions using simple, auditable logic.

It is designed to help answer questions such as:

* What is the optimal route between two ports?
* Do Dijkstra, A* and brute-force validation agree?
* What is the total voyage cost?
* Is the voyage profitable?
* What is the estimated TCE?
* Which vessel is best suited to the cargo?
* What speed produces the best profit or TCE?
* How do port congestion, demurrage and dispatch affect the result?
* Can the cargo be stowed within basic weight and volume limits?
* Which cargo-vessel combination is commercially attractive?

---

## Core Philosophy

This project prioritizes:

* Transparent calculations
* Simple logic before complex optimization
* Validation before scaling
* Clear assumptions
* No black-box modelling
* No pretending uncertain estimates are exact

> The objective is not to make the result look impressive.
> The objective is to understand when the result can be trusted.

---

## Current Features

### 1. Route Optimization

The routing engine calculates optimal port-to-port routes using:

* Dijkstra shortest path
* A* search
* Brute-force validation

The system compares all three methods where practical to check whether the result is consistent.

---

### 2. Multi-Constraint Route Cost Model

Each route leg is evaluated using:

```text
total_cost =
fuel_cost
+ canal_fee
+ weather_risk
+ piracy_risk
+ carbon_cost
```

Each leg can be inspected so users can see exactly where the route cost comes from.

---

### 3. Algorithm Validation

The app includes validation pages that compare:

* Dijkstra vs A*
* Dijkstra vs Brute Force
* Route agreement
* Cost agreement
* Random route tests
* Real-world route tests
* Conclusion matrix

This supports the project motto:

> Accurate results without lying to ourselves.

---

### 4. Route Visualization

The route visualizer shows:

* Selected route
* Route cost
* Route leg details
* Network graph
* Highlighted optimal route

---

### 5. Voyage Economics Engine

The voyage economics engine calculates:

* Distance
* Sea days
* Fuel consumed
* Fuel cost
* Port costs
* Transit costs
* Route costs
* Revenue
* Voyage cost
* Voyage profit
* TCE

Formula:

```text
Revenue =
cargo tonnes × freight rate × freight premium
```

```text
TCE =
voyage profit ÷ total voyage days
```

---

### 6. Speed Optimizer

The speed optimizer tests multiple vessel speeds and calculates:

* Sea days
* Fuel burn
* Fuel cost
* Voyage profit
* TCE

It uses a speed/fuel curve:

```text
fuel_burn_at_speed =
base_fuel_burn × (speed / base_speed) ^ exponent
```

This reflects the real-world concept that fuel consumption rises sharply as speed increases.

---

### 7. Vessel Profiles

The project includes a vessel profile dataset with representative vessel classes such as:

* Handysize
* Supramax
* Ultramax
* Panamax
* Kamsarmax
* Post-Panamax
* Capesize
* Newcastlemax
* VLCC
* ULCC

Each vessel includes:

* Vessel name
* Vessel type
* DWT
* Reference speed
* Fuel burn
* Cargo capacity

---

### 8. Vessel Selector

The vessel selector recommends a vessel class based on the actual fleet data.

It calculates:

* Matching vessels
* Smallest suitable vessel
* Cargo utilization
* Capacity fit
* Manual vessel assessment

---

### 9. Vessel Availability

The vessel availability page considers:

* Vessel current port
* Load port
* Available days
* Positioning distance
* Positioning days
* Daily hire cost
* Positioning hire cost

It ranks vessels by practical availability.

---

### 10. Laytime Calculator

The laytime calculator models:

* Allowed laytime
* Actual laytime
* Demurrage
* Dispatch
* Adjusted profit
* Adjusted TCE

This reflects one of the most important commercial risks in voyage profitability.

---

### 11. Fleet Optimizer

The fleet optimizer assigns cargoes to vessels using transparent logic.

Current assignment logic:

1. Process largest cargoes first
2. Find vessels with enough cargo capacity
3. Rank by:

   * smallest excess capacity
   * earliest availability
   * lowest daily hire cost
4. Assign one vessel per cargo
5. Remove assigned vessel from available fleet

Outputs include:

* Fleet assignments
* Unassigned cargoes
* Idle vessels
* Commodity summary
* Total revenue
* Average utilization
* Fleet utilization

---

### 12. Stowage Planner

The stowage planner performs a simplified stowage feasibility check.

It calculates:

* Cargo volume
* Stowage factor
* Hold volume
* Hold weight capacity
* Volume utilization
* Weight utilization
* Basic hold allocation
* Stowage warnings

It currently does not calculate trim, stability, shear force or bending moments.

---

### 13. Port Congestion Engine

The port congestion page models:

* Delay days
* Congestion level
* Berth utilization
* Waiting risk score
* TCE impact

This allows congestion to be included in voyage decision-making.

---

### 14. Demurrage / Dispatch Optimizer

This page combines voyage economics with laytime outcomes.

It calculates:

* Base voyage profit
* Base TCE
* Laytime difference
* Demurrage cost
* Dispatch credit
* Adjusted profit
* Adjusted TCE

---

### 15. Chartering Desk

The chartering desk ranks vessel options for a selected cargo.

It considers:

* Cargo size
* Vessel capacity
* Vessel current port
* Positioning route
* Voyage route
* Port congestion
* Voyage economics
* Positioning hire cost
* Net profit
* Net TCE

It produces a commercial recommendation:

```text
FIX / ACCEPT CARGO
MARGINAL — REVIEW ASSUMPTIONS
DO NOT FIX
```

---

### 16. Market Freight Engine

The market freight engine estimates freight premiums based on:

* Vessel scarcity
* Cargo urgency
* Market sentiment
* Port congestion
* Manual adjustment

It outputs:

* Suggested premium
* Suggested freight rate
* Base revenue
* Suggested revenue
* Pricing explanation

---

### 17. Fleet P&L Dashboard

The Fleet P&L Dashboard estimates:

* Assigned cargoes
* Revenue
* Voyage cost
* Hire cost
* Net profit
* Net TCE
* Fleet TCE
* Total fleet profit

---

### 18. Master Shipping Dashboard

The master dashboard combines the main project modules into one workflow:

* Cargo selection
* Vessel recommendation
* Vessel availability
* Route calculation
* Speed optimization
* Port congestion
* Voyage economics
* Laytime impact
* Stowage feasibility
* Final commercial recommendation

---

## App Pages

```text
pages/
├── 1_route_optimizer.py
├── 2_route_visualizer.py
├── 3_algorithm_validation.py
├── 4_voyage_economics.py
├── 5_conclusion_matrix.py
├── 6_speed_optimizer.py
├── 7_vessel_selector.py
├── 8_vessel_availability.py
├── 9_laytime_calculator.py
├── 10_fleet_optimizer.py
├── 11_stowage_planner.py
├── 12_port_congestion.py
├── 13_demurrage_dispatch_optimizer.py
├── 14_chartering_desk.py
├── 15_market_freight_engine.py
├── 16_fleet_pnl_dashboard.py
├── 99_shipping_dashboard.py
```

---

## Project Structure

```text
shipping-route-optimizer/
├── app_shipping.py
├── pages/
├── optimizer/
│   ├── dijkstra.py
│   ├── astar.py
│   ├── brute_force.py
│   ├── cost_model.py
│   └── route_generator.py
├── economics/
│   ├── voyage_economics.py
│   ├── speed_fuel_model.py
│   └── vessel_profiles.py
├── data/
│   ├── generated_routes.csv
│   ├── global_ports.csv
│   ├── vessels.csv
│   ├── vessel_positions.csv
│   ├── cargoes.csv
│   ├── cargo_stowage_factors.csv
│   └── port_congestion.csv
├── docs/
│   └── accuracy_policy.md
├── requirements.txt
├── README.md
└── LICENSE
```

---

## Example Commercial Workflow

A user can:

1. Select a cargo, such as Iron Ore or Wheat
2. Select or auto-rank suitable vessels
3. Calculate the route
4. Estimate distance and sea days
5. Apply fuel price and port costs
6. Include congestion days
7. Check demurrage or dispatch
8. Check basic stowage feasibility
9. Compare vessel/speed combinations
10. Receive a final commercial recommendation

---

## Datasets

The project uses transparent CSV-based datasets:

### Routes

```text
generated_routes.csv
```

Includes:

* Origin port
* Destination port
* Distance
* Fuel cost estimate
* Canal fee
* Weather risk
* Piracy risk
* Carbon cost

### Vessels

```text
vessels.csv
```

Includes:

* Vessel name
* Vessel type
* DWT
* Speed
* Fuel burn
* Cargo capacity

### Vessel Positions

```text
vessel_positions.csv
```

Includes:

* Current port
* Available days
* Daily hire cost

### Cargoes

```text
cargoes.csv
```

Includes realistic dry bulk cargoes such as:

* Iron Ore
* Iron Ore Fines
* Thermal Coal
* Metallurgical Coal
* Wheat
* Corn
* Soybeans
* Barley
* Bauxite
* Alumina
* Fertilizer
* Cement Clinker
* Petroleum Coke
* Salt
* Steel Products

### Stowage Factors

```text
cargo_stowage_factors.csv
```

Includes estimated cargo volume per tonne.

### Port Congestion

```text
port_congestion.csv
```

Includes:

* Delay days
* Congestion level
* Berth utilization
* Waiting risk score

---

## Installation

Clone the repository:

```bash
git clone https://github.com/YOUR-USERNAME/shipping-route-optimizer.git
cd shipping-route-optimizer
```

Create and activate a virtual environment:

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

Mac/Linux:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## Run the App

```bash
streamlit run app_shipping.py
```

Or, if using the original entry point:

```bash
streamlit run app/frontend.py
```

---

## Accuracy Policy

This project is designed for transparent modelling, not hidden optimization.

Important limitations:

* Route costs are estimates
* Port congestion is manually modelled
* Fuel burn uses simplified assumptions
* Stowage is not a certified naval architecture calculation
* Laytime does not yet model full charter-party complexity
* Market freight pricing is rule-based, not live market data
* AIS, live bunker prices and live weather routing are not yet integrated

See:

```text
docs/accuracy_policy.md
```

---

## Current Limitations

The project does not yet include:

* Live AIS vessel tracking
* Live bunker prices
* Live port congestion feeds
* Weather routing
* Real canal tariff tables
* Certified stability calculations
* Shear force or bending moment calculations
* Charter-party legal logic
* Real freight index integration
* Mathematical fleet optimization

---

## Roadmap

### Near-Term

* Integrate the master dashboard more tightly with all submodules
* Improve vessel positioning economics
* Add draft calculator
* Add cargo laycan windows
* Improve Fleet Optimizer V2 with profit-based scoring

### Medium-Term

* Market route benchmarks
* Freight rate index assumptions
* Port-specific cost tables
* Route-specific canal fee model
* Positioning fuel cost
* Multi-cargo scheduling
* Fleet utilization dashboard

### Long-Term

* AIS integration
* Live bunker prices
* Live congestion data
* Weather routing
* Fleet digital twin
* Optimization solver integration
* Commercial chartering simulator

---

## License

This project is licensed under the MIT License.

---

## Project Motto

> **Accurate results without lying to ourselves**
