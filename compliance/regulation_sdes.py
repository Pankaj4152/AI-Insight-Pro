REGULATION_SDEs = {
    # GDPR is a comprehensive regulation, suitable for various industries.
    "GDPR": {
        "industry": ["Finance", "Retail Ecommerce", "Telecommunications", "Marketing Advertising"],
        "required_sdes": [
            "full_name",
            "email",
            "address",
            "phone_number",
            "bank_account_number",
            "ip_address",
            "credit_card_number",
            "dob"
        ]
    },
    # HIPAA is specific to the healthcare industry.
    "HIPAA": {
        "industry": ["Healthcare"],
        "required_sdes": [
            "full_name",
            "email",
            "address",
            "phone_number",
            "medical_record_number",
            "dob",
            "ssn",
            "diagnosis",
            "treatment_details",
            "prescription"
        ]
    },
    # PCI DSS is for any company that handles credit card data.
    "PCI": {
        "industry": ["Finance", "Retail Ecommerce", "Restaurants", "Hospitality"],
        "required_sdes": [
            "full_name",
            "email",
            "address",
            "phone_number",
            "credit_card_number",
            "bank_account_number"
        ]
    },
    # DPDP (Digital Personal Data Protection) is a broad, India-specific regulation.
    "DPDP": {
        "industry": ["All Industries", "Government", "Education", "Manufacturing", "Transportation Logistics", "Human Resources"],
        "required_sdes": [
            "full_name",
            "email",
            "address",
            "phone_number",
            "aadhaar_number",
            "passport_number",
            "driving_license_number",
            "ssn"
        ]
    }
}

def get_regulation_sdes(regulation_name):
    """
    Returns the required SDEs for a given regulation name.
    """
    return REGULATION_SDEs.get(regulation_name)

def get_regulation_by_industry(industry):
    """
    Finds the regulation name based on the client's industry.
    This now handles multiple industries per regulation.
    """
    for reg_name, details in REGULATION_SDEs.items():
        if industry in details["industry"]:
            return reg_name
    return None
