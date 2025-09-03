from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

from pynamodb.attributes import (
    BooleanAttribute,
    ListAttribute,
    MapAttribute,
    NumberAttribute,
    UnicodeAttribute,
    UTCDateTimeAttribute,
)
from pynamodb.exceptions import DoesNotExist, PutError
from pynamodb.indexes import AllProjection, GlobalSecondaryIndex
from pynamodb.models import Model


class CitizenshipType(Enum):
    """Enumeration for citizenship types."""
    US_CITIZEN = "U.S. Citizen"
    PERMANENT_RESIDENT = "Permanent Resident"
    NON_RESIDENT_ALIEN = "Non-Resident Alien"


class MaritalStatus(Enum):
    """Enumeration for marital status options."""
    SINGLE = "Single"
    MARRIED = "Married"
    SEPARATED = "Separated"
    DIVORCED = "Divorced"
    WIDOWED = "Widowed"


class HousingSituation(Enum):
    """Enumeration for housing situation types."""
    RENTING = "Renting"
    OWN = "Own"
    LIVING_WITH_OTHERS = "Living with Others"
    OTHER = "Other"


class CreditType(Enum):
    """Enumeration for credit application types."""
    INDIVIDUAL = "Individual application"
    JOINT = "Joint application"


class OccupancyType(Enum):
    """Enumeration for property occupancy types."""
    PRIMARY_RESIDENCE = "Primary Residence"
    SECONDARY_RESIDENCE = "Secondary Residence"
    INVESTMENT_PROPERTY = "Investment Property"


class LoanPurpose(Enum):
    """Enumeration for loan purpose types."""
    PURCHASE = "Purchase"
    REFINANCE = "Refinance"
    CONSTRUCTION = "Construction"
    OTHER = "Other"


class LoanType(Enum):
    """Enumeration for loan types."""
    OTHER_LOAN = "Other Loan"
    INSTALLMENT_LOAN = "Installment Loan"
    REVOLVING_CREDIT = "Revolving Credit"


class ApplicationStatus(Enum):
    """Enumeration for application status values."""
    PENDING = "pending"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    DENIED = "denied"
    WITHDRAWN = "withdrawn"


class BankAccountAttribute(MapAttribute):
    """Bank account information."""
    account_number: UnicodeAttribute = UnicodeAttribute()
    bank: UnicodeAttribute = UnicodeAttribute()
    value: NumberAttribute = NumberAttribute()


class InvestmentAccountAttribute(MapAttribute):
    """Investment account information."""
    account_number: UnicodeAttribute = UnicodeAttribute()
    institution: UnicodeAttribute = UnicodeAttribute()
    value: NumberAttribute = NumberAttribute()


class AssetsAttribute(MapAttribute):
    """Asset information."""
    checking_account: BankAccountAttribute = BankAccountAttribute(null=True)
    savings_account: BankAccountAttribute = BankAccountAttribute(null=True)
    retirement_account: InvestmentAccountAttribute = InvestmentAccountAttribute(null=True)
    stocks: InvestmentAccountAttribute = InvestmentAccountAttribute(null=True)
    other_assets: NumberAttribute = NumberAttribute(null=True)


class DeclarationsAttribute(MapAttribute):
    """Borrower declarations."""
    connections_to_seller: BooleanAttribute = BooleanAttribute()
    other_liens: BooleanAttribute = BooleanAttribute()
    other_mortgage_applications: BooleanAttribute = BooleanAttribute()
    owned_property_past_36_months: BooleanAttribute = BooleanAttribute()
    pending_credit_applications: BooleanAttribute = BooleanAttribute()
    primary_residence: BooleanAttribute = BooleanAttribute()
    undisclosed_financial_assistance: BooleanAttribute = BooleanAttribute()


class MonthlyIncomeAttribute(MapAttribute):
    """Monthly income breakdown."""
    base: NumberAttribute = NumberAttribute()
    bonus: NumberAttribute = NumberAttribute()


class EmploymentInformationAttribute(MapAttribute):
    """Employment details."""
    employer: UnicodeAttribute = UnicodeAttribute()
    position: UnicodeAttribute = UnicodeAttribute()
    address: UnicodeAttribute = UnicodeAttribute()
    phone: UnicodeAttribute = UnicodeAttribute()
    start_date: UnicodeAttribute = UnicodeAttribute()  # MM/DD/YYYY format
    time_in_field: UnicodeAttribute = UnicodeAttribute()
    monthly_income: MonthlyIncomeAttribute = MonthlyIncomeAttribute()


