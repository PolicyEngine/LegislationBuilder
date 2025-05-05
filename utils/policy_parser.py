"""
PolicyEngine JSON parser.
Extracts policy changes from PolicyEngine-generated code.
"""

import re
import ast
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional

class PolicyParseError(Exception):
    """Exception raised when parsing policy fails."""
    pass

def parse_policy_json(policy_code: str) -> Dict[str, Any]:
    """
    Parse PolicyEngine JSON/Python code to extract policy details.
    
    Args:
        policy_code: String containing PolicyEngine Python code with reform definition
    
    Returns:
        Dictionary with parsed policy information
    
    Raises:
        PolicyParseError: If policy code can't be properly parsed
    """
    try:
        # Extract the reform dictionary definition
        reform_dict_match = re.search(r'Reform\.from_dict\((.*?}),\s*country_id=', 
                                      policy_code, re.DOTALL)
        if not reform_dict_match:
            raise PolicyParseError("Could not find Reform.from_dict() call in the policy code")
        
        # Extract the dictionary string and parse it
        reform_dict_str = reform_dict_match.group(1)
        
        # For safety, evaluate the string as a literal AST node
        try:
            reform_dict = ast.literal_eval(reform_dict_str)
        except (SyntaxError, ValueError) as e:
            # If ast.literal_eval fails, try to extract the dictionary more directly
            # This is a fallback method
            dict_match = re.search(r'{(.*?)}', reform_dict_str, re.DOTALL)
            if not dict_match:
                raise PolicyParseError(f"Failed to parse reform dictionary: {str(e)}")
            
            # Try to manually process the dictionary
            raw_dict = dict_match.group(0)
            reform_dict = _safe_eval_dict(raw_dict)
        
        # Process the reform dictionary
        processed_policy = _process_reform_dict(reform_dict)
        
        # Extract impact information
        impact_info = _extract_impact_info(policy_code)
        if impact_info:
            processed_policy.update(impact_info)
        
        return processed_policy
    
    except Exception as e:
        raise PolicyParseError(f"Error parsing policy code: {str(e)}")

def _safe_eval_dict(dict_str: str) -> Dict:
    """
    Safely evaluate a dictionary string, for cases where ast.literal_eval fails.
    This is a fallback method and should be used cautiously.
    
    Args:
        dict_str: String representation of a dictionary
    
    Returns:
        Evaluated dictionary
    """
    # This is a simplified implementation
    # In a production environment, you'd want more robust parsing
    cleaned = dict_str.replace("\n", "").replace(" ", "")
    result = {}
    
    # Extract key-value pairs using regex
    matches = re.findall(r'"([^"]+)":{(?:[^{}]|{[^{}]*})*}', cleaned)
    for match in matches:
        key = match
        value_match = re.search(f'"{key}":({{.*?}})', cleaned, re.DOTALL)
        if value_match:
            value_str = value_match.group(1)
            
            # Extract date ranges and values
            date_values = {}
            date_matches = re.findall(r'"([^"]+)":(.*?)(?:,|})', value_str)
            for date_range, value in date_matches:
                try:
                    # Clean and convert the value
                    clean_value = value.strip()
                    if clean_value.isdigit():
                        date_values[date_range] = int(clean_value)
                    elif clean_value.replace('.', '', 1).isdigit():
                        date_values[date_range] = float(clean_value)
                    else:
                        date_values[date_range] = clean_value
                except ValueError:
                    date_values[date_range] = value
            
            result[key] = date_values
    
    return result

def _process_reform_dict(reform_dict: Dict) -> Dict[str, Any]:
    """
    Process the reform dictionary to extract policy parameters, dates, and values.
    
    Args:
        reform_dict: Dictionary from Reform.from_dict()
    
    Returns:
        Processed policy information
    """
    policy_info = {
        "parameters": [],
        "country": "United States",  # Default, assuming US
        "year": datetime.now().year  # Default to current year
    }
    
    for param_path, value_dict in reform_dict.items():
        param_info = _parse_parameter(param_path, value_dict)
        policy_info["parameters"].append(param_info)
    
    return policy_info

