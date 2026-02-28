# Milk Bank Logistics Optimization: Inventory Routing Problem (IRP)

This project optimizes milk collection routes for a milk bank logistics system using an Inventory Routing Problem (IRP) optimization model. The system determines optimal daily routes for a single driver to collect milk from multiple depots while minimizing operational costs.

> This is a group project, where I'm responsible for all the code part.

## Project Overview

The optimization model addresses the following challenge:

- **Single driver** with maximum **12 hours (720 minutes)** working time per day
- **Single driver** with a company policy maximum **12 hours (720 minutes)** working time per day, but daily route plans are built to a **660-minute (11-hour) operating cap** to leave buffer for traffic and unexpected delays
- Multiple depots with varying daily milk volumes
- Need to balance inventory levels, travel time, and operational costs
- Determine which depots should use "Shipping" vs "Truck" collection based on distance/time constraints

## Key Features

- **2025 Forecast Generation**: Creates realistic forecast data from 2024 base data with variability
- **Depot Classification**: Automatically classifies depots as "Shipping" or "Truck Candidate" based on:
  - Traffic safety buffer (max 660 minutes task time)
  - ROI efficiency (distance vs annual volume)
- **Rolling Horizon Optimization**: Solves IRP day-by-day over a 20-day run with safety triggers (inventory threshold and a maximum “days since last pickup” guardrail)
- **Cost Minimization**: Optimizes driver wages and fuel costs

## Project Structure

```
530-Case-Study/
├── data/
│   ├── raw/
│   │   ├── Deposits_Trans_2023_2024.xlsx
│   │   ├── Depot_Information.xlsx
│   │   └── Optional_Driving_Distance_and_Time.xlsx
│   │
│   └── processed/
│       ├── depot_mapping.csv
│       ├── depot_service_strategy.csv
│       ├── final_inventory_log.csv
│       ├── final_route_plan.csv
│       ├── forecast_2025.csv
│       ├── forecast_2025_truck_only.csv
│       ├── ready_forecast_data.csv
│       └── ready_network_data.csv
│
├── notebooks/
│   ├── 01_Data_Exp.ipynb
│   ├── 02_Data_Prep.ipynb
│   └── 03_Optimization_Model.ipynb
│
├── scripts/
│   └── create_2025_forecast.py
│
├── .gitignore
├── README.md
└── requirements.txt
```

## Workflow

### Step 1: Generate 2025 Forecast

```bash
python scripts/create_2025_forecast.py
```

- Filters 2024 data
- Shifts dates to 2025 (handles leap year)
- Adds variability (0.95-1.15 multiplier)
- Outputs: `data/processed/forecast_2025.csv`

### Step 2: Data Exploration & Depot Classification

Run `notebooks/01_Data_Exp.ipynb`:

- Identifies hub location (Milk Bank)
- Calculates round trip times for each depot
- Applies filtering rules:
  - **Traffic Buffer Rule**: If total task time > 660 min → Shipping
  - **ROI Efficiency Rule**: If round trip > 300 min AND volume < 2000 oz → Shipping
- Outputs: `depot_service_strategy.csv`, `forecast_2025_truck_only.csv`

### Step 3: Data Preparation

Run `notebooks/02_Data_Prep.ipynb`:

- Maps depot names to IDs
- Converts distance/time matrices to standard format
- Filters to truck candidate nodes only
- Formats forecast data with Day_Index
- Outputs: `ready_network_data.csv`, `ready_forecast_data.csv`, `depot_mapping.csv`

### Step 4: Optimization Model

Run `notebooks/03_Optimization_Model.ipynb`:

- Implements IRP model using Pyomo
- Runs day-by-day over 20 days (pilot horizon)
- Safety triggers:
  - Force visit if projected inventory would exceed **850 oz**
  - Force visit if a depot has not been picked up in roughly **5 months (150 days)** (operational shelf-life guardrail)
- Minimizes operational costs (wages + fuel)
- Outputs: `final_inventory_log.csv`, `final_route_plan.csv`

## Installation

1. **Clone the repository**

```bash
git clone https://github.com/hanfuzhao/530-Case-Study.git
cd 530-Case-Study
```

2. **Create a virtual environment** (recommended)

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

4. **Install GLPK solver** (required for Pyomo)
   - **macOS**: `brew install glpk`
   - **Linux**: `sudo apt-get install glpk-utils`
   - **Windows**: Download from [GLPK website](https://www.gnu.org/software/glpk/)

## Usage

### Quick Start

1. **Generate forecast data**:

   ```bash
   python scripts/create_2025_forecast.py
   ```
2. **Run notebooks in order**:

   - Open `notebooks/01_Data_Exp.ipynb` and run all cells
   - Open `notebooks/02_Data_Prep.ipynb` and run all cells
   - Open `notebooks/03_Optimization_Model.ipynb` and run all cells

### Input Data Requirements

Place your raw data files in `data/raw/`:

- `Deposits_Trans_2023_2024.xlsx`: Historical transaction data
- `Optional_Driving_Distance_and_Time.xlsx`: Distance and time matrix between locations
- `Depot_Information.xlsx`: Depot metadata (optional)

## Model Details

### Objective Function

Minimize total operational costs:

- Driver wages: $36/hour
- Fuel costs: $0.70/mile

### Constraints

- **Inventory Balance**: `I[i,t] = I[i,t-1] + q[i,t] - d[i,t]`
- **Capacity Limits**: Max 1000 oz per depot
- **Time Limits**: Max 660 minutes per day (11 hours + buffer vs 12-hour policy limit)
- **Flow Conservation**: Routes must start/end at hub
- **Subtour Elimination**: MTZ formulation

### Safety Trigger

If inventory at any depot exceeds 850 oz, the depot must be visited on that day.

## Output Files

- **`depot_service_strategy.csv`**: Classification of each depot (Shipping vs Truck Candidate) with reasons
- **`forecast_2025_truck_only.csv`**: Daily forecast volumes for truck candidate depots only
- **`ready_network_data.csv`**: Network graph with distances and travel times
- **`ready_forecast_data.csv`**: Standardized forecast data for optimization
- **`final_inventory_log.csv`**: Daily inventory levels for each depot
- **`final_route_plan.csv`**: Optimized daily routes

## Dependencies

See `requirements.txt` for full list. Key packages:

- `pandas`: Data manipulation
- `numpy`: Numerical operations
- `pyomo`: Optimization modeling
- `openpyxl`: Excel file reading

## Solver

This project uses **GLPK** (GNU Linear Programming Kit) solver. Make sure GLPK is installed and accessible in your PATH.

