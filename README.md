# Austin Permits Data Normalization Pipeline

## Overview

This repository contains a data normalization pipeline for processing Austin construction permit data. The pipeline converts raw permit data into a clean, modular JSON schema, ensuring consistency and usability for further analysis or AI/ML applications.

The pipeline is designed to handle ~70 fields of inconsistent data, normalize them, and return a standardized output. It also manages edge cases, including null or missing values, and ensures that the code is reusable across different cities.

---

## 1. **Normalized Schema**

### **Location Object**
Standardized location information for each permit, including geographic and administrative details.

- **street_address**: The street address of the permit location (string).
- **city**: The city where the permit is located (default: "Austin") (string).
- **state**: The state where the permit is located (default: "TX") (string).
- **zip_code**: The ZIP code of the location (string).
- **latitude**: Latitude coordinate of the location (float).
- **longitude**: Longitude coordinate of the location (float).
- **council_district**: Austin city council district number (integer).

### **Contractor Object**
Contractor-related information, including company name, license details, and contact information.

- **name**: Name of the contractor (string).
- **license_number**: Contractor's professional license number (string).
- **phone**: Contractor's phone number in the format `XXX-XXX-XXXX` (string).
- **address**: Address of the contractor (string).
- **company_type**: Type of contracting company (string).

### **Applicant Object**
Information about the permit applicant.

- **name**: Name of the applicant (string).
- **company**: Name of the applicant's company (string).
- **phone**: Applicant's phone number (string).
- **email**: Applicant's email address (string).
- **address**: Applicant's address (string).

### **Valuation Object**
Valuation and financial information about the construction project.

- **total_valuation**: Total project valuation (float, USD).
- **permit_fee**: Permit fee paid (float, USD).
- **currency**: Currency code (default: "USD") (string).

### **WorkDetails Object**
Describes the work related to the permit, including the type of work and specifications.

- **permit_type**: Type of the permit (e.g., Building, Electrical, Mechanical) (string).
- **work_class**: Work class or category (string).
- **description**: Description of the work being performed (string).
- **use_category**: Category of use (string).


### **PermitDates Object**
Standardized date information for the permit.

- **issue_date**: Date when the permit was issued (ISO format, string).
- **expiration_date**: Date when the permit expires (ISO format, string).
- **application_date**: Date when the permit was applied for (ISO format, string).

### **NormalizedPermit Object**
This is the main object that holds the normalized information for each permit.

- **permit_id**: Unique identifier for the permit (string).
- **permit_number**: Permit number (string, optional).
- **status**: Status of the permit (string, optional).
- **location**: Standardized location object.
- **contractor**: Standardized contractor object.
- **applicant**: Standardized applicant object.
- **valuation**: Standardized valuation object.
- **work_details**: Standardized work details object (newly added).
- **dates**: Standardized date object.
- **metadata**: Metadata related to the normalization process, such as the timestamp and data quality score (dictionary).

---

## 2. **Logic Decisions**

### **Normalization Logic**
- **Grouping Fields**: Related fields such as location, contractor, and applicant information are grouped into respective sub-objects, making it easier to query.
- **Renaming Fields**: Ambiguous or inconsistent field names (e.g., `original_address1` → `street_address`) are mapped to standardized field names to ensure consistency.
- **Date Formatting**: All dates are converted to **ISO format** (`YYYY-MM-DD`), which is a standard date format.
- **Data Type Standardization**: Currency values are normalized to `float`, and phone numbers are standardized to the `XXX-XXX-XXXX` format.

### **Handling Missing or Null Data**
- **Default Values**: Default values like `"Austin"` for city and `"TX"` for state are used when missing. This ensures no critical information is left blank.
- **Skip Invalid or Empty Fields**: If a field is `None`, `NaN`, or empty, it is skipped, avoiding incorrect or incomplete data in the final output.
- **Handling Missing ZIP Codes**: ZIP codes are fetched from an external API (OpenStreetMap Nominatim API) if missing.

### **Data Integrity**
- **Duplicate Handling**: Redundant or conflicting fields (e.g., `permit_class` vs. `permit_class_mapped`) are prioritized based on their relevance or completeness.
- **External Data Sources**: Missing ZIP codes are fetched using an external service (OpenStreetMap Nominatim API).

---

## 3. **Assumptions + Tradeoffs**

### **Assumptions**
- **Geographic Location**: The default city is assumed to be Austin, the state is assumed to be TX, and the country is assumed to be US for most records.
- **Uniformity of Permit Types**: The pipeline assumes that permit types will be from a predefined list (Building, Electrical, Mechanical, etc.), with possible expansion in the future.
- **Date Formats**: It is assumed that input data may contain several different date formats, but only the first valid format is considered for normalization.

### **Tradeoffs**
- **External API Dependency**: The reliance on the OpenStreetMap Nominatim API introduces a potential failure point if the service is slow or unavailable. This introduces a tradeoff between automation and external dependency.
- **Handling Null or Missing Fields**: By skipping empty or null fields, the script avoids introducing incorrect data but may result in incomplete records. This tradeoff is essential to maintain data integrity but could affect completeness.
- **Default Values**: The use of default values for `city` and `state` is a tradeoff between convenience and accuracy, assuming that most records are for Austin. This might lead to inaccuracies if records for other cities are included.

---

## 4. **How to Run**

### **Installation**
1. Clone this repository:
   ```bash
   git clone https://github.com/safiullahkhan45/ConstructIQ.git
   cd ConstructIQ
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### **Running the Pipeline**
1. Run the pipeline:
   ```bash
   python pipeline.py
   ```

2. Check the output: `normalized_permit_data.json`

---