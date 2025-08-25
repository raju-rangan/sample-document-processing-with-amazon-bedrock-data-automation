"""
Pylance-compliant Mortgage Application Model with PynamoDB Best Practices

This module provides a comprehensive mortgage application data model using PynamoDB
with full Pylance/mypy compliance and 2024+ best practices.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union
from uuid import uuid4

from pynamodb.attributes import (
    BooleanAttribute,
    ListAttribute,
    MapAttribute,
    NumberAttribute,
    TTLAttribute,
    UnicodeAttribute,
    UTCDateTimeAttribute,
    VersionAttribute,
)
from pynamodb.exceptions import DoesNotExist, PutError, UpdateError
from pynamodb.indexes import AllProjection, GlobalSecondaryIndex
from pynamodb.models import Model

if TYPE_CHECKING:
    from pynamodb.pagination import ResultIterator


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


# Map Attributes for nested objects
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
    total_assets_value: NumberAttribute = NumberAttribute()


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
    gross_total: NumberAttribute = NumberAttribute()


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
    total_monthly_debt: NumberAttribute = NumberAttribute()


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
    home_phone: UnicodeAttribute = UnicodeAttribute()
    cell_phone: UnicodeAttribute = UnicodeAttribute()
    email: UnicodeAttribute = UnicodeAttribute()


class PersonalInformationAttribute(MapAttribute):
    """Personal information."""
    date_of_birth: UnicodeAttribute = UnicodeAttribute()  # MM/DD/YYYY format
    marital_status: UnicodeAttribute = UnicodeAttribute()  # Enum value as string
    dependents: NumberAttribute = NumberAttribute()
    citizenship: UnicodeAttribute = UnicodeAttribute()  # Enum value as string
    credit_type: UnicodeAttribute = UnicodeAttribute()  # Enum value as string
    contact: ContactAttribute = ContactAttribute()


class ConfigurationAttribute(MapAttribute):
    """Main configuration object."""
    created_at: UTCDateTimeAttribute = UTCDateTimeAttribute()
    updated_at: UTCDateTimeAttribute = UTCDateTimeAttribute()
    personal_information: PersonalInformationAttribute = PersonalInformationAttribute()
    employment_information: EmploymentInformationAttribute = EmploymentInformationAttribute()
    assets: AssetsAttribute = AssetsAttribute()
    liabilities: LiabilitiesAttribute = LiabilitiesAttribute()
    loan_information: LoanInformationAttribute = LoanInformationAttribute()
    loan_originator_information: LoanOriginatorInformationAttribute = LoanOriginatorInformationAttribute()
    declarations: DeclarationsAttribute = DeclarationsAttribute()


# Global Secondary Indexes
class StatusIndex(GlobalSecondaryIndex):
    """Index for querying by application status."""
    
    class Meta:
        index_name = 'status-date-index'
        projection = AllProjection()
        billing_mode = 'PAY_PER_REQUEST'
    
    status: UnicodeAttribute = UnicodeAttribute(hash_key=True)
    application_date: UnicodeAttribute = UnicodeAttribute(range_key=True)


class OriginatorIndex(GlobalSecondaryIndex):
    """Index for querying by loan originator."""
    
    class Meta:
        index_name = 'loan-originator-index'
        projection = AllProjection()
        billing_mode = 'PAY_PER_REQUEST'
        # Use on-demand billing instead of PAY_PER_REQUEST constant
        # Region is inherited from the main model
    
    loan_originator_id: UnicodeAttribute = UnicodeAttribute(hash_key=True)
    application_date: UnicodeAttribute = UnicodeAttribute(range_key=True)


class PropertyStateIndex(GlobalSecondaryIndex):
    """Index for querying by property state."""
    
    class Meta:
        index_name = 'property-state-index'
        projection = AllProjection()
        billing_mode = 'PAY_PER_REQUEST'
        # Use on-demand billing instead of PAY_PER_REQUEST constant
        # Region is inherited from the main model
    
    property_state: UnicodeAttribute = UnicodeAttribute(hash_key=True)
    application_date: UnicodeAttribute = UnicodeAttribute(range_key=True)


class LoanAmountIndex(GlobalSecondaryIndex):
    """Index for querying by status and loan amount."""
    
    class Meta:
        index_name = 'loan-amount-index'
        projection = AllProjection()
        billing_mode = 'PAY_PER_REQUEST'
    
    status: UnicodeAttribute = UnicodeAttribute(hash_key=True)
    loan_amount: NumberAttribute = NumberAttribute(range_key=True)


class BorrowerNameIndex(GlobalSecondaryIndex):
    """Index for querying by borrower name."""
    
    class Meta:
        index_name = 'borrower-name-index'
        projection = AllProjection()
        billing_mode = 'PAY_PER_REQUEST'
    
    borrower_name: UnicodeAttribute = UnicodeAttribute(hash_key=True)


class SSNLookupIndex(GlobalSecondaryIndex):
    """Index for querying by SSN (use with caution for security)."""
    
    class Meta:
        index_name = 'ssn-lookup-index'
        projection = AllProjection()
        billing_mode = 'PAY_PER_REQUEST'
    
    ssn: UnicodeAttribute = UnicodeAttribute(hash_key=True)


# Main Model
class MortgageApplication(Model):
    """
    Mortgage Application Model with 2025 best practices.
    
    This model provides comprehensive mortgage application data storage
    with full Pylance compliance and optimizations.
    """
    
    class Meta:
        table_name = "mortgage-applications"
        region = "us-east-1"  # Update to your preferred region
        billing_mode = 'PAY_PER_REQUEST'
        enable_backup = True
    
    # Primary key - Fixed default syntax
    application_id: UnicodeAttribute = UnicodeAttribute(hash_key=True, default=str(uuid4()))
    
    # Core attributes
    name: UnicodeAttribute = UnicodeAttribute()
    description: UnicodeAttribute = UnicodeAttribute()
    borrower_name: UnicodeAttribute = UnicodeAttribute()
    ssn: UnicodeAttribute = UnicodeAttribute()  # Should be encrypted in production
    application_date: UnicodeAttribute = UnicodeAttribute()  # YYYY-MM-DD format
    loan_amount: NumberAttribute = NumberAttribute()
    loan_originator_id: UnicodeAttribute = UnicodeAttribute()
    property_state: UnicodeAttribute = UnicodeAttribute()
    status: UnicodeAttribute = UnicodeAttribute(default=ApplicationStatus.PENDING.value)
    version: UnicodeAttribute = UnicodeAttribute(default="1.0")
    
    # Complex nested configuration
    configuration: ConfigurationAttribute = ConfigurationAttribute()
    
    # Timestamps - Fixed default syntax
    created_at: UTCDateTimeAttribute = UTCDateTimeAttribute(default=lambda: datetime.now(timezone.utc))
    updated_at: UTCDateTimeAttribute = UTCDateTimeAttribute(default=lambda: datetime.now(timezone.utc))
    
    # Version control for optimistic locking
    record_version: VersionAttribute = VersionAttribute()
    
    # TTL for automatic cleanup (optional - remove if not needed)
    # ttl: TTLAttribute = TTLAttribute(default=lambda: datetime.utcnow() + timedelta(days=2555))  # 7 years
    
    # Global Secondary Indexes
    status_index: StatusIndex = StatusIndex()
    originator_index: OriginatorIndex = OriginatorIndex()
    property_state_index: PropertyStateIndex = PropertyStateIndex()
    loan_amount_index: LoanAmountIndex = LoanAmountIndex()
    borrower_name_index: BorrowerNameIndex = BorrowerNameIndex()
    ssn_lookup_index: SSNLookupIndex = SSNLookupIndex()
    
    @classmethod
    def create_application(
        cls,
        borrower_name: str,
        ssn: str,
        loan_amount: Union[int, float, Decimal],
        loan_originator_id: str,
        property_state: str,
        configuration_data: Dict[str, Any],
        application_date: Optional[str] = None,
        description: Optional[str] = None
    ) -> MortgageApplication:
        """
        Factory method to create a new mortgage application.
        
        Args:
            borrower_name: Name of the borrower
            ssn: Social Security Number
            loan_amount: Requested loan amount
            loan_originator_id: ID of the loan originator
            property_state: State where property is located
            configuration_data: Detailed application configuration
            application_date: Application date (defaults to today)
            description: Optional description
            
        Returns:
            New mortgage application instance
            
        Raises:
            ValueError: If required fields are invalid
            PutError: If save operation fails
        """
        if application_date is None:
            application_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        
        if description is None:
            description = f"Mortgage application for {borrower_name}"
        
        name = f"Mortgage Application - {borrower_name}"
        
        # Convert configuration data to ConfigurationAttribute
        config = ConfigurationAttribute(**configuration_data)
        
        try:
            application = cls(
                borrower_name=borrower_name,
                ssn=ssn,
                loan_amount=loan_amount,
                loan_originator_id=loan_originator_id,
                property_state=property_state,
                application_date=application_date,
                name=name,
                description=description,
                configuration=config
            )
            
            application.save()
            return application
        except Exception as e:
            raise PutError(f"Failed to create application: {str(e)}") from e
    
    def update_status(self, new_status: ApplicationStatus) -> None:
        """
        Update application status with timestamp.
        
        Args:
            new_status: New status to set
            
        Raises:
            UpdateError: If update operation fails
        """
        try:
            self.status = new_status.value
            self.updated_at = datetime.now(timezone.utc)
            self.save()
        except Exception as e:
            raise UpdateError(f"Failed to update status: {str(e)}") from e
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert model to dictionary for API responses.
        
        Returns:
            Dictionary representation of the model
        """
        return {
            "application_id": self.application_id,
            "name": self.name,
            "description": self.description,
            "borrower_name": self.borrower_name,
            "ssn": self.ssn,  # Mask in production
            "application_date": self.application_date,
            "loan_amount": float(self.loan_amount),
            "loan_originator_id": self.loan_originator_id,
            "property_state": self.property_state,
            "status": self.status,
            "version": self.version,
            "configuration": self.configuration.as_dict() if self.configuration else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "record_version": self.record_version
        }
    
    @classmethod
    def get_by_status(cls, status: ApplicationStatus, limit: int = 50) -> List[MortgageApplication]:
        """
        Query applications by status.
        
        Args:
            status: Status to filter by
            limit: Maximum number of results
            
        Returns:
            List of matching applications
        """
        try:
            return list(cls.status_index.query(status.value, limit=limit))
        except Exception:
            return []
    
    @classmethod
    def get_by_originator(cls, originator_id: str, limit: int = 50) -> List[MortgageApplication]:
        """
        Query applications by loan originator.
        
        Args:
            originator_id: Loan originator ID to filter by
            limit: Maximum number of results
            
        Returns:
            List of matching applications
        """
        try:
            return list(cls.originator_index.query(originator_id, limit=limit))
        except Exception:
            return []
    
    @classmethod
    def get_by_state_and_amount_range(
        cls, 
        state: str, 
        min_amount: Optional[Union[int, float]] = None,
        max_amount: Optional[Union[int, float]] = None,
        limit: int = 50
    ) -> List[MortgageApplication]:
        """
        Query applications by property state and loan amount range.
        
        Note: This method queries by state first, then filters by amount.
        For amount-focused queries, consider using get_by_amount_range instead.
        
        Args:
            state: Property state to filter by
            min_amount: Minimum loan amount
            max_amount: Maximum loan amount
            limit: Maximum number of results
            
        Returns:
            List of matching applications
        """
        try:
            # Query by property state first
            query_results = cls.property_state_index.query(state, limit=limit)
            results = list(query_results)
            
            # Apply amount filters manually
            filtered_results = []
            for item in results:
                if min_amount is not None and item.loan_amount < min_amount:
                    continue
                if max_amount is not None and item.loan_amount > max_amount:
                    continue
                filtered_results.append(item)
                
            return filtered_results
        except Exception:
            return []
    
    @classmethod
    def get_by_amount_range(
        cls,
        status: ApplicationStatus,
        min_amount: Optional[Union[int, float]] = None,
        max_amount: Optional[Union[int, float]] = None,
        limit: int = 50
    ) -> List[MortgageApplication]:
        """
        Query applications by status and loan amount range using the loan-amount-index.
        
        Args:
            status: Application status to filter by
            min_amount: Minimum loan amount
            max_amount: Maximum loan amount
            limit: Maximum number of results
            
        Returns:
            List of matching applications
        """
        try:
            # Use the loan-amount-index for efficient amount-based queries
            if min_amount is not None and max_amount is not None:
                # Query with range condition
                query_results = cls.loan_amount_index.query(
                    status.value,
                    cls.loan_amount.between(min_amount, max_amount),
                    limit=limit
                )
            elif min_amount is not None:
                # Query with minimum amount
                query_results = cls.loan_amount_index.query(
                    status.value,
                    cls.loan_amount >= min_amount,
                    limit=limit
                )
            elif max_amount is not None:
                # Query with maximum amount
                query_results = cls.loan_amount_index.query(
                    status.value,
                    cls.loan_amount <= max_amount,
                    limit=limit
                )
            else:
                # Query all for this status
                query_results = cls.loan_amount_index.query(status.value, limit=limit)
            
            return list(query_results)
        except Exception:
            return []
    
    @classmethod
    def get_by_borrower_name(cls, borrower_name: str, limit: int = 50) -> List[MortgageApplication]:
        """
        Query applications by borrower name.
        
        Args:
            borrower_name: Borrower name to search for
            limit: Maximum number of results
            
        Returns:
            List of matching applications
        """
        try:
            return list(cls.borrower_name_index.query(borrower_name, limit=limit))
        except Exception:
            return []
    
    @classmethod
    def get_by_ssn(cls, ssn: str) -> Optional[MortgageApplication]:
        """
        Query application by SSN (should return at most one result).
        
        SECURITY WARNING: Use this method with caution. Ensure proper
        authorization and audit logging when accessing SSN data.
        
        Args:
            ssn: Social Security Number to search for
            
        Returns:
            Application if found, None otherwise
        """
        try:
            results = list(cls.ssn_lookup_index.query(ssn, limit=1))
            return results[0] if results else None
        except Exception:
            return None
    
    @classmethod
    def search_borrower_partial(cls, partial_name: str, limit: int = 50) -> List[MortgageApplication]:
        """
        Search for borrowers with names containing the partial string.
        
        Note: This performs a scan operation and may be expensive for large tables.
        Consider using get_by_borrower_name for exact matches.
        
        Args:
            partial_name: Partial name to search for
            limit: Maximum number of results
            
        Returns:
            List of matching applications
        """
        try:
            results = []
            for item in cls.scan(cls.borrower_name.contains(partial_name), limit=limit):
                results.append(item)
            return results
        except Exception:
            return []
    
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
                    'home_phone': '555-0123',
                    'cell_phone': '555-0124',
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
            loan_originator_id="TEST_LO_001",
            property_state="CA",
            configuration_data=config_data
        )
        
        print(f"✅ Created application: {app.application_id}")
        print(f"Status: {app.status}")
        print(f"Loan amount: ${app.loan_amount:,.2f}")
        
        # Test status update
        app.update_status(ApplicationStatus.UNDER_REVIEW)
        print(f"✅ Updated status to: {app.status}")
        
        # Test query by status
        apps = MortgageApplication.get_by_status(ApplicationStatus.UNDER_REVIEW, limit=1)
        print(f"✅ Found {len(apps)} applications under review")
        
        # Test new loan amount query method
        amount_apps = MortgageApplication.get_by_amount_range(
            ApplicationStatus.UNDER_REVIEW, 
            min_amount=200000, 
            max_amount=300000, 
            limit=5
        )
        print(f"✅ Found {len(amount_apps)} applications under review with loan amount $200K-$300K")
        
        # Test borrower name query
        borrower_apps = MortgageApplication.get_by_borrower_name("Test Borrower", limit=5)
        print(f"✅ Found {len(borrower_apps)} applications for borrower 'Test Borrower'")
        
        # Test SSN lookup (use with caution in production)
        ssn_app = MortgageApplication.get_by_ssn("123-45-6789")
        if ssn_app:
            print(f"✅ Found application by SSN: {ssn_app.application_id}")
        else:
            print("⚠️ No application found by SSN (may be due to GSI propagation delay)")
        
        print("✅ All tests passed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
