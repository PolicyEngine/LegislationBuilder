# policy_text_generator.py
"""
Functions for generating plain English text descriptions of policy reforms.
"""

def generate_policy_text(reform_info):
    """
    Generate plain English text description of policy reforms.
    
    Args:
        reform_info (list): List of reform information dictionaries
        
    Returns:
        str: Plain English description of the policy changes
    """
    if not reform_info:
        return "No policy changes were identified."
    
    text_descriptions = []
    
    # Group reforms by policy area for better organization
    policy_areas = {}
    for reform in reform_info:
        area = reform["policy_area"]
        if area not in policy_areas:
            policy_areas[area] = []
        policy_areas[area].append(reform)
    
    # Generate descriptions for each reform by policy area
    for area, reforms in policy_areas.items():
        area_descriptions = []
        
        for reform in reforms:
            # Format the monetary values with commas and dollar signs if applicable
            value_str = str(reform["new_value"])
            if isinstance(reform["new_value"], (int, float)) and reform["new_value"] >= 1000:
                value_str = f"${reform['new_value']:,}"
            
            # Create a description based on the reform type
            if "ctc.amount.base" in reform["parameter"]:
                description = (
                    f"Change the Child Tax Credit amount to {value_str} "
                    f"from {reform['start_date']} to {reform['end_date']}."
                )
            elif "eitc" in reform["parameter"] and "age" in reform["parameter"]:
                description = (
                    f"Change the EITC {reform['name']} eligibility age to {value_str} "
                    f"from {reform['start_date']} to {reform['end_date']}."
                )
            elif "eitc" in reform["parameter"] and "investment_income" in reform["parameter"]:
                description = (
                    f"Change the maximum investment income for EITC eligibility to {value_str} "
                    f"from {reform['start_date']} to {reform['end_date']}."
                )
            elif "threshold" in reform["name"]:
                description = (
                    f"Change the {reform['description']} threshold to {value_str} "
                    f"from {reform['start_date']} to {reform['end_date']}."
                )
            elif "rate" in reform["name"]:
                # Format percentage values
                if isinstance(reform["new_value"], (int, float)) and reform["new_value"] <= 1:
                    value_str = f"{reform['new_value'] * 100}%"
                description = (
                    f"Change the {reform['description']} rate to {value_str} "
                    f"from {reform['start_date']} to {reform['end_date']}."
                )
            else:
                description = (
                    f"Change {reform['description'] or reform['parameter']} to {value_str} "
                    f"from {reform['start_date']} to {reform['end_date']}."
                )
            
            # Add reference information if available
            if reform["references"]:
                ref_titles = [ref.get("title", "Unknown reference") for ref in reform["references"]]
                description += f" This modifies {', '.join(ref_titles)}."
            
            area_descriptions.append(description)
        
        # Add all descriptions for this policy area
        text_descriptions.extend(area_descriptions)
    
    # Combine all descriptions
    if len(text_descriptions) == 1:
        full_text = "This policy reform includes the following change:\n\n"
    else:
        full_text = f"This policy reform includes the following {len(text_descriptions)} changes:\n\n"
    full_text += "\n".join(f"- {desc}" for desc in text_descriptions)
    
    return full_text