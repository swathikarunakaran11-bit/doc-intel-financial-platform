from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field

class Evidence(BaseModel):
    source_text: str
    page_number: int

class ExtractedField(BaseModel):
    value: Optional[Union[str, float, int, bool]] = None
    confidence: Optional[float] = 0.95
    evidence: Optional[Evidence] = None

class InvoiceLineItem(BaseModel):
    description: str
    quantity: float
    unit_price: float
    amount: float
    confidence: Optional[float] = 0.95
    page_number: Optional[int] = 1

class InvoiceExtractedData(BaseModel):
    invoice_number: ExtractedField
    invoice_date: ExtractedField
    vendor_name: ExtractedField
    customer_name: ExtractedField
    currency: ExtractedField
    subtotal: ExtractedField
    tax_amount: ExtractedField
    discount: ExtractedField
    shipping_amount: Optional[ExtractedField] = None
    total_amount: ExtractedField
    cash_paid: Optional[ExtractedField] = None
    change_due: Optional[ExtractedField] = None
    is_tax_inclusive: Optional[bool] = False
    line_items: List[InvoiceLineItem] = Field(default_factory=list)

class StatementPeriodValues(BaseModel):
    period: str
    reported_value: Optional[float] = None
    evidence: Optional[Evidence] = None

class BalanceSheetItem(BaseModel):
    line_item: str
    values: Dict[str, Optional[float]] = Field(default_factory=dict)
    category: str  # asset | liability | equity

class BalanceSheetExtractedData(BaseModel):
    statement_title: ExtractedField
    entity_name: ExtractedField
    reporting_currency: ExtractedField
    periods: List[str] = Field(default_factory=list)
    # Core aggregate fields per period
    total_assets: Dict[str, ExtractedField] = Field(default_factory=dict)
    total_liabilities: Dict[str, ExtractedField] = Field(default_factory=dict)
    total_equity: Dict[str, ExtractedField] = Field(default_factory=dict)
    total_capital_and_liabilities: Dict[str, ExtractedField] = Field(default_factory=dict)
    # Detailed line items
    asset_line_items: List[BalanceSheetItem] = Field(default_factory=list)
    liability_and_equity_line_items: List[BalanceSheetItem] = Field(default_factory=list)

class ProfitAndLossItem(BaseModel):
    line_item: str
    values: Dict[str, Optional[float]] = Field(default_factory=dict)
    category: str  # income | expense | appropriation

class ProfitAndLossExtractedData(BaseModel):
    statement_title: ExtractedField
    entity_name: ExtractedField
    reporting_currency: ExtractedField
    periods: List[str] = Field(default_factory=list)
    # P&L line items & checks
    revenue: Dict[str, ExtractedField] = Field(default_factory=dict)
    interest_earned: Dict[str, ExtractedField] = Field(default_factory=dict)
    other_income: Dict[str, ExtractedField] = Field(default_factory=dict)
    total_income: Dict[str, ExtractedField] = Field(default_factory=dict)
    cost_of_sales: Dict[str, ExtractedField] = Field(default_factory=dict)
    interest_expended: Dict[str, ExtractedField] = Field(default_factory=dict)
    operating_expenses: Dict[str, ExtractedField] = Field(default_factory=dict)
    provisions_and_contingencies: Dict[str, ExtractedField] = Field(default_factory=dict)
    total_expenditure: Dict[str, ExtractedField] = Field(default_factory=dict)
    operating_profit: Dict[str, ExtractedField] = Field(default_factory=dict)
    profit_before_tax: Dict[str, ExtractedField] = Field(default_factory=dict)
    tax_expense: Dict[str, ExtractedField] = Field(default_factory=dict)
    minority_interest: Dict[str, ExtractedField] = Field(default_factory=dict)
    net_profit_attributable: Dict[str, ExtractedField] = Field(default_factory=dict)
    current_profit: Dict[str, ExtractedField] = Field(default_factory=dict)
    brought_forward_profit: Dict[str, ExtractedField] = Field(default_factory=dict)
    total_appropriations: Dict[str, ExtractedField] = Field(default_factory=dict)
    line_items: List[ProfitAndLossItem] = Field(default_factory=list)

class CashFlowExtractedData(BaseModel):
    statement_title: ExtractedField
    entity_name: ExtractedField
    reporting_currency: ExtractedField
    periods: List[str] = Field(default_factory=list)
    operating_cash_flow: Dict[str, ExtractedField] = Field(default_factory=dict)
    investing_cash_flow: Dict[str, ExtractedField] = Field(default_factory=dict)
    financing_cash_flow: Dict[str, ExtractedField] = Field(default_factory=dict)
    fx_translation_adjustment: Dict[str, ExtractedField] = Field(default_factory=dict)
    net_change_in_cash: Dict[str, ExtractedField] = Field(default_factory=dict)
    opening_cash: Dict[str, ExtractedField] = Field(default_factory=dict)
    closing_cash: Dict[str, ExtractedField] = Field(default_factory=dict)
    cash_acquired_on_amalgamation: Dict[str, ExtractedField] = Field(default_factory=dict)
