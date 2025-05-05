"""
Text generator for policy reforms.
Converts parsed policy information into human-readable descriptions.
"""

from typing import Dict, Any, List, Optional
from models.policy_reform import PolicyReform, PolicyParameter, PolicyChange

class TextGenerationError(Exception):
    """Exception raised when text generation fails."""
    pass

def generate_policy_text(policy_info: Dict[str, Any]) -> str:
    """
    Generate human-readable text describing a policy reform.
    
    Args:
        policy_info: Dictionary with parsed policy information
    
    Returns:
        String with policy description
    
    Raises:
        TextGenerationError: If text generation fails
    """
    try:
        # Convert dict to PolicyReform object for easier processing
        reform = _dict_to_reform_object(policy_info)
        
        # Generate policy text based on the reform object
        policy_text = _generate_reform_description(reform)
        
        return policy_text
    
    except Exception as e:
        raise TextGenerationError(f"Error generating policy text: {str(e)}")

def _dict_to_reform_object(policy_info: Dict[str, Any]) -> PolicyReform:
    """
    Convert a policy info dictionary to a PolicyReform object.
    
    Args:
        policy_info: Dictionary with parsed policy information
    
    Returns:
        PolicyReform object
    """
    # Create policy parameters
    parameters = []
    for param_dict in policy_info.get("parameters", []):
        changes = []
        
        for change_dict in param_dict.get("changes", []):
            # Create PolicyChange objects
            change = PolicyChange(
                start_date=change_dict.get("start_date", ""),
                end_date=change_dict.get("end_date", ""),
                value=change_dict.get("value"),
                date_range=change_dict.get("date_range")
            )
            changes.append(change)
        
        # Create PolicyParameter object
        parameter = PolicyParameter(
            path=param_dict.get("path", ""),
            name=param_dict.get("name", "Unknown Parameter"),
            agency=param_dict.get("agency", "Federal Government"),
            type=param_dict.get("type", "Policy Parameter"),
            changes=changes,
            year=param_dict.get("year")
        )
        parameters.append(parameter)
    
    # Create the PolicyReform object
    reform = PolicyReform(
        parameters=parameters,
        country=policy_info.get("country", "United States"),
        year=policy_info.get("year", 2025),
        metrics=policy_info.get("metrics", []),
        simulation_year=policy_info.get("simulation_year"),
        difference_variable=policy_info.get("difference_variable")
    )
    
    return reform

def _generate_reform_description(reform: PolicyReform) -> str:
    """
    Generate a comprehensive description of the policy reform.
    
    Args:
        reform: PolicyReform object
    
    Returns:
        String with policy description
    """
    description_parts = []
    
    # Add title
    program_name = reform.get_program_name()
    description_parts.append(f"Reform to the {program_name}")
    
    # Add summary
    summary = _generate_summary(reform)
    if summary:
        description_parts.append(summary)
    
    # Add parameter details
    param_details = _generate_parameter_details(reform)
    if param_details:
        description_parts.append(param_details)
        
    # Add implementation details
    implementation = _generate_implementation_details(reform)
    if implementation:
        description_parts.append(implementation)
    
    # Join all parts with double newlines
    return "\n\n".join(description_parts)

def _generate_summary(reform: PolicyReform) -> str:
    """
    Generate a summary of the policy reform.
    
    Args:
        reform: PolicyReform object
    
    Returns:
        Summary text
    """
    if not reform.parameters:
        return "This reform modifies federal tax and transfer policy parameters."
    
    primary_param = reform.primary_parameter
    
    # Basic summary format
    if primary_param and primary_param.changes:
        change = primary_param.changes[0]
        param_name = primary_param.name
        value = primary_param.get_formatted_value()
        date_str = change.get_formatted_dates()
        
        if primary_param.type == "Tax Credit":
            return f"This reform modifies the {param_name} to {value} {date_str}."
        elif primary_param.type == "Tax Rate":
            return f"This reform sets the {param_name} to {value} {date_str}."
        elif primary_param.type == "Benefit Amount":
            return f"This reform changes the {param_name} to {value} {date_str}."
        elif primary_param.type == "Threshold":
            return f"This reform adjusts the {param_name} to {value} {date_str}."
        else:
            return f"This reform changes the {param_name} parameter to {value} {date_str}."
    
    return "This reform modifies one or more parameters of the federal tax and transfer system."

def _generate_parameter_details(reform: PolicyReform) -> str:
    """
    Generate detailed descriptions of each parameter change.
    
    Args:
        reform: PolicyReform object
    
    Returns:
        Parameter details text
    """
    if not reform.parameters:
        return ""
    
    details_parts = []
    
    for param in reform.parameters:
        if not param.changes:
            continue
            
        param_details = []
        
        for i, change in enumerate(param.changes):
            value = param.get_formatted_value(i)
            date_str = change.get_formatted_dates()
            
            # Format based on parameter type
            if param.type == "Tax Credit":
                param_details.append(f"The {param.name} is set to {value} {date_str}.")
            elif param.type == "Tax Rate":
                param_details.append(f"The {param.name} is changed to {value} {date_str}.")
            elif param.type == "Benefit Amount":
                param_details.append(f"The {param.name} is adjusted to {value} {date_str}.")
            elif param.type == "Threshold" or param.type == "Eligibility Criteria":
                param_details.append(f"The {param.name} is modified to {value} {date_str}.")
            else:
                param_details.append(f"The {param.name} parameter is set to {value} {date_str}.")
        
        details_parts.append(" ".join(param_details))
    
    return "Details:\n" + "\n".join(details_parts)

def _generate_implementation_details(reform: PolicyReform) -> str:
    """
    Generate implementation details of the reform.
    
    Args:
        reform: PolicyReform object
    
    Returns:
        Implementation details text
    """
    details_parts = []
    
    # Add agency information
    agencies = set(param.agency for param in reform.parameters if param.agency)
    if agencies:
        agency_list = ", ".join(agencies)
        details_parts.append(f"This reform would be implemented through {agency_list}.")
    
    # Add effective year if available
    effective_years = set()
    for param in reform.parameters:
        for change in param.changes:
            year = change.get_year()
            if year:
                effective_years.add(year)
    
    if effective_years:
        years_str = ", ".join(str(year) for year in sorted(effective_years))
        if len(effective_years) == 1:
            details_parts.append(f"The reform would take effect in {years_str}.")
        else:
            details_parts.append(f"The reform would be implemented across multiple years: {years_str}.")
    
    # Add simulation information if available
    if reform.simulation_year:
        details_parts.append(f"The policy impact was simulated for the year {reform.simulation_year}.")
    
    if reform.metrics:
        metrics_str = ", ".join(m.replace("_", " ").title() for m in reform.metrics)
        details_parts.append(f"The simulation analyzed impacts on {metrics_str}.")
    
    if not details_parts:
        return ""
        
    return "Implementation:\n" + "\n".join(details_parts)