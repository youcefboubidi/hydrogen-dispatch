"""
High-fidelity PySAM model of the PV source in the ETAP 'electrolyzer-demo'
Load Flow study (scenarios: SUNNY, PV_EXPORT, NIGHT).

WHAT THE ETAP SUMMARIES ACTUALLY CONSTRAIN
------------------------------------------
These are Load Flow summary reports, not PV-design reports. The only PV fact
they pin down is the AC output at the point of interconnection:

  * SUNNY / PV_EXPORT : PV source (non-swing bus) = 0.5342467 MW at 100% PF,
                        on the 0.415 kV secondary bus (~743 A), stepped up by a
                        2 MVA transformer (T1) to the 11 kV main bus.
  * PV_EXPORT         : grid swing bus goes negative / leading PF -> the array
                        is back-feeding (exporting) to the grid.
  * NIGHT             : PV source = 0 (dark); grid carries the full ~0.8 MW
                        electrolyzer (motor) load.

  => Your real PV interconnect is ~534 kW AC at unity power factor.

The previous version of this script modelled ~24 MW DC (43,624 x 550 W), which
is ~45x larger than the ETAP setup. The sizing below is corrected to ~534 kW AC.

WHAT THESE FILES DO *NOT* CONTAIN
---------------------------------
A load-flow report has no module count, inverter model, tracking mode, tilt,
azimuth, GCR, or site location. Those values below are RETAINED ASSUMPTIONS
(your original geometry choices, kept as-is). Confirm them against your array
design / PVsyst model -- they are NOT derived from the ETAP summaries.
"""

import PySAM.Pvsamv1 as pvsam
import PySAM.ResourceTools as tools
import csv
import sys
from datetime import datetime, timedelta

# 1. Initialize the High-Fidelity PySAM Model
solar_farm = pvsam.default("FlatPlatePVSingleOwner")

# 2. Location (RETAINED ASSUMPTION -- not from ETAP; ignored when embedded
#    weather data below carries its own coordinates, but kept for documentation)
latitude = 32.5873    # Ghardaia, Algeria (overridden by the weather file below)
longitude = 3.7314

# 3. Geometric Array Configuration -- single-axis tracking
#    (RETAINED ASSUMPTIONS -- not derivable from a load-flow report)
solar_farm.SystemDesign.subarray1_track_mode = 1     # 1 = single-axis tracking
solar_farm.SystemDesign.subarray1_tilt = 0
solar_farm.SystemDesign.subarray1_azimuth = 180
solar_farm.SystemDesign.subarray1_backtrack = 1
solar_farm.SystemDesign.subarray1_gcr = 0.35

# 4. Electrical Sizing -- MATCHED TO THE ETAP AC INTERFACE (~534 kW AC)
#    --------------------------------------------------------------------
#    The default CEC module in this configuration is ~530.75 W (Vmp x Imp),
#    NOT 550 W. We read it from the model so the DC nameplate stays
#    self-consistent instead of hard-coding a wattage that disagrees with
#    the module actually being simulated.
cec = solar_farm.CECPerformanceModelWithModuleDatabase
module_watt = cec.cec_v_mp_ref * cec.cec_i_mp_ref          # ~530.75 W

TARGET_AC_KW = 534.2467          # 0.5342467 MW from ETAP, at 100% PF
DC_AC_RATIO = 1.25               # typical for single-axis tracking

modules_per_string = 28
# Size the string count to hit ~534 kW AC at the chosen DC/AC ratio:
target_dc_kw = TARGET_AC_KW * DC_AC_RATIO
nstrings = round(target_dc_kw * 1000 / (module_watt * modules_per_string))  # -> 45
system_capacity_kw = nstrings * modules_per_string * module_watt / 1000      # ~668.7 kWdc

solar_farm.SystemDesign.subarray1_modules_per_string = modules_per_string
solar_farm.SystemDesign.subarray1_nstrings = nstrings
solar_farm.SystemDesign.system_capacity = system_capacity_kw