class LoanAttribute(MapAttribute):
    """Individual loan information."""
    account_number: UnicodeAttribute = UnicodeAttribute()
    institution: UnicodeAttribute = UnicodeAttribute()
    type: UnicodeAttribute = UnicodeAttribute()  # Enum value as string
    balance: NumberAttribute = NumberAttribute()
    monthly_payment: NumberAttribute = NumberAttribute()


class LiabilitiesAttribute(MapAttribute):
    """Liability information."""
    loans: ListAttribute[LoanAttribute] = ListAttribute(of=LoanAttribute, default=list)


class LoanInformationAttribute(MapAttribute):
    """Loan request details."""
    purpose: UnicodeAttribute = UnicodeAttribute()  # Enum value as string
    occupancy: UnicodeAttribute = UnicodeAttribute()  # Enum value as string
    property_address: UnicodeAttribute = UnicodeAttribute()
    property_value: NumberAttribute = NumberAttribute()


class LoanOriginatorInformationAttribute(MapAttribute):
    """Loan originator details."""
    loan_originator_name: UnicodeAttribute = UnicodeAttribute()
    loan_originator_nmlsr_id: UnicodeAttribute = UnicodeAttribute()
    originator_state_license_id: UnicodeAttribute = UnicodeAttribute()
    organization: UnicodeAttribute = UnicodeAttribute()
    organization_nmlsr_id: UnicodeAttribute = UnicodeAttribute()
    organization_state_license_id: UnicodeAttribute = UnicodeAttribute()
    address: UnicodeAttribute = UnicodeAttribute()
    phone: UnicodeAttribute = UnicodeAttribute()
    email: UnicodeAttribute = UnicodeAttribute()


class ContactAttribute(MapAttribute):
    """Contact information."""
    current_address: UnicodeAttribute = UnicodeAttribute()
    time_at_address: UnicodeAttribute = UnicodeAttribute()
    housing_situation: UnicodeAttribute = UnicodeAttribute()  # Enum value as string
    housing_payment: NumberAttribute = NumberAttribute()
    phone: UnicodeAttribute = UnicodeAttribute()
    email: UnicodeAttribute = UnicodeAttribute()


class PersonalInformationAttribute(MapAttribute):
    """Personal information."""
    first_name: UnicodeAttribute = UnicodeAttribute()
    last_name: UnicodeAttribute = UnicodeAttribute()
    date_of_birth: UnicodeAttribute = UnicodeAttribute()  # MM/DD/YYYY format
    marital_status: UnicodeAttribute = UnicodeAttribute()  # Enum value as string
    dependents: NumberAttribute = NumberAttribute()
    citizenship: UnicodeAttribute = UnicodeAttribute()  # Enum value as string
    credit_type: UnicodeAttribute = UnicodeAttribute()  # Enum value as string
    contact: ContactAttribute = ContactAttribute()


class ConfigurationAttribute(MapAttribute):
    """Main configuration object."""   
    personal_information: PersonalInformationAttribute = PersonalInformationAttribute()
    employment_information: EmploymentInformationAttribute = EmploymentInformationAttribute()
    assets: AssetsAttribute = AssetsAttribute()
    liabilities: LiabilitiesAttribute = LiabilitiesAttribute()
    loan_information: LoanInformationAttribute = LoanInformationAttribute()
    loan_originator_information: LoanOriginatorInformationAttribute = LoanOriginatorInformationAttribute()
    declarations: DeclarationsAttribute = DeclarationsAttribute()

