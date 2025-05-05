"""
Data models for policy reforms.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime

@dataclass
class PolicyChange:
    """Represents a specific change to a policy parameter."""
    start_date: str
    end_date: str
    value: Any
    date_range: Optional[str] = None
    
    def get_year(self) -> Optional[int]:
        """Extract the year from the start date."""
        try:
            return int(self.start_date.split('-')[0])
        except (ValueError, IndexError, AttributeError):
            return None
    
    def get_formatted_dates(self) -> str:
        """Return a human-readable date range string."""
        if self.date_range:
            return self.date_range
        
        try:
            start_year = self.start_date.split('-')[0]
            end_year = self.end_date.split('-')[0]
            
            if end_year == "2100":
                return f"starting in {start_year}"
            else:
                return f"from {start_year} to {end_year}"
        except (IndexError, AttributeError):
            return "for a specified period"

@dataclass
class PolicyParameter:
    """Represents a policy parameter that is being modified."""
    path: str
    name: str
    agency: str
    type: str
    changes: List[PolicyChange] = field(default_factory=list)
    year: Optional[int] = None
    
    def get_effective_year(self) -> int:
        """Get the effective year of the policy change."""
        if self.year:
            return self.year
            
        # Try to extract year from changes
        for change in self.changes:
            year = change.get_year()
            if year:
                return year
        
        # Default to current year if no year found
        return datetime.now().year

    def get_formatted_value(self, change_index: int = 0) -> str:
        """Format the value for human-readable output."""
        if not self.changes or change_index >= len(self.changes):
            return "modified value"
            
        value = self.changes[change_index].value
        
        # Format based on likely value type
        if isinstance(value, (int, float)):
            if self.type == "Tax Rate" or "rate" in self.path.lower():
                # Format as percentage
                return f"{value * 100:.1f}%" if value < 1 else f"{value:.1f}%"
            elif "amount" in self.path.lower() or "benefit" in self.path.lower():
                # Format as currency
                return f"${value:,.0f}"
            else:
                # Format as number
                return f"{value:,}"
        
        return str(value)

@dataclass
class PolicyReform:
    """Represents a complete policy reform with multiple parameter changes."""
    parameters: List[PolicyParameter] = field(default_factory=list)
    country: str = "United States"
    year: int = datetime.now().year
    metrics: List[str] = field(default_factory=list)
    simulation_year: Optional[int] = None
    difference_variable: Optional[str] = None
    
    @property
    def primary_parameter(self) -> Optional[PolicyParameter]:
        """Get the primary parameter being changed, if any."""
        if self.parameters:
            return self.parameters[0]
        return None
    
    def get_program_name(self) -> str:
        """Extract the program name from parameters."""
        if not self.parameters:
            return "Tax and Transfer Program"
            
        # Try to extract from first parameter
        parts = self.parameters[0].path.split('.')
        
        # Look for common program abbreviations
        for part in parts:
            part_lower = part.lower()
            if part_lower == "ctc":
                return "Child Tax Credit"
            elif part_lower == "eitc":
                return "Earned Income Tax Credit"
            elif part_lower == "snap":
                return "Supplemental Nutrition Assistance Program"
            elif part_lower == "tanf":
                return "Temporary Assistance for Needy Families"
            elif part_lower == "ssi":
                return "Supplemental Security Income"
            elif part_lower == "ui":
                return "Unemployment Insurance"
            elif part_lower == "housing" or part_lower == "section8":
                return "Housing Assistance"
            elif part_lower == "medicaid":
                return "Medicaid"
        
        # Default to a generic name based on parameter type
        if self.parameters[0].type:
            return f"{self.parameters[0].type} Program"
            
        return "Government Program"