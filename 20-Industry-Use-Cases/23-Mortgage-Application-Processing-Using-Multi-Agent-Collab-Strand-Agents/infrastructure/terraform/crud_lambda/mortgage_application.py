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


class FinancialAccountAttribute(MapAttribute):
    """Financial account information."""
    type: UnicodeAttribute = UnicodeAttribute()  # checking, savings, retirement, stocks, other
    account_number: UnicodeAttribute = UnicodeAttribute()
    institution: UnicodeAttribute = UnicodeAttribute()
    value: NumberAttribute = NumberAttribute()


class AssetsAttribute(MapAttribute):
    """Asset information."""
    accounts: ListAttribute[FinancialAccountAttribute] = ListAttribute(of=FinancialAccountAttribute)
    other_assets: NumberAttribute = NumberAttribute(null=True)


class DeclarationAttribute(MapAttribute):
    """Individual declaration question and answer."""
    question: UnicodeAttribute = UnicodeAttribute()
    answer: BooleanAttribute = BooleanAttribute()


class IncomeAttribute(MapAttribute):
    """Monthly income breakdown."""
    base: NumberAttribute = NumberAttribute()
    bonus: NumberAttribute = NumberAttribute()


class DurationAttribute(MapAttribute):
    """Duration in years and months."""
    years: NumberAttribute = NumberAttribute()
    months: NumberAttribute = NumberAttribute()


class EmploymentInformationAttribute(MapAttribute):
    """Employment details."""
    employer: UnicodeAttribute = UnicodeAttribute()
    address: UnicodeAttribute = UnicodeAttribute()
    phone: UnicodeAttribute = UnicodeAttribute()
    position: UnicodeAttribute = UnicodeAttribute()
    monthly_income: IncomeAttribute = IncomeAttribute()
    start_date: UnicodeAttribute = UnicodeAttribute()  # ISO date format
    time_in_field: DurationAttribute = DurationAttribute()


class LoanAccountAttribute(MapAttribute):
    """Individual loan information."""
    account_number: UnicodeAttribute = UnicodeAttribute()
    institution: UnicodeAttribute = UnicodeAttribute()
    balance: NumberAttribute = NumberAttribute()
    monthly_payment: NumberAttribute = NumberAttribute()
    type: UnicodeAttribute = UnicodeAttribute()  # Other Loan, Installment Loan, Revolving Credit


class PropertyAttribute(MapAttribute):
    """Property information."""
    address: UnicodeAttribute = UnicodeAttribute()
    value: NumberAttribute = NumberAttribute()


class LoanInformationAttribute(MapAttribute):
    """Loan request details."""
    purpose: UnicodeAttribute = UnicodeAttribute()  # Purchase, Refinance, Construction, Other
    occupancy: UnicodeAttribute = UnicodeAttribute()  # Primary Residence, Secondary Residence, Investment Property
    property: PropertyAttribute = PropertyAttribute()


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


class ContactInformationAttribute(MapAttribute):
    """Contact information."""
    current_address: UnicodeAttribute = UnicodeAttribute()
    time_at_address: DurationAttribute = DurationAttribute()
    cell_phone: UnicodeAttribute = UnicodeAttribute()
    home_phone: UnicodeAttribute = UnicodeAttribute(null=True)
    email: UnicodeAttribute = UnicodeAttribute()
    housing_payment: NumberAttribute = NumberAttribute()
    housing_situation: UnicodeAttribute = UnicodeAttribute()  # Renting, Own, Living with Others, Other


