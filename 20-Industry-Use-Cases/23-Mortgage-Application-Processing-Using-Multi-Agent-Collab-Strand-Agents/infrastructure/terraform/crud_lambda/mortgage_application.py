from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Union
from uuid import uuid4

from pynamodb.attributes import (
    BooleanAttribute,
    ListAttribute,
    MapAttribute,
    NumberAttribute,
    UnicodeAttribute,
    UTCDateTimeAttribute,
)
from pynamodb.exceptions import PutError
from pynamodb.indexes import AllProjection, GlobalSecondaryIndex
from pynamodb.models import Model

class CitizenshipType(Enum):
    US_CITIZEN = "U.S. Citizen"
    PERMANENT_RESIDENT = "Permanent Resident"
    NON_RESIDENT_ALIEN = "Non-Resident Alien"


class MaritalStatus(Enum):
    SINGLE = "Single"
    MARRIED = "Married"
    SEPARATED = "Separated"
    DIVORCED = "Divorced"
    WIDOWED = "Widowed"


class HousingSituation(Enum):
    RENTING = "Renting"
    OWN = "Own"
    LIVING_WITH_OTHERS = "Living with Others"
    OTHER = "Other"


class CreditType(Enum):
    INDIVIDUAL = "Individual application"
    JOINT = "Joint application"


class OccupancyType(Enum):
    PRIMARY_RESIDENCE = "Primary Residence"
    SECONDARY_RESIDENCE = "Secondary Residence"
    INVESTMENT_PROPERTY = "Investment Property"


class LoanPurpose(Enum):
    PURCHASE = "Purchase"
    REFINANCE = "Refinance"
    CONSTRUCTION = "Construction"
    OTHER = "Other"


class LoanType(Enum):
    OTHER_LOAN = "Other Loan"
    INSTALLMENT_LOAN = "Installment Loan"
    REVOLVING_CREDIT = "Revolving Credit"


class ApplicationStatus(Enum):
    PENDING = "pending"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    DENIED = "denied"
    WITHDRAWN = "withdrawn"


class StatusIndex(GlobalSecondaryIndex):
    """
    GSI for querying applications by status.
    """
    class Meta:
        index_name = "status-index"
        projection = AllProjection()
        billing_mode = "PAY_PER_REQUEST"

    status = UnicodeAttribute(hash_key=True)


class SSNIndex(GlobalSecondaryIndex):
    """
    GSI for querying applications by SSN.
    NOTE: In production, encrypt or mask SSN to meet compliance.
    """
    class Meta:
        index_name = "borrower-ssn-index"
        projection = AllProjection()
        billing_mode = "PAY_PER_REQUEST"

    ssn = UnicodeAttribute(hash_key=True)


class FinancialAccountAttribute(MapAttribute):
    """Financial account information."""
    type = UnicodeAttribute()  # checking, savings, retirement, etc.
    institution = UnicodeAttribute()
    account_number = UnicodeAttribute()
    value = NumberAttribute()


class AssetsAttribute(MapAttribute):
    """Asset information."""
    accounts = ListAttribute(of=FinancialAccountAttribute)


class EmployerAttribute(MapAttribute):
    """Employment history record."""
    employer = UnicodeAttribute()
    position = UnicodeAttribute()
    address = UnicodeAttribute()
    monthly_base_income = NumberAttribute()
    monthly_bonus_income = NumberAttribute(null=True)
    start_date = UnicodeAttribute()  # ISO format
    end_date = UnicodeAttribute(null=True)  # if left


class ContactInformationAttribute(MapAttribute):
    """Contact info."""
    address = UnicodeAttribute()
    cell_phone = UnicodeAttribute()
    email = UnicodeAttribute()
    home_phone = UnicodeAttribute(null=True)
    housing_payment = NumberAttribute()
    housing_situation = UnicodeAttribute()


class PersonalInformationAttribute(MapAttribute):
    """Personal info."""
    date_of_birth = UnicodeAttribute()
    citizenship = UnicodeAttribute()
    marital_status = UnicodeAttribute()
    dependents = NumberAttribute()
    credit_type = UnicodeAttribute()
    contact = ContactInformationAttribute()


class LoanAccountAttribute(MapAttribute):
    type = UnicodeAttribute()
    institution = UnicodeAttribute()
    account_number = UnicodeAttribute()
    balance = NumberAttribute()
    monthly_payment = NumberAttribute()


class PropertyAttribute(MapAttribute):
    address = UnicodeAttribute()
    value = NumberAttribute()


class LoanInformationAttribute(MapAttribute):
    purpose = UnicodeAttribute()
    occupancy = UnicodeAttribute()
    property = PropertyAttribute()


class DeclarationAttribute(MapAttribute):
    question = UnicodeAttribute()
    answer = BooleanAttribute()


class MortgageApplication(Model):
    """
    Optimized Mortgage Application Model
    """

    class Meta:
        table_name = "mortgage-applications"
        region = "us-east-1"
        billing_mode = "PAY_PER_REQUEST"
        enable_backup = True

    application_id = UnicodeAttribute(hash_key=True, default_for_new=lambda: str(uuid4()))

    status = UnicodeAttribute(default=ApplicationStatus.PENDING.value)
    status_index: StatusIndex = StatusIndex()

    ssn = UnicodeAttribute()
    ssn_index: SSNIndex = SSNIndex()

    borrower_name = UnicodeAttribute()
    loan_amount = NumberAttribute()
    personal_information = PersonalInformationAttribute()
    employment_history = ListAttribute(of=EmployerAttribute)
    assets = AssetsAttribute()
    liabilities = ListAttribute(of=LoanAccountAttribute)
    loan_information = LoanInformationAttribute()
    declarations = ListAttribute(of=DeclarationAttribute)

    version = UnicodeAttribute(default="1.0")
    created_at = UTCDateTimeAttribute(default=lambda: datetime.now(timezone.utc))
    updated_at = UTCDateTimeAttribute(default=lambda: datetime.now(timezone.utc))

    @classmethod
    def create_application(
        cls,
        borrower_name: str,
        ssn: str,
        loan_amount: Union[int, float, Decimal],
        assets: Dict[str, Any],
        employment_history: List[Dict[str, Any]],
        liabilities: List[Dict[str, Any]],
        loan_information: Dict[str, Any],
        personal_information: Dict[str, Any],
        declarations: List[Dict[str, bool]],
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
                employment_history=[EmployerAttribute(**e) for e in employment_history],
                liabilities=[LoanAccountAttribute(**l) for l in liabilities],
                loan_information=LoanInformationAttribute(**loan_information),
                personal_information=PersonalInformationAttribute(**personal_information),
                declarations=[DeclarationAttribute(**d) for d in declarations],
            )
            application.save()
            return application
        except Exception as e:
            raise PutError(f"Failed to create application: {str(e)}") from e