def _parse_parameter(param_path: str, value_dict: Dict) -> Dict[str, Any]:
    """
    Parse a single policy parameter and its values.
    
    Args:
        param_path: Parameter path string
        value_dict: Dictionary of date ranges and values
    
    Returns:
        Parsed parameter information
    """
    # Extract components from the parameter path
    path_parts = param_path.split('.')
    
    parameter = {
        "path": param_path,
        "name": _get_readable_name(path_parts),
        "agency": _extract_agency(path_parts),
        "type": _infer_parameter_type(path_parts),
        "changes": []
    }
    
    # Process date ranges and values
    for date_range, value in value_dict.items():
        dates = date_range.split('.')
        if len(dates) >= 2:
            try:
                start_date = dates[0]
                end_date = dates[1]
                
                # Add the change with dates and value
                parameter["changes"].append({
                    "start_date": start_date,
                    "end_date": end_date,
                    "value": value
                })
                
                # Update the policy year based on start date
                try:
                    policy_year = int(start_date.split('-')[0])
                    parameter["year"] = policy_year
                except (ValueError, IndexError):
                    pass
                
            except (ValueError, IndexError):
                # If date parsing fails, just store as is
                parameter["changes"].append({
                    "date_range": date_range,
                    "value": value
                })
        else:
            # If not a proper date range, store as is
            parameter["changes"].append({
                "date_range": date_range,
                "value": value
            })
    
    return parameter

def _get_readable_name(path_parts: List[str]) -> str:
    """
    Generate a human-readable name from parameter path parts.
    
    Args:
        path_parts: List of parts from a parameter path
    
    Returns:
        Human-readable parameter name
    """
    # Extract the main parameter name, typically the last part before any array indices
    core_parts = []
    for part in path_parts:
        # Skip array indices
        if part.startswith("[") and part.endswith("]"):
            continue
        # Remove array indices
        if "[" in part:
            part = part.split("[")[0]
        core_parts.append(part)
    
    # Join with spaces and capitalize words
    if core_parts:
        last_part = core_parts[-1]
        return last_part.replace("_", " ").title()
    
    return "Unknown Parameter"

def _extract_agency(path_parts: List[str]) -> str:
    """
    Extract the government agency from parameter path.
    
    Args:
        path_parts: List of parts from a parameter path
    
    Returns:
        Agency name or default
    """
    # Look for common agency abbreviations
    if len(path_parts) >= 2 and path_parts[0] == "gov":
        if path_parts[1] == "irs":
            return "Internal Revenue Service"
        elif path_parts[1] == "hhs":
            return "Health and Human Services"
        elif path_parts[1] == "usda":
            return "Department of Agriculture"
        elif path_parts[1] == "dol":
            return "Department of Labor"
        elif path_parts[1] == "ssi":
            return "Social Security Administration"
        return path_parts[1].upper()  # Default to uppercase abbreviation
    
    return "Federal Government"  # Default

def _infer_parameter_type(path_parts: List[str]) -> str:
    """
    Infer the type of parameter from its path.
    
    Args:
        path_parts: List of parts from a parameter path
    
    Returns:
        Inferred parameter type
    """
    path_str = ".".join(path_parts).lower()
    
    if "credit" in path_str or "ctc" in path_str:
        return "Tax Credit"
    elif "deduction" in path_str:
        return "Tax Deduction"
    elif "amount" in path_str:
        return "Benefit Amount"
    elif "rate" in path_str:
        return "Tax Rate"
    elif "threshold" in path_str or "limit" in path_str:
        return "Threshold"
    elif "eligibility" in path_str:
        return "Eligibility Criteria"
    
    return "Policy Parameter"

def _extract_impact_info(policy_code: str) -> Optional[Dict[str, Any]]:
    """
    Extract impact information from the policy simulation code.
    
    Args:
        policy_code: String containing PolicyEngine Python code
    
    Returns:
        Dictionary with impact information or None if not found
    """
    impact_info = {}
    
    # Look for calculations in the code
    calc_matches = re.findall(r'calculate\("([^"]+)",\s*period=(\d+)\)', policy_code)
    if calc_matches:
        impact_info["metrics"] = [metric for metric, _ in calc_matches]
        # Extract the simulation year
        if calc_matches and calc_matches[0][1].isdigit():
            impact_info["simulation_year"] = int(calc_matches[0][1])
    
    # Look for difference calculations
    diff_match = re.search(r'(\w+)\s*=\s*(\w+)\s*-\s*(\w+)', policy_code)
    if diff_match:
        impact_info["difference_variable"] = diff_match.group(1)
    
    return impact_info if impact_info else None