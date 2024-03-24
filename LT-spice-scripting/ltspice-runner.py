import subprocess
import os
import pprint
import time

def get_original_asc_text(asc_file_path:str=None):
    with open(asc_file_path, 'r') as file:
        data = file.read()
    return data

def set_to_original_asc_text(asc_file_path:str=None, data:str=None):
    with open(asc_file_path, 'w') as file:
        file.write(data)

def update_place_asc_placeholder(asc_file_path:str=None, place_holder_text:str = None, replacement_text:str = None):
    with open(asc_file_path, 'r') as file:
        data = file.read()
    
    # Find and replace specific text
    new_data = data.replace(place_holder_text, replacement_text)
    
    with open(asc_file_path, 'w') as file:
        file.write(new_data)

def parse_LTspice_data(data):
    header_lines = []
    for line in data.split("\n"):
        if "Values:" in line:
            break       
        header_lines.append(line)

    header_dict = {
        "Title": None,
        "Date": None,
        "No. Variables": None,
        "No. Points": None,
        "Offset": None,
        "Command": None,
        "Variables": [],
    }

    is_variables = False
    for line in header_lines:
        if "Title" in line:
            header_dict["Title"] = line
        elif "Date" in line:
            header_dict["Date"] = line.split(":")[1].strip()
        elif "No. Variables" in line:
            header_dict["No. Variables"] = int(line.split(":")[1].strip())
        elif "No. Points" in line:
            header_dict["No. Points"] = int(line.split(":")[1].strip())
        elif "Offset" in line:
            header_dict["Offset"] = float(line.split(":")[1].strip())
        elif "Command" in line:
            header_dict["Command"] = line.split(":")[1].strip()
        elif "Variables" in line:
            is_variables = True
        elif is_variables:
            header_dict["Variables"].append(line.split("\t"))

    value_lines = []
    is_at_values = False
    no_of_variables = header_dict["No. Variables"]
    sample_now = []
    for line in data.split("\n"):
        if "Values:" in line:
            is_at_values = True
            continue

        if is_at_values:
            if len(sample_now) == 0:
                sample_no_and_time = line
                sample_now.append(sample_no_and_time)
            else:
                sample_now.append(line.split("\t")[1])

            if len(sample_now) == no_of_variables:
                value_lines.append(sample_now)
                sample_now = []
            
    return header_dict, value_lines

def find_peak_of_each_value(header_dict:dict, value_lines:list[list], is_absolute:bool=True):
    # Find the peak of each value

    value_tags = []
    for variable in header_dict["Variables"]:
        value_tags.append(variable[2]) #name of the variable

    number_of_variables = header_dict["No. Variables"]
    peak_values = [float("-inf")]*number_of_variables
    for sample_values in value_lines:
        for i in range(1,len(sample_values)):
            sample_value = float(sample_values[i])
            if is_absolute:
                sample_value = abs(sample_value)
           
            if sample_value > peak_values[i]:
                peak_values[i] = sample_value

    print("Peak values:")
    for i in range(1, len(peak_values)):
        print(f"{value_tags[i]}: {peak_values[i]}")

    return peak_values

LT_SPICE_EXECUTABLE_PATH = "C:/Program Files/LTC/LTspiceXVII/XVIIx64.exe" #probable path to LTspice executable
SCRIPT_PATH = os.path.abspath(__file__)
LTSPICE_ASC_PATH = os.path.join(os.path.dirname(SCRIPT_PATH), "AC_R_circuit/AC_R_circuit.asc")

ORIGINAL_ASC_TEXT = get_original_asc_text(asc_file_path=LTSPICE_ASC_PATH)
update_place_asc_placeholder(asc_file_path=LTSPICE_ASC_PATH, place_holder_text = "<sine_voltage>", replacement_text = "10")

create_netlist_line = [LT_SPICE_EXECUTABLE_PATH, "-netlist", LTSPICE_ASC_PATH] # -netlist flag to generate netlist
subprocess.run(create_netlist_line)
LTSPICE_NET_PATH = os.path.join(os.path.dirname(SCRIPT_PATH), "AC_R_circuit/AC_R_circuit.net")

run_simulation_line = [LT_SPICE_EXECUTABLE_PATH, "-b -ascii ", LTSPICE_NET_PATH] # -b flag to run simulation without ui. To see the ui, replace with -Run. -ascii flag to generate ascii output raw file
subprocess.run(run_simulation_line)
LTSPICE_RAW_DATA_PATH = os.path.join(os.path.dirname(SCRIPT_PATH), "AC_R_circuit/AC_R_circuit.raw")

with open(LTSPICE_RAW_DATA_PATH, 'r') as file:
    data = file.read()
header_dict, value_lines = parse_LTspice_data(data)

print("Header:")
pprint.pprint(header_dict)

# print("\nValues:")
# pprint.pprint(value_lines)

find_peak_of_each_value(header_dict, value_lines, is_absolute=True)

# Restore the original asc file
set_to_original_asc_text(asc_file_path=LTSPICE_ASC_PATH, data=ORIGINAL_ASC_TEXT)