class MortgageApplication(Model):
    """
    Mortgage Application Model
    """
    
    class Meta:
        table_name = "mortgage-applications"
        region = "us-east-1"
        billing_mode = 'PAY_PER_REQUEST'
        enable_backup = True
    
    application_id: UnicodeAttribute = UnicodeAttribute(hash_key=True, default=str(uuid4()))
    description: UnicodeAttribute = UnicodeAttribute()
    borrower_name: UnicodeAttribute = UnicodeAttribute()
    ssn: UnicodeAttribute = UnicodeAttribute()  # Should be encrypted in production
    loan_amount: NumberAttribute = NumberAttribute()
    status: UnicodeAttribute = UnicodeAttribute(default=ApplicationStatus.PENDING.value)
    version: UnicodeAttribute = UnicodeAttribute(default="1.0")
    
    configuration: ConfigurationAttribute = ConfigurationAttribute()
    
    created_at: UTCDateTimeAttribute = UTCDateTimeAttribute(default=lambda: datetime.now(timezone.utc))
    updated_at: UTCDateTimeAttribute = UTCDateTimeAttribute(default=lambda: datetime.now(timezone.utc))
    
    @classmethod
    def create_application(
        cls,
        borrower_name: str,
        ssn: str,
        loan_amount: Union[int, float, Decimal],
        configuration: Dict[str, Any],
        description: Optional[str] = None,
    ) -> MortgageApplication:
        """
        Factory method to create a new mortgage application.
        
        Args:
            borrower_name: Name of the borrower
            ssn: Social Security Number
            loan_amount: Requested loan amount
            configuration_data: Detailed application configuration
            description: Optional description
            
        Returns:
            New mortgage application instance
            
        Raises:
            ValueError: If required fields are invalid
            PutError: If save operation fails
        """
        if description is None:
            description = f"Mortgage application for {borrower_name}"
        
        now = datetime.now(timezone.utc)
        configuration['created_at'] = str(now)
        configuration['updated_at'] = str(now)
        config = ConfigurationAttribute(**configuration)
        
        try:
            application = cls(
                borrower_name=borrower_name,
                ssn=ssn,
                loan_amount=loan_amount,
                description=description,
                configuration=config,
            )
            
            application.save()
            return application
        except Exception as e:
            raise PutError(f"Failed to create application: {str(e)}") from e
    
    @classmethod
    def get_application_safely(cls, application_id: str) -> Optional[MortgageApplication]:
        """
        Safely retrieve an application by ID.
        
        Args:
            application_id: Application ID to retrieve
            
        Returns:
            Application if found, None otherwise
        """
        try:
            return cls.get(application_id)
        except DoesNotExist:
            return None
        except Exception:
            return None


if __name__ == "__main__":
    # Minimal test assuming table exists
    try:
        # Test basic functionality
        config_data = {
            'created_at': datetime.now(timezone.utc),
            'updated_at': datetime.now(timezone.utc),
            'personal_information': {
                'date_of_birth': '01/01/1980',
                'marital_status': MaritalStatus.SINGLE.value,
                'dependents': 0,
                'citizenship': CitizenshipType.US_CITIZEN.value,
                'credit_type': CreditType.INDIVIDUAL.value,
                'contact': {
                    'current_address': '123 Test St',
                    'time_at_address': '2 years',
                    'housing_situation': HousingSituation.RENTING.value,
                    'housing_payment': 1500,
                    'phone': '555-0124',
                    'email': 'test@example.com'
                }
            },
            'employment_information': {
                'employer': 'Test Corp',
                'position': 'Developer',
                'address': '456 Work Ave',
                'phone': '555-0125',
                'start_date': '01/01/2020',
                'time_in_field': '5 years',
                'monthly_income': {'base': 5000, 'bonus': 500, 'gross_total': 5500}
            },
            'assets': {'total_assets_value': 25000},
            'liabilities': {'loans': [], 'total_monthly_debt': 200},
            'loan_information': {
                'purpose': LoanPurpose.PURCHASE.value,
                'occupancy': OccupancyType.PRIMARY_RESIDENCE.value,
                'property_address': '789 Dream St',
                'property_value': 300000
            },
            'loan_originator_information': {
                'loan_originator_name': 'Test Originator',
                'loan_originator_nmlsr_id': 'TEST123',
                'originator_state_license_id': 'ST123',
                'organization': 'Test Mortgage Co',
                'organization_nmlsr_id': 'ORG123',
                'organization_state_license_id': 'ST456',
                'address': '321 Lender St',
                'phone': '555-0126',
                'email': 'originator@test.com'
            },
            'declarations': {
                'connections_to_seller': False,
                'other_liens': False,
                'other_mortgage_applications': False,
                'owned_property_past_36_months': False,
                'pending_credit_applications': False,
                'primary_residence': True,
                'undisclosed_financial_assistance': False
            }
        }
        
        # Create test application
        app = MortgageApplication.create_application(
            borrower_name="Test Borrower",
            ssn="123-45-6789",
            loan_amount=250000,
            configuration=config_data
        )
        
        print(f"✅ Created application: {app.application_id}")
        print(f"Status: {app.status}")
        print(f"Loan amount: ${app.loan_amount:,.2f}")
        print("✅ All tests passed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
