from typing import Dict, Any, List, Optional
from backend.app.core.config import settings
from backend.app.core.logging import logger

class FinancialValidationService:
    def __init__(self, tolerance: float = None):
        self.tolerance = tolerance if tolerance is not None else settings.NUMERICAL_TOLERANCE

    def validate(self, document_type: str, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main entry point for financial validations based on document type.
        Returns the structured validation block: {checks: [...], overall_status: "PASS"|"FAIL", issues: [...]}
        """
        checks: List[Dict[str, Any]] = []
        issues: List[str] = []

        doc_type_norm = document_type.lower().strip().replace("-", "_").replace(" ", "_")

        if doc_type_norm == "invoice":
            checks, issues = self._validate_invoice(extracted_data)
        elif doc_type_norm == "balance_sheet":
            checks, issues = self._validate_balance_sheet(extracted_data)
        elif doc_type_norm in ["profit_and_loss", "pnl", "income_statement"]:
            checks, issues = self._validate_profit_and_loss(extracted_data)
        elif doc_type_norm in ["cash_flow_statement", "cash_flow"]:
            checks, issues = self._validate_cash_flow(extracted_data)
        else:
            issues.append(f"Unrecognized document type for validation: {document_type}")

        # Overall status is PASS if there are no checks with status FAIL
        has_failure = any(c.get("status") == "FAIL" for c in checks)
        overall_status = "FAIL" if has_failure else "PASS"

        return {
            "checks": checks,
            "overall_status": overall_status,
            "issues": issues
        }

    # =========================================================================
    # 1. INVOICE VALIDATION
    # =========================================================================
    def _validate_invoice(self, data: Dict[str, Any]) -> (List[Dict[str, Any]], List[str]):
        checks = []
        issues = []

        subtotal = self._get_num(data.get("subtotal"))
        tax_amount = self._get_num(data.get("tax_amount")) or 0.0
        discount = self._get_num(data.get("discount")) or 0.0
        total_amount = self._get_num(data.get("total_amount"))
        cash_paid = self._get_num(data.get("cash_paid"))
        change_due = self._get_num(data.get("change_due"))
        is_tax_inclusive = data.get("is_tax_inclusive", False)
        line_items = data.get("line_items") or []

        # Check 1: Line Item Unit Price x Quantity ≈ Line Total
        if line_items and isinstance(line_items, list):
            line_sums = 0.0
            all_items_checked = True
            for idx, item in enumerate(line_items):
                desc = item.get("description", f"Item #{idx+1}")
                qty = self._get_num(item.get("quantity"))
                unit_price = self._get_num(item.get("unit_price"))
                item_total = self._get_num(item.get("amount"))

                if qty is not None and unit_price is not None and item_total is not None:
                    calc_total = round(qty * unit_price, 2)
                    var = round(abs(calc_total - item_total), 2)
                    status = "PASS" if var <= self.tolerance else "FAIL"
                    if status == "FAIL":
                        issues.append(f"Line item '{desc}' total mismatch: calculated {calc_total} != reported {item_total} (variance: {var})")
                    checks.append({
                        "name": f"line_item_math_check_{idx+1}",
                        "formula": "quantity * unit_price",
                        "operands": {"description": desc, "quantity": qty, "unit_price": unit_price},
                        "calculated_value": calc_total,
                        "reported_value": item_total,
                        "variance": var,
                        "status": status,
                        "description": f"Multiplication check for line item: {desc}"
                    })
                    line_sums += item_total
                else:
                    all_items_checked = False

            # Check 2: Sum of line totals ≈ Subtotal (or Total if subtotal missing)
            if all_items_checked and line_sums > 0:
                expected_target = subtotal if subtotal is not None else total_amount
                target_name = "subtotal" if subtotal is not None else "total_amount"
                if expected_target is not None:
                    calc_sub = round(line_sums, 2)
                    var = round(abs(calc_sub - expected_target), 2)
                    status = "PASS" if var <= self.tolerance else "FAIL"
                    if status == "FAIL":
                        issues.append(f"Sum of line items ({calc_sub}) does not reconcile to reported {target_name} ({expected_target}). Variance: {var}")
                    checks.append({
                        "name": "line_items_sum_reconciliation",
                        "formula": "sum(line_item.amount)",
                        "operands": {"line_items_count": len(line_items), "line_items_sum": calc_sub},
                        "calculated_value": calc_sub,
                        "reported_value": expected_target,
                        "variance": var,
                        "status": status,
                        "description": f"Reconciliation of sum of line items to {target_name}"
                    })
        else:
            checks.append({
                "name": "line_items_sum_reconciliation",
                "formula": "sum(line_item.amount)",
                "operands": {},
                "calculated_value": None,
                "reported_value": None,
                "variance": None,
                "status": "NOT_APPLICABLE",
                "description": "No line items available in document to validate sum."
            })

        shipping = self._get_num(data.get("shipping_amount")) or 0.0

        # Check 3: Invoice Total Reconciliation (Subtotal + Tax + Shipping - Discount ≈ Total)
        if subtotal is not None and total_amount is not None:
            if is_tax_inclusive:
                calc_total = round(subtotal + shipping - discount, 2)
                formula_str = "subtotal + shipping - discount (tax inclusive)" if shipping > 0 else "subtotal - discount (tax inclusive)"
            else:
                calc_total = round(subtotal + tax_amount + shipping - discount, 2)
                formula_str = "subtotal + tax_amount + shipping - discount" if shipping > 0 else "subtotal + tax_amount - discount"

            var = round(abs(calc_total - total_amount), 2)
            # Also handle alternative where reported subtotal was tax-exclusive or tax already included
            if var > self.tolerance and not is_tax_inclusive:
                alt_calc = round(subtotal + shipping - discount, 2)
                if abs(alt_calc - total_amount) <= self.tolerance:
                    calc_total = alt_calc
                    formula_str = "subtotal + shipping - discount (detected tax-inclusive)" if shipping > 0 else "subtotal - discount (detected tax-inclusive)"
                    var = 0.0

            status = "PASS" if var <= self.tolerance else "FAIL"
            if status == "FAIL":
                issues.append(f"Invoice total reconciliation failed: calculated {calc_total} != reported total {total_amount} (variance: {var})")
            checks.append({
                "name": "invoice_total_check",
                "formula": formula_str,
                "operands": {"subtotal": subtotal, "tax_amount": tax_amount, "shipping": shipping, "discount": discount},
                "calculated_value": calc_total,
                "reported_value": total_amount,
                "variance": var,
                "status": status,
                "description": "Reconciliation of subtotal, tax, shipping and discount against total amount"
            })
        else:
            checks.append({
                "name": "invoice_total_check",
                "formula": "subtotal + tax_amount - discount",
                "operands": {"subtotal": subtotal, "total_amount": total_amount},
                "calculated_value": None,
                "reported_value": total_amount,
                "variance": None,
                "status": "NOT_APPLICABLE",
                "description": "Subtotal or total_amount is missing from document."
            })

        # Check 4: Cash Paid - Total Amount ≈ Change Due (if present)
        if cash_paid is not None and total_amount is not None and change_due is not None:
            calc_change = round(cash_paid - total_amount, 2)
            var = round(abs(calc_change - change_due), 2)
            status = "PASS" if var <= self.tolerance else "FAIL"
            if status == "FAIL":
                issues.append(f"Cash change check failed: {cash_paid} - {total_amount} = {calc_change} != reported {change_due}")
            checks.append({
                "name": "cash_change_check",
                "formula": "cash_paid - total_amount",
                "operands": {"cash_paid": cash_paid, "total_amount": total_amount},
                "calculated_value": calc_change,
                "reported_value": change_due,
                "variance": var,
                "status": status,
                "description": "Verification of cash tender and change returned"
            })
        elif cash_paid is not None or change_due is not None:
            checks.append({
                "name": "cash_change_check",
                "formula": "cash_paid - total_amount",
                "operands": {"cash_paid": cash_paid, "change_due": change_due},
                "calculated_value": None,
                "reported_value": change_due,
                "variance": None,
                "status": "NOT_APPLICABLE",
                "description": "Incomplete cash payment fields in document."
            })

        return checks, issues

    # =========================================================================
    # 2. BALANCE SHEET VALIDATION
    # =========================================================================
    def _validate_balance_sheet(self, data: Dict[str, Any]) -> (List[Dict[str, Any]], List[str]):
        checks = []
        issues = []

        periods = data.get("periods") or ["Current Period"]
        if not isinstance(periods, list) or len(periods) == 0:
            periods = ["Current Period"]

        total_assets_map = data.get("total_assets") or {}
        total_liab_map = data.get("total_liabilities") or {}
        total_equity_map = data.get("total_equity") or {}
        total_cap_liab_map = data.get("total_capital_and_liabilities") or {}
        asset_items = data.get("asset_line_items") or []
        liab_equity_items = data.get("liability_and_equity_line_items") or []

        for period in periods:
            tot_assets = self._get_num(total_assets_map.get(period))
            tot_liab = self._get_num(total_liab_map.get(period))
            tot_equity = self._get_num(total_equity_map.get(period))
            tot_cap_liab = self._get_num(total_cap_liab_map.get(period))

            # 1. Total Assets ≈ Total Capital & Liabilities (or Total Liabilities + Total Equity)
            calc_cap_liab = None
            if tot_cap_liab is not None:
                calc_cap_liab = tot_cap_liab
                formula_str = "reported_capital_and_liabilities"
                operands_dict = {"total_capital_and_liabilities": tot_cap_liab}
            elif tot_liab is not None and tot_equity is not None:
                calc_cap_liab = round(tot_liab + tot_equity, 2)
                formula_str = "total_liabilities + total_equity"
                operands_dict = {"total_liabilities": tot_liab, "total_equity": tot_equity}
            else:
                formula_str = "total_liabilities + total_equity"
                operands_dict = {"total_liabilities": tot_liab, "total_equity": tot_equity}

            if tot_assets is not None and calc_cap_liab is not None:
                var = round(abs(tot_assets - calc_cap_liab), 2)
                status = "PASS" if var <= self.tolerance else "FAIL"
                if status == "FAIL":
                    issues.append(f"Balance Sheet [{period}] inequality: Total Assets ({tot_assets}) != Capital & Liabilities ({calc_cap_liab}). Variance: {var}")
                checks.append({
                    "name": f"balance_sheet_equality_check_{period}",
                    "formula": formula_str,
                    "operands": operands_dict,
                    "calculated_value": calc_cap_liab,
                    "reported_value": tot_assets,
                    "variance": var,
                    "status": status,
                    "description": f"Fundamental accounting balance equality for period {period}"
                })
            else:
                checks.append({
                    "name": f"balance_sheet_equality_check_{period}",
                    "formula": "total_capital_and_liabilities ≈ total_assets",
                    "operands": operands_dict,
                    "calculated_value": calc_cap_liab,
                    "reported_value": tot_assets,
                    "variance": None,
                    "status": "NOT_APPLICABLE",
                    "description": f"Missing assets or liabilities/equity data for period {period}"
                })

            # 2. Asset components sum check
            if asset_items and tot_assets is not None:
                comp_sum = 0.0
                has_comp = False
                for item in asset_items:
                    vals = item.get("values") or {}
                    v = self._get_num(vals.get(period))
                    if v is not None:
                        comp_sum += v
                        has_comp = True

                if has_comp:
                    calc_sum = round(comp_sum, 2)
                    var = round(abs(calc_sum - tot_assets), 2)
                    status = "PASS" if var <= self.tolerance else "FAIL"
                    checks.append({
                        "name": f"asset_components_sum_check_{period}",
                        "formula": "sum(asset_line_items)",
                        "operands": {"period": period, "item_count": len(asset_items)},
                        "calculated_value": calc_sum,
                        "reported_value": tot_assets,
                        "variance": var,
                        "status": status,
                        "description": f"Sum of individual asset line items vs Total Assets for {period}"
                    })

            # 3. Liability & Equity components sum check
            if liab_equity_items and (tot_cap_liab is not None or (tot_liab is not None and tot_equity is not None)):
                comp_sum = 0.0
                has_comp = False
                target_val = tot_cap_liab if tot_cap_liab is not None else round(tot_liab + tot_equity, 2)
                for item in liab_equity_items:
                    vals = item.get("values") or {}
                    v = self._get_num(vals.get(period))
                    if v is not None:
                        comp_sum += v
                        has_comp = True

                if has_comp:
                    calc_sum = round(comp_sum, 2)
                    var = round(abs(calc_sum - target_val), 2)
                    status = "PASS" if var <= self.tolerance else "FAIL"
                    checks.append({
                        "name": f"liability_equity_components_sum_check_{period}",
                        "formula": "sum(liability_and_equity_line_items)",
                        "operands": {"period": period, "item_count": len(liab_equity_items)},
                        "calculated_value": calc_sum,
                        "reported_value": target_val,
                        "variance": var,
                        "status": status,
                        "description": f"Sum of individual liability & equity items vs Total Capital & Liabilities for {period}"
                    })

        return checks, issues

    # =========================================================================
    # 3. PROFIT & LOSS VALIDATION
    # =========================================================================
    def _validate_profit_and_loss(self, data: Dict[str, Any]) -> (List[Dict[str, Any]], List[str]):
        checks = []
        issues = []

        periods = data.get("periods") or ["Current Period"]
        if not isinstance(periods, list) or len(periods) == 0:
            periods = ["Current Period"]

        for period in periods:
            # 1. Total Income Check: Interest Earned + Other Income ≈ Total Income (or Revenue + Other Income)
            rev = self._get_num(self._extract_period_val(data.get("revenue"), period))
            int_earned = self._get_num(self._extract_period_val(data.get("interest_earned"), period))
            other_inc = self._get_num(self._extract_period_val(data.get("other_income"), period)) or 0.0
            tot_inc = self._get_num(self._extract_period_val(data.get("total_income"), period))

            base_inc = int_earned if int_earned is not None else rev
            base_name = "interest_earned" if int_earned is not None else "revenue"

            if base_inc is not None and tot_inc is not None:
                calc_tot_inc = round(base_inc + other_inc, 2)
                var = round(abs(calc_tot_inc - tot_inc), 2)
                status = "PASS" if var <= self.tolerance else "FAIL"
                if status == "FAIL":
                    issues.append(f"P&L [{period}] Total Income check mismatch: calculated {calc_tot_inc} != reported {tot_inc}")
                checks.append({
                    "name": f"total_income_check_{period}",
                    "formula": f"{base_name} + other_income",
                    "operands": {base_name: base_inc, "other_income": other_inc},
                    "calculated_value": calc_tot_inc,
                    "reported_value": tot_inc,
                    "variance": var,
                    "status": status,
                    "description": f"Reconciliation of total income for period {period}"
                })
            else:
                checks.append({
                    "name": f"total_income_check_{period}",
                    "formula": "interest_earned + other_income",
                    "operands": {"interest_earned": int_earned, "revenue": rev, "other_income": other_inc},
                    "calculated_value": None,
                    "reported_value": tot_inc,
                    "variance": None,
                    "status": "NOT_APPLICABLE",
                    "description": f"Missing components for total income validation in period {period}"
                })

            # 2. Total Expenditure Check: Interest Expended + Operating Expenses + Provisions ≈ Total Expenditure
            int_exp = self._get_num(self._extract_period_val(data.get("interest_expended"), period))
            cogs = self._get_num(self._extract_period_val(data.get("cost_of_sales"), period))
            opex = self._get_num(self._extract_period_val(data.get("operating_expenses"), period)) or 0.0
            provisions = self._get_num(self._extract_period_val(data.get("provisions_and_contingencies"), period)) or 0.0
            tot_exp = self._get_num(self._extract_period_val(data.get("total_expenditure"), period))

            base_exp = int_exp if int_exp is not None else cogs
            base_exp_name = "interest_expended" if int_exp is not None else "cost_of_sales"

            if base_exp is not None and tot_exp is not None:
                calc_tot_exp = round(base_exp + opex + provisions, 2)
                var = round(abs(calc_tot_exp - tot_exp), 2)
                status = "PASS" if var <= self.tolerance else "FAIL"
                if status == "FAIL":
                    issues.append(f"P&L [{period}] Total Expenditure check mismatch: calculated {calc_tot_exp} != reported {tot_exp}")
                checks.append({
                    "name": f"total_expenditure_check_{period}",
                    "formula": f"{base_exp_name} + operating_expenses + provisions",
                    "operands": {base_exp_name: base_exp, "operating_expenses": opex, "provisions": provisions},
                    "calculated_value": calc_tot_exp,
                    "reported_value": tot_exp,
                    "variance": var,
                    "status": status,
                    "description": f"Reconciliation of total expenditure for period {period}"
                })
            else:
                checks.append({
                    "name": f"total_expenditure_check_{period}",
                    "formula": "interest_expended + operating_expenses + provisions",
                    "operands": {base_exp_name: base_exp, "operating_expenses": opex, "provisions": provisions},
                    "calculated_value": None,
                    "reported_value": tot_exp,
                    "variance": None,
                    "status": "NOT_APPLICABLE",
                    "description": f"Missing components for total expenditure in period {period}"
                })

            # 3. Net Profit before Tax / Minority Interest: Total Income - Total Expenditure ≈ PBT
            pbt = self._get_num(self._extract_period_val(data.get("profit_before_tax"), period)) or \
                  self._get_num(self._extract_period_val(data.get("operating_profit"), period))

            if tot_inc is not None and tot_exp is not None and pbt is not None:
                calc_pbt = round(tot_inc - tot_exp, 2)
                var = round(abs(calc_pbt - pbt), 2)
                status = "PASS" if var <= self.tolerance else "FAIL"
                if status == "FAIL":
                    issues.append(f"P&L [{period}] Net Profit Before Tax mismatch: calculated {calc_pbt} != reported {pbt}")
                checks.append({
                    "name": f"profit_before_tax_check_{period}",
                    "formula": "total_income - total_expenditure",
                    "operands": {"total_income": tot_inc, "total_expenditure": tot_exp},
                    "calculated_value": calc_pbt,
                    "reported_value": pbt,
                    "variance": var,
                    "status": status,
                    "description": f"Operating / Pre-tax profit reconciliation for period {period}"
                })
            else:
                checks.append({
                    "name": f"profit_before_tax_check_{period}",
                    "formula": "total_income - total_expenditure",
                    "operands": {"total_income": tot_inc, "total_expenditure": tot_exp},
                    "calculated_value": None,
                    "reported_value": pbt,
                    "variance": None,
                    "status": "NOT_APPLICABLE",
                    "description": f"Income, expenditure, or PBT missing for period {period}"
                })

            # 4. Profit attributable: PBT - Tax / Minority Interest ≈ Net Profit
            tax = self._get_num(self._extract_period_val(data.get("tax_expense"), period)) or 0.0
            minority = self._get_num(self._extract_period_val(data.get("minority_interest"), period)) or 0.0
            pat = self._get_num(self._extract_period_val(data.get("net_profit_attributable"), period))

            if pbt is not None and pat is not None:
                calc_pat = round(pbt - tax - minority, 2)
                var = round(abs(calc_pat - pat), 2)
                status = "PASS" if var <= self.tolerance else "FAIL"
                if status == "FAIL":
                    issues.append(f"P&L [{period}] Net Profit Attributable mismatch: calculated {calc_pat} != reported {pat}")
                checks.append({
                    "name": f"net_profit_attributable_check_{period}",
                    "formula": "profit_before_tax - tax_expense - minority_interest",
                    "operands": {"profit_before_tax": pbt, "tax_expense": tax, "minority_interest": minority},
                    "calculated_value": calc_pat,
                    "reported_value": pat,
                    "variance": var,
                    "status": status,
                    "description": f"Consolidated net profit attributable reconciliation for period {period}"
                })

            # 5. Appropriations: Current Profit + Brought Forward Profit ≈ Total Available for Appropriation
            cur_prof = self._get_num(self._extract_period_val(data.get("current_profit"), period)) or pat
            bf_prof = self._get_num(self._extract_period_val(data.get("brought_forward_profit"), period))
            tot_approp = self._get_num(self._extract_period_val(data.get("total_appropriations"), period))

            if cur_prof is not None and bf_prof is not None and tot_approp is not None:
                calc_approp = round(cur_prof + bf_prof, 2)
                var = round(abs(calc_approp - tot_approp), 2)
                status = "PASS" if var <= self.tolerance else "FAIL"
                checks.append({
                    "name": f"appropriations_check_{period}",
                    "formula": "current_profit + brought_forward_profit",
                    "operands": {"current_profit": cur_prof, "brought_forward_profit": bf_prof},
                    "calculated_value": calc_approp,
                    "reported_value": tot_approp,
                    "variance": var,
                    "status": status,
                    "description": f"Appropriations reconciliation for period {period}"
                })

        return checks, issues

    # =========================================================================
    # 4. CASH FLOW STATEMENT VALIDATION
    # =========================================================================
    def _validate_cash_flow(self, data: Dict[str, Any]) -> (List[Dict[str, Any]], List[str]):
        checks = []
        issues = []

        periods = data.get("periods") or ["Current Period"]
        if not isinstance(periods, list) or len(periods) == 0:
            periods = ["Current Period"]

        for period in periods:
            op_cf = self._get_num(self._extract_period_val(data.get("operating_cash_flow"), period))
            inv_cf = self._get_num(self._extract_period_val(data.get("investing_cash_flow"), period))
            fin_cf = self._get_num(self._extract_period_val(data.get("financing_cash_flow"), period))
            fx_adj = self._get_num(self._extract_period_val(data.get("fx_translation_adjustment"), period)) or 0.0
            net_change = self._get_num(self._extract_period_val(data.get("net_change_in_cash"), period))
            open_cash = self._get_num(self._extract_period_val(data.get("opening_cash"), period))
            close_cash = self._get_num(self._extract_period_val(data.get("closing_cash"), period))
            amal_adj = self._get_num(self._extract_period_val(data.get("cash_acquired_on_amalgamation"), period)) or 0.0

            # Check 1: Operating + Investing + Financing + FX ≈ Net Increase in Cash
            if op_cf is not None and inv_cf is not None and fin_cf is not None and net_change is not None:
                calc_net_change = round(op_cf + inv_cf + fin_cf + fx_adj, 2)
                var = round(abs(calc_net_change - net_change), 2)
                status = "PASS" if var <= self.tolerance else "FAIL"
                if status == "FAIL":
                    issues.append(f"Cash Flow [{period}] Net increase mismatch: {op_cf} + {inv_cf} + {fin_cf} + {fx_adj} = {calc_net_change} != reported {net_change}")
                checks.append({
                    "name": f"net_change_in_cash_check_{period}",
                    "formula": "operating_cash_flow + investing_cash_flow + financing_cash_flow + fx_translation_adjustment",
                    "operands": {
                        "operating_cash_flow": op_cf,
                        "investing_cash_flow": inv_cf,
                        "financing_cash_flow": fin_cf,
                        "fx_translation_adjustment": fx_adj
                    },
                    "calculated_value": calc_net_change,
                    "reported_value": net_change,
                    "variance": var,
                    "status": status,
                    "description": f"Net cash increase reconciliation for period {period}"
                })
            else:
                checks.append({
                    "name": f"net_change_in_cash_check_{period}",
                    "formula": "operating_cash_flow + investing_cash_flow + financing_cash_flow + fx_translation_adjustment",
                    "operands": {"operating_cash_flow": op_cf, "investing_cash_flow": inv_cf, "financing_cash_flow": fin_cf},
                    "calculated_value": None,
                    "reported_value": net_change,
                    "variance": None,
                    "status": "NOT_APPLICABLE",
                    "description": f"Missing cash flow activity totals for period {period}"
                })

            # Check 2: Opening Cash + Net Increase + Adjustments ≈ Closing Cash
            target_change = net_change if net_change is not None else (
                round(op_cf + inv_cf + fin_cf + fx_adj, 2) if (op_cf is not None and inv_cf is not None and fin_cf is not None) else None
            )

            if open_cash is not None and target_change is not None and close_cash is not None:
                calc_close = round(open_cash + target_change + amal_adj, 2)
                var = round(abs(calc_close - close_cash), 2)
                status = "PASS" if var <= self.tolerance else "FAIL"
                if status == "FAIL":
                    issues.append(f"Cash Flow [{period}] Closing cash mismatch: {open_cash} + {target_change} + {amal_adj} = {calc_close} != reported {close_cash}")
                checks.append({
                    "name": f"closing_cash_reconciliation_{period}",
                    "formula": "opening_cash + net_change_in_cash + adjustments",
                    "operands": {
                        "opening_cash": open_cash,
                        "net_change_in_cash": target_change,
                        "amalgamation_adjustments": amal_adj
                    },
                    "calculated_value": calc_close,
                    "reported_value": close_cash,
                    "variance": var,
                    "status": status,
                    "description": f"Reconciliation of opening to closing cash for period {period}"
                })
            else:
                checks.append({
                    "name": f"closing_cash_reconciliation_{period}",
                    "formula": "opening_cash + net_change_in_cash + adjustments",
                    "operands": {"opening_cash": open_cash, "closing_cash": close_cash},
                    "calculated_value": None,
                    "reported_value": close_cash,
                    "variance": None,
                    "status": "NOT_APPLICABLE",
                    "description": f"Opening cash or closing cash missing for period {period}"
                })

        return checks, issues

    # =========================================================================
    # HELPER METHODS
    # =========================================================================
    @staticmethod
    def _get_num(val: Any) -> Optional[float]:
        """Safely extracts a float, handling dicts with 'value', negative parentheses like '(1,250)'."""
        if val is None:
            return None
        if isinstance(val, (int, float)):
            return float(val)
        if isinstance(val, dict):
            return FinancialValidationService._get_num(val.get("value"))
        if isinstance(val, str):
            clean = val.strip()
            if not clean or clean.lower() in ("null", "none", "n/a", "-"):
                return None
            # Handle bracketed negative numbers: (500.00) -> -500.00
            is_negative = False
            if clean.startswith("(") and clean.endswith(")"):
                is_negative = True
                clean = clean[1:-1].strip()
            elif clean.startswith("-"):
                is_negative = True
                clean = clean[1:].strip()
            
            # Remove currency symbols and formatting commas
            for char in ["$", "€", "£", "₹", "USD", "INR", "EUR", "GBP", ",", " "]:
                clean = clean.replace(char, "")

            try:
                num = float(clean)
                return -num if is_negative else num
            except ValueError:
                return None
        return None

    @staticmethod
    def _extract_period_val(field_obj: Any, period: str) -> Any:
        """Extracts value for a given period if mapped by period dictionary."""
        if isinstance(field_obj, dict):
            if period in field_obj:
                return field_obj[period]
            # If standard single value dict
            if "value" in field_obj and not any(isinstance(v, dict) for v in field_obj.values()):
                return field_obj
        return field_obj
