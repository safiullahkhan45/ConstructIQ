"""
Data normalization service - Enhanced from original pipeline
"""

import json
import re
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import asdict
from pathlib import Path
import requests
import time

from app.models.permit import (
    Location, Contractor, Applicant, Valuation, 
    WorkDetails, PermitDates, NormalizedPermit
)
from app.core.logging import logger


class AustinPermitsNormalizer:
    """Enhanced normalizer with vector search capabilities"""

    def __init__(self):
        # Default configuration instead of importing settings
        self.config = {
            "date_formats": [
                "%Y-%m-%d", 
                "%m/%d/%Y", 
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%dT%H:%M:%S.%f"
            ],
            "currency_symbols": ["$", "USD", "usd"],
            "zip_pattern": r"\d{5}(-\d{4})?"
        }
        
        self.field_mappings = self._initialize_field_mappings()
        self.stats = {
            "total_records": 0,
            "normalized_records": 0,
            "errors": 0,
            "warnings": 0,
            "zip_codes_filled": 0,
            "geocoding_failures": 0,
        }

    def _initialize_field_mappings(self) -> Dict[str, str]:
        """Initialize field mappings for common Austin permit field variations"""
        return {
            # Permit identification
            "permit_num": "permit_number", "permit_number": "permit_number",
            "permitnumber": "permit_number", "permit_id": "permit_id",
            "permitid": "permit_id", "permit_no": "permit_number",
            
            # Location fields
            "original_address1": "street_address", "street_address": "street_address",
            "address": "street_address", "permit_location": "street_address",
            "original_city": "city", "original_state": "state", "original_zip": "zip_code",
            "zip_code": "zip_code", "zipcode": "zip_code",
            "council_district_code": "council_district", "council_dist": "council_district",
            "council_district": "council_district",
            "latitude": "latitude", "longitude": "longitude",
            "lat": "latitude", "lng": "longitude", "long": "longitude",
            
            # Contractor fields
            "contractor_name": "contractor_name", "contractor_company_name": "contractor_name",
            "contractor_trade_name": "contractor_name", "contractor_phone": "contractor_phone",
            "contractor_phone_number": "contractor_phone", "contractor_address": "contractor_address",
            "license_number": "contractor_license", "contractor_license_number": "contractor_license",
            
            # Applicant fields
            "applicant_name": "applicant_name", "applicant_company": "applicant_company",
            "applicant_phone": "applicant_phone", "applicant_email": "applicant_email",
            "applicant_address": "applicant_address", "owner_name": "applicant_name",
            
            # Valuation fields
            "total_valuation": "total_valuation", "totalvaluation": "total_valuation",
            "valuation": "total_valuation", "permit_fee": "permit_fee", "fee_amount": "permit_fee",
            
            # Work details
            "permit_type_desc": "permit_type", "permit_type": "permit_type",
            "permittype": "permit_type", "work_class": "work_class",
            "permit_class": "work_class", "permit_class_mapped": "work_class",
            "description": "work_description", "work_description": "work_description", 
            "scope_of_work": "work_description",
            "use_category": "use_category", "use_type": "use_category",
            
            # Date fields
            "issue_date": "issue_date", "issued_date": "issue_date", "date_issued": "issue_date",
            "expiration_date": "expiration_date", "expire_date": "expiration_date",
            "expiresdate": "expiration_date",
            "application_date": "application_date", "applied_date": "application_date",
            "applieddate": "application_date",
            
            # Status fields
            "status": "status", "permit_status": "status", "current_status": "status",
            "status_current": "status",
        }

    def normalize_date(self, date_value: Any) -> Optional[str]:
        """Normalize various date formats to ISO format"""
        if pd.isna(date_value) or date_value is None or str(date_value).strip() == "":
            return None

        date_str = str(date_value).strip()

        for fmt in self.config["date_formats"]:
            try:
                parsed_date = datetime.strptime(date_str, fmt)
                return parsed_date.strftime("%Y-%m-%d")
            except ValueError:
                continue

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

        value_str = str(value).strip()
        for symbol in self.config["currency_symbols"]:
            value_str = value_str.replace(symbol, "")
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
        digits = re.sub(r"\D", "", phone_str)

        if len(digits) == 10:
            return f"{digits[:3]}-{digits[3:6]}-{digits[6:]}"
        elif len(digits) == 11 and digits[0] == "1":
            return f"{digits[1:4]}-{digits[4:7]}-{digits[7:]}"
        else:
            return phone_str if phone_str else None

    def get_zip_code(self, street_address: str, city: str = "Austin", state: str = "TX") -> Optional[str]:
        """
        Get the zip code based on the street address using Nominatim API (OpenStreetMap)
        """
        if not street_address or not street_address.strip():
            return None
            
        try:
            # Clean and format the address
            address = street_address.strip()
            city = city or "Austin"
            state = state or "TX"
            
            query = f"{address}, {city}, {state}, US"
            url = "https://nominatim.openstreetmap.org/search"
            
            params = {
                "format": "json",
                "addressdetails": "1",
                "q": query,
                "limit": "1"
            }
            
            headers = {
                "User-Agent": "AustinPermitsAPI/1.0 (constructiq-permits@example.com)"
            }
            
            # Add a small delay to be respectful to the API
            time.sleep(0.1)
            
            response = requests.get(url, params=params, headers=headers, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                
                if data and len(data) > 0:
                    address_details = data[0].get("address", {})
                    zip_code = address_details.get("postcode")
                    
                    if zip_code:
                        # Validate zip code format
                        if re.match(self.config["zip_pattern"], zip_code):
                            logger.info(f"Found zip code {zip_code} for address: {address}")
                            self.stats["zip_codes_filled"] += 1
                            return zip_code
                        else:
                            logger.warning(f"Invalid zip code format returned: {zip_code}")
            
            logger.warning(f"Could not get zip code for address: {address}, {city}, {state}")
            self.stats["geocoding_failures"] += 1
            return None
            
        except requests.RequestException as e:
            logger.warning(f"Geocoding API request failed for {street_address}: {e}")
            self.stats["geocoding_failures"] += 1
            return None
        except Exception as e:
            logger.warning(f"Unexpected error during geocoding for {street_address}: {e}")
            self.stats["geocoding_failures"] += 1
            return None

    def normalize_zip_code(
        self, zip_code: Any, street_address: str = "", city: str = "Austin", state: str = "TX"
    ) -> Optional[str]:
        """Normalize zip codes and fill missing ones using geocoding"""
        
        # First, try to normalize existing zip code
        if not pd.isna(zip_code) and zip_code is not None:
            zip_str = str(zip_code).strip()
            if zip_str:  # Not empty
                # Extract zip code pattern
                match = re.search(self.config["zip_pattern"], zip_str)
                if match:
                    return match.group(0)
        
        # If zip code is missing or invalid, try to get it from address
        if street_address and street_address.strip():
            logger.info(f"Attempting to fill missing zip code for address: {street_address}")
            return self.get_zip_code(street_address, city, state)
        
        return None

    def map_field_name(self, original_name: str) -> str:
        """Map original field names to standardized names"""
        normalized_name = re.sub(r"[^a-zA-Z0-9_]", "_", original_name.lower().strip())
        normalized_name = re.sub(r"_+", "_", normalized_name).strip("_")
        return self.field_mappings.get(normalized_name, normalized_name)

    def handle_duplicate_fields(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Handle duplicate or conflicting fields"""
        cleaned_record = {}
        for key, value in record.items():
            mapped_key = self.map_field_name(key)
            if pd.isna(value) or str(value).strip() == "":
                continue
                
            if mapped_key in cleaned_record:
                current_len = len(str(cleaned_record[mapped_key]))
                new_len = len(str(value))
                if new_len > current_len:
                    cleaned_record[mapped_key] = value
            else:
                cleaned_record[mapped_key] = value

        return cleaned_record

    def create_objects(self, record: Dict[str, Any]) -> tuple:
        """Create all standardized objects from record"""
        location = Location(
            street_address=record.get("street_address"),
            city=record.get("city", "Austin"),
            state=record.get("state", "TX"),
            zip_code=self.normalize_zip_code(
                record.get("zip_code"),
                street_address=record.get("street_address", ""),
                city=record.get("city", "Austin"),
                state=record.get("state", "TX")
            ),
            latitude=pd.to_numeric(record.get("latitude"), errors="coerce") or None,
            longitude=pd.to_numeric(record.get("longitude"), errors="coerce") or None,
            council_district=pd.to_numeric(record.get("council_district"), errors="coerce") or None,
            census_tract=record.get("census_tract"),
        )

        contractor = Contractor(
            name=record.get("contractor_name"),
            license_number=record.get("contractor_license"),
            phone=self.normalize_phone(record.get("contractor_phone")),
            address=record.get("contractor_address"),
            company_type=record.get("contractor_type"),
        )

        applicant = Applicant(
            name=record.get("applicant_name"),
            company=record.get("applicant_company"),
            phone=self.normalize_phone(record.get("applicant_phone")),
            email=record.get("applicant_email"),
            address=record.get("applicant_address"),
        )

        valuation = Valuation(
            total_valuation=self.normalize_currency(record.get("total_valuation")),
            permit_fee=self.normalize_currency(record.get("permit_fee")),
            currency="USD",
        )

        work_details = WorkDetails(
            permit_type=record.get('permit_type'),
            work_class=record.get('work_class'),
            description=record.get('work_description'),
            use_category=record.get('use_category')
        )

        dates = PermitDates(
            issue_date=self.normalize_date(record.get("issue_date")),
            expiration_date=self.normalize_date(record.get("expiration_date")),
            application_date=self.normalize_date(record.get("application_date")),
        )

        return location, contractor, applicant, valuation, work_details, dates

    def normalize_record(self, raw_record: Dict[str, Any]) -> Optional[NormalizedPermit]:
        """Normalize a single permit record"""
        try:
            self.stats["total_records"] += 1
            cleaned_record = self.handle_duplicate_fields(raw_record)

            permit_id = cleaned_record.get("permit_id") or cleaned_record.get("permit_number")
            if not permit_id:
                permit_id = f"permit_{hash(str(raw_record)) % 1000000}"

            location, contractor, applicant, valuation, work_details, dates = self.create_objects(cleaned_record)

            normalized_permit = NormalizedPermit(
                permit_id=str(permit_id),
                permit_number=cleaned_record.get("permit_number"),
                status=cleaned_record.get("status"),
                location=location,
                contractor=contractor,
                applicant=applicant,
                valuation=valuation,
                work_details=work_details,
                dates=dates,
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

        for field in essential_fields:
            total_weight += 2.0
            if record.get(field):
                score += 2.0

        other_fields = set(record.keys()) - set(essential_fields)
        for field in other_fields:
            total_weight += 1.0
            if record.get(field):
                score += 1.0

        return score / total_weight if total_weight > 0 else 0.0

    def load_data(self, file_path: str, file_format: str = "auto") -> List[Dict[str, Any]]:
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
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Normalize dataset and return normalized records"""
        logger.info(f"Starting normalization of {input_file}")

        # Load data
        raw_data = self.load_data(input_file)
        self.stats["total_records"] = len(raw_data)

        if limit:
            raw_data = raw_data[:limit]
            logger.info(f"Limited to {limit} records for processing")

        # Normalize records
        normalized_records = []
        for i, raw_record in enumerate(raw_data):
            if i % 10 == 0:
                logger.info(f"Processed {i}/{len(raw_data)} records")

            normalized_record = self.normalize_record(raw_record)
            if normalized_record:
                normalized_records.append(asdict(normalized_record))

        logger.info(f"Normalization complete. Processed {len(normalized_records)} records")
        logger.info(f"Zip codes filled: {self.stats['zip_codes_filled']}, Geocoding failures: {self.stats['geocoding_failures']}")
        return normalized_records