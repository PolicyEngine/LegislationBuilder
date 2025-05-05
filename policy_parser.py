# policy_parser.py
"""
Functions for parsing PolicyEngine Python code and extracting parameter information.
"""
import re
import ast
import yaml

def extract_reform_dict_from_code(code_string):
    """
    Extract the reform dictionary from PolicyEngine Python code.
    
    Args:
        code_string (str): Python code containing a reform definition
        
    Returns:
        dict: The reform dictionary
    """
    # Find the Reform.from_dict() call and extract the dictionary
    reform_dict_match = re.search(r'Reform\.from_dict\((.*?)(?:,\s*country_id|\))', code_string, re.DOTALL)
    
    if not reform_dict_match:
        raise ValueError("Could not find Reform.from_dict() in the provided code")
    
    # Get the dictionary part from the match
    reform_dict_str = reform_dict_match.group(1).strip()
    
    try:
        # Try to safely evaluate the dictionary with ast
        reform_dict = ast.literal_eval(reform_dict_str)
        return reform_dict
    except Exception as e:
        # If parsing fails, try a more flexible approach with a custom parser
        try:
            # Extract keys and values manually
            reform_dict = {}
            # Find all parameter paths and their values
            param_matches = re.findall(r'"([^"]+)":\s*{([^{}]+)}\s*,?', reform_dict_str)
            
            for param_path, values_str in param_matches:
                # Extract date range and value
                value_match = re.search(r'"([^"]+)":\s*(\d+)', values_str)
                if value_match:
                    date_range = value_match.group(1)
                    value = int(value_match.group(2))  # Assuming values are integers
                    reform_dict[param_path] = {date_range: value}
            
            if reform_dict:
                return reform_dict
            else:
                raise ValueError("Could not extract parameters from the reform dictionary")
        except Exception as e:
            raise ValueError(f"Could not parse the reform dictionary from the code: {str(e)}")


def get_parameter_info(parameter_path):
    """
    Get parameter information from the PolicyEngine parameter path.
    
    Args:
        parameter_path (str): The parameter path from the reform dict
        
    Returns:
        dict: Parameter information including name, description, references
    """
    # Convert parameter path to file path in policyengine-us repo structure
    # Example: "gov.irs.credits.ctc.amount.base[0].amount" -> "gov/irs/credits/ctc/amount/base.yaml"
    
    # Extract the base path without the array index and field
    base_path = re.sub(r'\[\d+\]\.[\w]+$', '', parameter_path)
    file_path = base_path.replace('.', '/')
    
    try:
        # Try to import the yaml file from policyengine_us
        from importlib.resources import files
        import policyengine_us.parameters
        
        # Get the parameter file content
        parameter_file = files('policyengine_us.parameters').joinpath(f"{file_path}.yaml")
        with open(parameter_file, 'r') as file:
            param_data = yaml.safe_load(file)
            
        return param_data
    except Exception as e:
        # If can't load the file, return basic info
        return {
            "description": f"Parameter at {parameter_path}",
            "metadata": {
                "reference": []
            }
        }


def parse_policy_reform(reform_dict):
    """
    Parse a PolicyEngine reform dictionary into a structured format.
    
    Args:
        reform_dict (dict): The reform dictionary from PolicyEngine
        
    Returns:
        dict: Structured information about the reform
    """
    reforms_info = []
    
    for param_path, changes in reform_dict.items():
        # Get parameter metadata
        param_info = get_parameter_info(param_path)
        
        # Extract parameter name (last part of the path)
        param_name = param_path.split('.')[-1]
        if '[' in param_name:
            param_name = param_name.split('[')[0]
        
        # Extract policy area (first few parts of the path)
        path_parts = param_path.split('.')
        policy_area = '.'.join(path_parts[:3]) if len(path_parts) >= 3 else path_parts[0]
        
        # Extract change information
        for date_range, new_value in changes.items():
            start_date, end_date = date_range.split('.')
            
            reforms_info.append({
                "parameter": param_path,
                "name": param_name,
                "policy_area": policy_area,
                "description": param_info.get("description", ""),
                "references": param_info.get("metadata", {}).get("reference", []),
                "start_date": start_date,
                "end_date": end_date,
                "new_value": new_value
            })
    
    return reforms_info

def format_date_values(obj):
    """
    Convert date objects in a nested structure to strings for JSON serialization.
    
    Args:
        obj: A dictionary, list, or other object that might contain date values
        
    Returns:
        The same structure with date objects converted to strings
    """
    import datetime
    
    if isinstance(obj, dict):
        return {str(k) if isinstance(k, datetime.date) else k: format_date_values(v) 
                for k, v in obj.items()}
    elif isinstance(obj, list):
        return [format_date_values(item) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(format_date_values(item) for item in obj)
    elif isinstance(obj, set):
        return {format_date_values(item) for item in obj}
    elif isinstance(obj, datetime.date):
        return obj.isoformat()  # Convert date to string
    else:
        return obj