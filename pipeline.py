"""
Austin Construction Permits Data Normalization Pipeline
=====================================================

A comprehensive solution for normalizing messy Austin construction permit data
into a clean, modular JSON schema. Handles ~70 inconsistent fields with edge cases.

Author: Safiullah Khan Sherzad
Purpose: Technical Assessment - Data Normalization Challenge
"""

import json
import re
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import logging
from pathlib import Path

import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


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
    dates: Optional[PermitDates] = None
    metadata: Optional[Dict[str, Any]] = None


class AustinPermitsNormalizer:
    """
    Main normalization class for Austin Construction Permits data
    """

    def __init__(self, config_path: Optional[str] = None):
        self.config = self._load_config(config_path)
        self.field_mappings = self._initialize_field_mappings()
        self.stats = {
            "total_records": 0,
            "normalized_records": 0,
            "errors": 0,
            "warnings": 0,
        }

    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load configuration file or use defaults"""
        default_config = {
            "date_formats": ["%Y-%m-%d", "%m/%d/%Y", "%Y-%m-%dT%H:%M:%S"],
            "currency_symbols": ["$", "USD", "usd"],
            "phone_patterns": [r"\d{3}-\d{3}-\d{4}", r"\(\d{3}\)\s*\d{3}-\d{4}"],
            "zip_pattern": r"\d{5}(-\d{4})?",
            "permit_types": [
                "Building",
                "Electrical",
                "Mechanical",
                "Plumbing",
                "Driveway",
            ],
        }

        if config_path and Path(config_path).exists():
            with open(config_path, "r") as f:
                user_config = json.load(f)
                default_config.update(user_config)

        return default_config

    def _initialize_field_mappings(self) -> Dict[str, str]:
        """
        Initialize field mappings for common Austin permit field variations
        This handles the ~70 inconsistent field names
        """
        return {
            # Permit identification
            "permit_num": "permit_number",
            "permit_number": "permit_number",
            "permitnumber": "permit_number",
            "permit_id": "permit_id",
            "permitid": "permit_id",
            "permit_no": "permit_number",
            # Location fields
            "original_address1": "street_address",
            "street_address": "street_address",
            "address": "street_address",
            # 'location': 'street_address',
            "original_city": "city",
            "original_state": "state",
            "original_zip": "zip_code",
            "zip_code": "zip_code",
            "zipcode": "zip_code",
            "council_district_code": "council_district",
            "council_dist": "council_district",
            "latitude": "latitude",
            "longitude": "longitude",
            "lat": "latitude",
            "lng": "longitude",
            "long": "longitude",
            # Contractor fields
            "contractor_name": "contractor_name",
            "contractor_company_name": "contractor_name",
            "contractor_trade_name": "contractor_name",
            "contractor_phone": "contractor_phone",
            "contractor_phone_number": "contractor_phone",
            "contractor_address": "contractor_address",
            "license_number": "contractor_license",
            "contractor_license_number": "contractor_license",
            # Applicant fields
            "applicant_name": "applicant_name",
            "applicant_company": "applicant_company",
            "applicant_phone": "applicant_phone",
            "applicant_email": "applicant_email",
            "applicant_address": "applicant_address",
            "owner_name": "applicant_name",
            # Valuation fields
            "total_valuation": "total_valuation",
            "totalvaluation": "total_valuation",
            "valuation": "total_valuation",
            "permit_fee": "permit_fee",
            "fee_amount": "permit_fee",
            # Work details
            "permit_type_desc": "permit_type",
            "permit_type": "permit_type",
            "permittype": "permit_type",
            "work_class": "work_class",
            "permit_class": "work_class",
            "description": "work_description",
            "work_description": "work_description",
            "scope_of_work": "work_description",
            "use_category": "use_category",
            "use_type": "use_category",
            # Date fields
            "issue_date": "issue_date",
            "issued_date": "issue_date",
            "date_issued": "issue_date",
            "expiration_date": "expiration_date",
            "expire_date": "expiration_date",
            "application_date": "application_date",
            "applied_date": "application_date",
            # Status fields
            "status": "status",
            "permit_status": "status",
            "current_status": "status",
        }

    def normalize_date(self, date_value: Any) -> Optional[str]:
        """Normalize various date formats to ISO format"""
        if pd.isna(date_value) or date_value is None or str(date_value).strip() == "":
            return None

        date_str = str(date_value).strip()

        # Try each configured date format
        for fmt in self.config["date_formats"]:
            try:
                parsed_date = datetime.strptime(date_str, fmt)
                return parsed_date.strftime("%Y-%m-%d")
            except ValueError:
                continue

        # Try pandas date parser as fallback
        try:
            parsed_date = pd.to_datetime(date_str)
            return parsed_date.strftime("%Y-%m-%d")
        except:
            logger.warning(f"Could not parse date: {date_str}")
            self.stats["warnings"] += 1
            return None

    def normalize_currency(self, value: Any) -> Optional[float]:
        """Normalize currency values to float"""
        if pd.isna(value) or value is None:
            return None

        # Convert to string and clean
        value_str = str(value).strip()

        # Remove currency symbols
        for symbol in self.config["currency_symbols"]:
            value_str = value_str.replace(symbol, "")

        # Remove commas and other formatting
        value_str = re.sub(r"[,\s]", "", value_str)

        try:
            return float(value_str)
        except ValueError:
            logger.warning(f"Could not parse currency value: {value}")
            self.stats["warnings"] += 1
            return None

    def normalize_phone(self, phone: Any) -> Optional[str]:
        """Normalize phone numbers to standard format"""
        if pd.isna(phone) or phone is None:
            return None

        phone_str = str(phone).strip()

        # Extract digits only
        digits = re.sub(r"\D", "", phone_str)

        # Format as XXX-XXX-XXXX if we have 10 digits
        if len(digits) == 10:
            return f"{digits[:3]}-{digits[3:6]}-{digits[6:]}"
        elif len(digits) == 11 and digits[0] == "1":
            # Remove leading 1
            return f"{digits[1:4]}-{digits[4:7]}-{digits[7:]}"
        else:
            # Return original if we can't parse
            return phone_str if phone_str else None

    def get_zip_code(self, street_address: str, city: str) -> str:
        """
        Get the zip code based on the street address using Nominatim API (OpenStreetMap)
        """
        query = f"{street_address}, {city}, US"  # Currently only US.
        url = f"https://nominatim.openstreetmap.org/search?format=json&addressdetails=1&q={query}"
        # Add headers with a User-Agent
        headers = {
            "User-Agent": "ConstructIQ/1.0 (safiullah.khan145@gmail.com)"  # Replace with your app name and email
        }
        response = requests.get(url, headers=headers)
        zip_code = None
        if response.status_code == 200:
            data = response.json()

            # Check if the response contains results
            if data:
                # Extract the zip code (if available)
                zip_code = data[0].get("address", {}).get("postcode", None)

        if not zip_code:
            logger.warning(f"Could not get zip code for {street_address}, {city}")
            self.stats["warnings"] += 1

        # Return None if no zip code found or the request failed
        return zip_code

    def normalize_zip_code(
        self, zip_code: Any, street_address: str = "", city: str = ""
    ) -> Optional[str]:
        """Normalize zip codes"""
        if pd.isna(zip_code) or zip_code is None:
            # If zip code is null/empty, try to get it from street address
            if street_address and city:
                return self.get_zip_code(street_address, city)
            return None

        zip_str = str(zip_code).strip()

        # Extract zip code pattern
        match = re.search(self.config["zip_pattern"], zip_str)
        if match:
            return match.group(0)

        return None

    def map_field_name(self, original_name: str) -> str:
        """Map original field names to standardized names"""
        # Normalize field name (lowercase, replace spaces/special chars)
        normalized_name = re.sub(r"[^a-zA-Z0-9_]", "_", original_name.lower().strip())
        normalized_name = re.sub(r"_+", "_", normalized_name).strip("_")

        return self.field_mappings.get(normalized_name, normalized_name)

    def handle_duplicate_fields(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Handle duplicate or conflicting fields"""
        cleaned_record = {}
        field_priorities = {}

        for key, value in record.items():
            mapped_key = self.map_field_name(key)

            # Skip if value is null/empty
            if pd.isna(value) or str(value).strip() == "":
                continue

            # If field already exists, keep the one with higher priority
            if mapped_key in cleaned_record:
                # Priority logic: longer strings usually have more info
                current_len = len(str(cleaned_record[mapped_key]))
                new_len = len(str(value))

                if new_len > current_len:
                    cleaned_record[mapped_key] = value
                    field_priorities[mapped_key] = key
            else:
                cleaned_record[mapped_key] = value
                field_priorities[mapped_key] = key

        return cleaned_record

    def create_location_object(self, record: Dict[str, Any]) -> Location:
        """Create standardized Location object from record"""
        return Location(
            street_address=record.get("street_address"),
            city=record.get("city", "Austin"),
            state=record.get("state", "TX"),
            zip_code=self.normalize_zip_code(
                record.get("zip_code"),
                street_address=record.get("street_address"),
                city=record.get("city"),
            ),
            latitude=pd.to_numeric(record.get("latitude"), errors="coerce") or None,
            longitude=pd.to_numeric(record.get("longitude"), errors="coerce") or None,
            council_district=pd.to_numeric(
                record.get("council_district"), errors="coerce"
            )
            or None,
            census_tract=record.get("census_tract"),
        )

    def create_contractor_object(self, record: Dict[str, Any]) -> Contractor:
        """Create standardized Contractor object from record"""
        return Contractor(
            name=record.get("contractor_name"),
            license_number=record.get("contractor_license"),
            phone=self.normalize_phone(record.get("contractor_phone")),
            address=record.get("contractor_address"),
            company_type=record.get("contractor_type"),
        )

    def create_applicant_object(self, record: Dict[str, Any]) -> Applicant:
        """Create standardized Applicant object from record"""
        return Applicant(
            name=record.get("applicant_name"),
            company=record.get("applicant_company"),
            phone=self.normalize_phone(record.get("applicant_phone")),
            email=record.get("applicant_email"),
            address=record.get("applicant_address"),
        )

    def create_valuation_object(self, record: Dict[str, Any]) -> Valuation:
        """Create standardized Valuation object from record"""
        return Valuation(
            total_valuation=self.normalize_currency(record.get("total_valuation")),
            permit_fee=self.normalize_currency(record.get("permit_fee")),
            currency="USD",
        )
    
    def create_work_details_object(self, record: Dict[str, Any]) -> WorkDetails:
        """Create standardized WorkDetails object from record"""
        return WorkDetails(
            permit_type=record.get('permit_type'),
            work_class=record.get('work_class'),
            description=record.get('work_description'),
            use_category=record.get('use_category')
        )
    
    def create_dates_object(self, record: Dict[str, Any]) -> PermitDates:
        """Create standardized PermitDates object from record"""
        return PermitDates(
            issue_date=self.normalize_date(record.get("issue_date")),
            expiration_date=self.normalize_date(record.get("expiration_date")),
            application_date=self.normalize_date(record.get("application_date")),
        )

    def normalize_record(
        self, raw_record: Dict[str, Any]
    ) -> Optional[NormalizedPermit]:
        """Normalize a single permit record"""
        try:
            # Handle duplicates and map field names
            cleaned_record = self.handle_duplicate_fields(raw_record)

            # Generate permit ID if not present
            permit_id = cleaned_record.get("permit_id") or cleaned_record.get(
                "permit_number"
            )
            if not permit_id:
                permit_id = f"permit_{hash(str(raw_record)) % 1000000}"

            # Create normalized permit object
            normalized_permit = NormalizedPermit(
                permit_id=str(permit_id),
                permit_number=cleaned_record.get("permit_number"),
                status=cleaned_record.get("status"),
                location=self.create_location_object(cleaned_record),
                contractor=self.create_contractor_object(cleaned_record),
                applicant=self.create_applicant_object(cleaned_record),
                valuation=self.create_valuation_object(cleaned_record),
                work_details=self.create_work_details_object(cleaned_record),
                dates=self.create_dates_object(cleaned_record),
                metadata={
                    "normalized_at": datetime.now().isoformat(),
                    "original_fields_count": len(raw_record),
                    "data_quality_score": self._calculate_quality_score(cleaned_record),
                },
            )

            self.stats["normalized_records"] += 1
            return normalized_permit

        except Exception as e:
            logger.error(f"Error normalizing record: {e}")
            self.stats["errors"] += 1
            return None

    def _calculate_quality_score(self, record: Dict[str, Any]) -> float:
        """Calculate data quality score (0-1)"""
        essential_fields = ["permit_id", "street_address", "permit_type", "issue_date"]

        score = 0.0
        total_weight = 0.0

        # Essential fields (weight: 2)
        for field in essential_fields:
            total_weight += 2.0
            if record.get(field):
                score += 2.0

        # Other fields (weight: 1)
        other_fields = set(record.keys()) - set(essential_fields)
        for field in other_fields:
            total_weight += 1.0
            if record.get(field):
                score += 1.0

        return score / total_weight if total_weight > 0 else 0.0

    def load_data(
        self, file_path: str, file_format: str = "auto"
    ) -> List[Dict[str, Any]]:
        """Load data from CSV or JSON file"""
        file_path = Path(file_path)

        if file_format == "auto":
            file_format = file_path.suffix.lower()[1:]  # Remove dot

        if file_format == "csv":
            df = pd.read_csv(file_path)
            return df.to_dict("records")
        elif file_format == "json":
            with open(file_path, "r") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
                else:
                    return [data]
        else:
            raise ValueError(f"Unsupported file format: {file_format}")

    def normalize_dataset(
        self,
        input_file: str,
        output_file: str,
        input_format: str = "auto",
        limit: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Normalize entire dataset"""
        logger.info(f"Starting normalization of {input_file}")

        # Load data
        raw_data = self.load_data(input_file, input_format)
        self.stats["total_records"] = len(raw_data)

        if limit:
            raw_data = raw_data[:limit]
            logger.info(f"Limited to {limit} records for processing")

        # Normalize records
        normalized_records = []
        for i, raw_record in enumerate(raw_data):
            if i % 100 == 0:
                logger.info(f"Processed {i}/{len(raw_data)} records")

            normalized_record = self.normalize_record(raw_record)
            if normalized_record:
                normalized_records.append(asdict(normalized_record))

        # Save normalized data
        output_data = {
            "metadata": {
                "normalized_at": datetime.now().isoformat(),
                "source_file": str(input_file),
                "total_records": self.stats["total_records"],
                "normalized_records": self.stats["normalized_records"],
                "errors": self.stats["errors"],
                "warnings": self.stats["warnings"],
                "schema_version": "1.0",
            },
            "schema": self._get_schema_documentation(),
            "records": normalized_records,
        }

        with open(output_file, "w") as f:
            json.dump(output_data, f, indent=2, default=str)

        logger.info(f"Normalization complete. Output saved to {output_file}")
        return self.stats

    def _get_schema_documentation(self) -> Dict[str, Any]:
        """Get schema documentation"""
        return {
            "description": "Normalized Austin Construction Permits Schema",
            "version": "1.0",
            "objects": {
                "Location": {
                    "description": "Standardized location information",
                    "fields": {
                        "street_address": "Primary street address",
                        "city": "City name (default: Austin)",
                        "state": "State code (default: TX)",
                        "zip_code": "Normalized ZIP code",
                        "latitude": "Decimal latitude",
                        "longitude": "Decimal longitude",
                        "council_district": "Austin council district number",
                        "census_tract": "Census tract identifier",
                    },
                },
                "Contractor": {
                    "description": "Contractor information",
                    "fields": {
                        "name": "Contractor name or company",
                        "license_number": "Professional license number",
                        "phone": "Normalized phone (XXX-XXX-XXXX)",
                        "address": "Contractor address",
                        "company_type": "Type of contracting company",
                    },
                },
                "Applicant": {
                    "description": "Applicant information",
                    "fields": {
                        "name": "Name of the applicant",
                        "company": "Name of the applicant's company",
                        "phone": "Applicant's phone number",
                        "email": "Applicant's email address",
                        "address": "Applicant's address",
                    },
                },
                "Valuation": {
                    "description": "Financial information",
                    "fields": {
                        "total_valuation": "Total project valuation (USD)",
                        "permit_fee": "Permit fee paid (USD)",
                        "currency": "Currency code (default: USD)",
                    },
                },
                "WorkDetails": {
                    "description": "Work description and specifications",
                    "fields": {
                        "permit_type": "Type of the permit (e.g., Building, Electrical)",
                        "work_class": "Class or category of the work",
                        "description": "Detailed description of the work",
                        "use_category": "Category of use for the work (e.g., Residential, Commercial)",
                    },
                },
                "PermitDates": {
                    "description": "Dates related to the permit",
                    "fields": {
                        "issue_date": "Date the permit was issued (ISO format)",
                        "expiration_date": "Date the permit expires (ISO format)",
                        "application_date": "Date the permit was applied for (ISO format)",
                    },
                },
            },
        }



# Example usage and testing
def main():
    """Main function for testing the normalizer"""

    # Initialize normalizer
    normalizer = AustinPermitsNormalizer()

    input_file = "permit_data.json"
    output_file = "normalized_permit_data.json"

    normalizer.normalize_dataset(input_file, output_file)

    print(f"\nProcessing Statistics:")
    print(f"Total Records: {normalizer.stats['total_records']}")
    print(f"Normalized Records: {normalizer.stats['normalized_records']}")
    print(f"Errors: {normalizer.stats['errors']}")
    print(f"Warnings: {normalizer.stats['warnings']}")


if __name__ == "__main__":
    main()