# Inverter: one unit sized to the ETAP AC rating (the default 2.5 MW Sandia
# inverter would be ~5x oversized for 534 kW and run badly at part load).
# Use the datasheet/single-point inverter model so we can set the AC nameplate.
solar_farm.SystemDesign.inverter_count = 1
inv = solar_farm.Inverter
inv.inverter_model = 1                       # 1 = inverter datasheet model
inv.inv_ds_paco = TARGET_AC_KW * 1000        # AC nameplate, W  (= 534,246.7 W)
inv.inv_ds_eff = 98.0                         # nominal efficiency, %
inv.mppt_low_inverter = 200                   # MPPT window low, V
inv.mppt_hi_inverter = 1000                   # MPPT window high, V

solar_farm.Lifetime.system_use_lifetime_output = 0

print(f"Module power (from model): {module_watt:.2f} W")
print(f"Array: {nstrings} strings x {modules_per_string} modules "
      f"= {nstrings * modules_per_string} modules")
print(f"DC nameplate: {system_capacity_kw:,.1f} kWdc")
print(f"Inverter AC nameplate: {TARGET_AC_KW:,.2f} kW  (matches ETAP PV source)")
print(f"DC/AC ratio: {system_capacity_kw / TARGET_AC_KW:.2f}\n")

# 5. Ingest the Real Weather Dataset
#    NOTE: solar_resource_data overrides the lat/long set above. Your NSRDB CSV
#    must have the standard header row (Source, Location ID, ..., Latitude,
#    Longitude, Time Zone, Elevation) or SAM_CSV_to_solar_data will reject it.
weather_file_path = "ghardaia_sam_2023_15min.csv"  # CAMS-driven SAM file (upload to Colab)

try:
    solar_data_dict = tools.SAM_CSV_to_solar_data(weather_file_path)
    solar_farm.SolarResource.solar_resource_data = solar_data_dict
    print("Ghardaia weather dataset successfully loaded into memory.")
except FileNotFoundError:
    print(f"Error: Please ensure '{weather_file_path}' is in the directory.")
    sys.exit(1)   # don't fall through to execute() with no resource loaded

# 6. Execute the Simulation
print("Executing simulation...")
solar_farm.execute()

# 7. Extract the Projected Power Production Datasets
annual_energy_kwh = solar_farm.Outputs.annual_energy
print(f"\nProjected Annual Energy Production: {annual_energy_kwh:,.2f} kWh")

capacity_factor = solar_farm.Outputs.capacity_factor
print(f"System Capacity Factor: {capacity_factor:.2f}%")

# Full generation time-series (kW AC)
generation_kw = solar_farm.Outputs.gen

# 8. Export to CSV for Digital Twin Integration
output_csv_path = "ghardaia_solar_generation.csv"

# Derive the timestep from the data length instead of assuming 5 minutes.
# The original script hard-coded 5 min, but `gen` resolution follows the
# weather file: 8760 -> 60 min, 17520 -> 30 min, 35040 -> 15 min,
# 105120 -> 5 min. Hard-coding 5 min on an hourly file would have crammed a
# full year of values into ~30 days of timestamps.
steps = len(generation_kw)
minutes_per_step = (365 * 24 * 60) / steps     # 525600 / steps
if minutes_per_step != int(minutes_per_step):
    print(f"Warning: {steps} steps does not divide a 365-day year evenly; "
          f"timestep = {minutes_per_step:.4f} min.")
minutes_per_step = minutes_per_step  # keep as float; timedelta accepts it

print(f"Detected {steps} timesteps -> {minutes_per_step:g} minutes per step")

current_time = datetime(2023, 1, 1, 0, 0)
print(f"Exporting {steps} data points to '{output_csv_path}'...")

with open(output_csv_path, mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(["Timestamp", "Power_Generation_kW_AC"])
    for power in generation_kw:
        writer.writerow([current_time.strftime('%Y-%m-%d %H:%M:%S'),
                         round(power, 2)])
        current_time += timedelta(minutes=minutes_per_step)

print("CSV export complete.")