class PersonalInformationAttribute(MapAttribute):
    """Personal information."""
    date_of_birth: UnicodeAttribute = UnicodeAttribute()  # ISO date format
    citizenship: UnicodeAttribute = UnicodeAttribute()  # U.S. Citizen, Permanent Resident, Non-Resident Alien
    marital_status: UnicodeAttribute = UnicodeAttribute()  # Single, Married, Separated, Divorced, Widowed
    dependents: NumberAttribute = NumberAttribute()
    credit_type: UnicodeAttribute = UnicodeAttribute()  # Individual application, Joint application
    contact: ContactInformationAttribute = ContactInformationAttribute()


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
    borrower_name: UnicodeAttribute = UnicodeAttribute()
    ssn: UnicodeAttribute = UnicodeAttribute()
    loan_amount: NumberAttribute = NumberAttribute()
    assets: AssetsAttribute = AssetsAttribute()
    declarations: ListAttribute[DeclarationAttribute] = ListAttribute(of=DeclarationAttribute)
    employment_information: EmploymentInformationAttribute = EmploymentInformationAttribute()
    liabilities: ListAttribute[LoanAccountAttribute] = ListAttribute(of=LoanAccountAttribute)
    loan_information: LoanInformationAttribute = LoanInformationAttribute()
    loan_originator_information: LoanOriginatorInformationAttribute = LoanOriginatorInformationAttribute()
    personal_information: PersonalInformationAttribute = PersonalInformationAttribute()
    
    # Additional fields for internal use
    status: UnicodeAttribute = UnicodeAttribute(default=ApplicationStatus.PENDING.value)
    version: UnicodeAttribute = UnicodeAttribute(default="1.0")
    description: UnicodeAttribute = UnicodeAttribute()
    created_at: UTCDateTimeAttribute = UTCDateTimeAttribute(default=lambda: datetime.now(timezone.utc))
    updated_at: UTCDateTimeAttribute = UTCDateTimeAttribute(default=lambda: datetime.now(timezone.utc))
    
    @classmethod
    def create_application(
        cls,
        borrower_name: str,
        ssn: str,
        loan_amount: Union[int, float, Decimal],
        assets: Dict[str, Any],
        declarations: List[Dict[str, Any]],
        employment_information: Dict[str, Any],
        liabilities: List[Dict[str, Any]],
        loan_information: Dict[str, Any],
        loan_originator_information: Dict[str, Any],
        personal_information: Dict[str, Any],
    ) -> MortgageApplication:
        """
        Factory method to create a new mortgage application.
        """
        try:
            application = cls(
                borrower_name=borrower_name,
                ssn=ssn,
                loan_amount=loan_amount,
                assets=AssetsAttribute(**assets),
                declarations=[DeclarationAttribute(**d) for d in declarations],
                employment_information=EmploymentInformationAttribute(**employment_information),
                liabilities=[LoanAccountAttribute(**l) for l in liabilities],
                loan_information=LoanInformationAttribute(**loan_information),
                loan_originator_information=LoanOriginatorInformationAttribute(**loan_originator_information),
                personal_information=PersonalInformationAttribute(**personal_information),
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
        # Create test application
        app = MortgageApplication.create_application(
            borrower_name="Test Borrower",
            ssn="123-45-6789",
            loan_amount=250000,
            assets={
                'accounts': [
                    {'type': 'checking', 'account_number': '12345', 'institution': 'Test Bank', 'value': 15000}
                ],
                'other_assets': 5000
            },
            declarations=[
                {'question': 'Do you have any connections to the seller?', 'answer': False}
            ],
            employment_information={
                'employer': 'Test Corp',
                'address': '456 Work Ave',
                'phone': '555-0125',
                'position': 'Developer',
                'monthly_income': {'base': 5000, 'bonus': 500},
                'start_date': '2020-01-01',
                'time_in_field': {'years': 5, 'months': 0}
            },
            liabilities=[
                {'account_number': 'CC123', 'institution': 'Credit Card Co', 'balance': 2000, 'monthly_payment': 100, 'type': 'Revolving Credit'}
            ],
            loan_information={
                'purpose': 'Purchase',
                'occupancy': 'Primary Residence',
                'property': {'address': '789 Dream St', 'value': 300000}
            },
            loan_originator_information={
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
            personal_information={
                'date_of_birth': '1980-01-01',
                'citizenship': 'U.S. Citizen',
                'marital_status': 'Single',
                'dependents': 0,
                'credit_type': 'Individual application',
                'contact': {
                    'current_address': '123 Test St',
                    'time_at_address': {'years': 2, 'months': 0},
                    'cell_phone': '555-0124',
                    'email': 'test@example.com',
                    'housing_payment': 1500,
                    'housing_situation': 'Renting'
                }
            }
        )
        
        print(f"✅ Created application: {app.application_id}")
        print(f"Status: {app.status}")
        print(f"Loan amount: ${app.loan_amount:,.2f}")
        print("✅ All tests passed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
