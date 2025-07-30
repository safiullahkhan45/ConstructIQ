"""
Permit data models - Enhanced from original normalization pipeline
"""

from dataclasses import dataclass
from typing import Dict, List, Any, Optional


@dataclass
class Location:
    """Standardized location information"""
    street_address: Optional[str] = None
    city: str = "Austin"
    state: str = "TX"
    zip_code: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    council_district: Optional[int] = None
    census_tract: Optional[str] = None


@dataclass
class Contractor:
    """Standardized contractor information"""
    name: Optional[str] = None
    license_number: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    company_type: Optional[str] = None


@dataclass
class Applicant:
    """Standardized applicant information"""
    name: Optional[str] = None
    company: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None


@dataclass
class Valuation:
    """Standardized valuation and financial information"""
    total_valuation: Optional[float] = None
    permit_fee: Optional[float] = None
    currency: str = "USD"


@dataclass
class WorkDetails:
    """Standardized work description and specifications"""
    permit_type: Optional[str] = None
    work_class: Optional[str] = None
    description: Optional[str] = None
    use_category: Optional[str] = None


@dataclass
class PermitDates:
    """Standardized date information"""
    issue_date: Optional[str] = None  # ISO format
    expiration_date: Optional[str] = None  # ISO format
    application_date: Optional[str] = None  # ISO format


@dataclass
class NormalizedPermit:
    """Main normalized permit record"""
    permit_id: str
    permit_number: Optional[str] = None
    status: Optional[str] = None
    location: Optional[Location] = None
    contractor: Optional[Contractor] = None
    applicant: Optional[Applicant] = None
    valuation: Optional[Valuation] = None
    work_details: Optional[WorkDetails] = None
    dates: Optional[PermitDates] = None
    metadata: Optional[Dict[str, Any]] = None