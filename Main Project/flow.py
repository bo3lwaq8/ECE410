# Import necessary OpenLane 2 classes
from openlane.flows import Flow
from openlane.config import Config
import os

# --- Configuration ---
# We are running from the current directory "."
# This means 'config.json', 'conv5x5_core.sv', and 'conv5x5_wrapper.sv'
# MUST be in the same directory as where this notebook cell is effectively running from
# (usually /content/ in Colab if you've uploaded them there directly).

design_dir = "."  # Use the current directory
config_file = os.path.join(design_dir, "config.json") # This will effectively be "config.json"

# These PDK and SCL root paths are based on the typical OpenLane 2 Colab setup
# and your previous logs.
pdk_root = "/root/.volare"
scl_root = "/root/.volare/sky130A/libs.ref/sky130_fd_sc_hd"

print("--- Starting OpenLane 2 'Classic' Flow ---")
print(f"Attempting to run design using configuration from: {os.path.abspath(config_file)}")
print(f"Expected Verilog files in current directory: conv5x5_core.sv, conv5x5_wrapper.sv")
print("-------------------------------------------")

# --- Pre-flight Checks ---
# Check if all required files exist in the current directory
required_verilog_files = ["conv5x5_core.sv", "conv5x5_wrapper.sv"]
all_files_present = True

if not os.path.exists(config_file):
    print(f"ERROR: 'config.json' not found in the current directory ({os.path.abspath(design_dir)})!")
    all_files_present = False

for vf in required_verilog_files:
    if not os.path.exists(os.path.join(design_dir, vf)):
        print(f"ERROR: Verilog file '{vf}' not found in the current directory ({os.path.abspath(design_dir)})!")
        all_files_present = False

if not all_files_present:
    print("---")
    print("ERROR: One or more required files are missing. Please upload them to the Colab root directory ('/content/') and ensure 'config.json' is also present.")
    print("Flow will not start.")
    print("---")
else:
    try:
        # --- Load Configuration from config.json ---
        print("Loading configuration from config.json...")
        # Config.load() returns (config_object, path_to_design_dir)
        # In this case, loaded_design_dir should resolve to "."
        config, loaded_design_dir = Config.load(
            config_file,
            pdk_root=pdk_root,
            scl_root=scl_root
            # We don't need to specify VERILOG_FILES or TOP_MODULE here
            # because they should be defined inside your config.json
        )
        print(f"Configuration loaded successfully for design: {config['DESIGN_NAME']}")
        print(f"Design directory resolved to: {os.path.abspath(loaded_design_dir)}")


        # --- Instantiate the 'Classic' Flow ---
        # "Classic" is the name of the standard full RTL-to-GDSII flow
        print("Creating the 'Classic' flow instance...")
        flow = Flow(
            "Classic",
            config,                # The configuration object loaded from config.json
            design_dir=loaded_design_dir,  # The directory where the design and config are located
            pdk_root=pdk_root,
            scl_root=scl_root
        )
        print("Flow instance created.")

        # --- Start the Flow Execution ---
        # This is the main command that runs Synthesis, Floorplan, Placement, CTS, Route, etc.
        print("Starting OpenLane 2 flow execution (This will take several minutes)...")
        flow.start() # This runs all the steps in the Classic flow

        print("---")
        print("OpenLane 2 'Classic' flow execution finished (or stopped on error).")
        print("Check the logs above for details and look for reports/results in:")
        # OpenLane will create a 'runs' directory inside your design_dir (which is '.')
        print(f"  {os.path.abspath(loaded_design_dir)}/runs/")
        print("----------------------------------------------------------------")

    except Exception as e:
        print(f"!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        print(f"An ERROR occurred during the OpenLane 2 flow: {e}")
        print(f"Please check your setup, 'config.json', and Verilog code.")
        print(f"Make sure all paths within 'config.json' (for VERILOG_FILES) are just filenames if they are in the same directory.")
        print(f"!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")