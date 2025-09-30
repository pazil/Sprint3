"""
Price Analyzer
Calculates price deviations from HP suggested retail prices
Accounts for bundles and XL vs regular models
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


# HP Suggested Retail Prices with Expected Page Yield (from provided table)
PRICE_TABLE = [
    {"code": "F6V28AB", "series": "HP 664", "product": "HP 664 Tri-color", "pages": 100, "price_brl": 74.90},
    {"code": "F6V29AB", "series": "HP 664", "product": "HP 664 Preto", "pages": 120, "price_brl": 69.90},
    {"code": "F6V30AB", "series": "HP 664", "product": "HP 664XL Tri-color", "pages": 330, "price_brl": 172.90},
    {"code": "F6V31AB", "series": "HP 664", "product": "HP 664XL Preto", "pages": 480, "price_brl": 172.90}
]

# Page yield expectations for reference in review analysis
PAGE_YIELD_REFERENCE = {
    ("664", False, "Colorido"): 100,  # Regular color
    ("664", False, "Preto"): 120,      # Regular black
    ("664", True, "Colorido"): 330,    # XL color
    ("664", True, "Preto"): 480        # XL black
}


@dataclass
class PriceAnalysis:
    """Price analysis results"""
    listed_price: float
    bundle_quantity: int
    price_per_unit: float
    
    # Matching to price table
    matched_sku: Optional[str]
    suggested_retail: Optional[float]
    expected_bundle_price: Optional[float]  # suggested × quantity
    
    # Deviation analysis
    deviation_amount: Optional[float]  # Actual - Expected
    deviation_pct: Optional[float]  # (Actual - Expected) / Expected × 100
    
    # Risk categorization
    price_risk_level: str  # "CRITICAL", "HIGH", "MEDIUM", "LOW", "NORMAL", "PREMIUM"
    is_suspicious_price: bool
    
    # Notes
    notes: str


class PriceAnalyzer:
    """Analyze product pricing against HP suggested retail"""
    
    def __init__(self):
        # Create lookup by (model, is_xl, color)
        self.price_lookup = self._build_price_lookup()
    
    def _build_price_lookup(self) -> Dict[Tuple[str, bool, str], Dict]:
        """
        Build price lookup table
        
        Key: (model, is_xl, color_type)
        - model: "664", "667", "662"
        - is_xl: True/False
        - color_type: "Preto", "Colorido"
        """
        lookup = {}
        
        for item in PRICE_TABLE:
            # Parse model
            model = "664"  # All in table are 664
            is_xl = "XL" in item['product']
            
            # Parse color
            if "Preto" in item['product']:
                color = "Preto"
            else:
                color = "Colorido"
            
            key = (model, is_xl, color)
            lookup[key] = item
        
        return lookup
    
    def analyze(
        self, 
        product: Dict,
        llm_product_structure = None
    ) -> PriceAnalysis:
        """
        Analyze product pricing
        
        Args:
            product: Product object with price info
            llm_product_structure: ProductStructure from LLM analysis
            
        Returns:
            PriceAnalysis with deviation calculations
        """
        # Get listed price
        listed_price = float(product.get('preco', 0))
        
        # Get bundle info from LLM analysis
        if llm_product_structure:
            bundle_qty = llm_product_structure.bundle_quantity
            model = llm_product_structure.model_primary
            is_xl = llm_product_structure.is_xl
            items = llm_product_structure.item_breakdown
        else:
            # Fallback (shouldn't happen in our pipeline)
            bundle_qty = 1
            model = "664"
            is_xl = False
            items = []
        
        # Calculate per-unit price
        price_per_unit = listed_price / bundle_qty if bundle_qty > 0 else listed_price
        
        # Calculate expected price for this bundle
        expected_total, matched_items = self._calculate_expected_price(items)
        
        # Calculate deviation
        if expected_total is not None:
            deviation_amt = listed_price - expected_total
            deviation_pct = (deviation_amt / expected_total) * 100
            
            # Get per-unit comparisons
            if bundle_qty > 0 and len(matched_items) > 0:
                avg_suggested = expected_total / bundle_qty
                matched_sku = matched_items[0].get('code', None)
            else:
                avg_suggested = expected_total
                matched_sku = None
        else:
            # No match in price table
            deviation_amt = None
            deviation_pct = None
            avg_suggested = None
            matched_sku = None
        
        # Categorize risk
        risk_level, is_suspicious = self._categorize_price_risk(deviation_pct)
        
        # Notes
        notes = self._generate_notes(
            bundle_qty, items, matched_items, deviation_pct
        )
        
        return PriceAnalysis(
            listed_price=listed_price,
            bundle_quantity=bundle_qty,
            price_per_unit=price_per_unit,
            matched_sku=matched_sku,
            suggested_retail=avg_suggested,
            expected_bundle_price=expected_total,
            deviation_amount=deviation_amt,
            deviation_pct=deviation_pct,
            price_risk_level=risk_level,
            is_suspicious_price=is_suspicious,
            notes=notes
        )
    
    def _calculate_expected_price(
        self, 
        items: List[Dict]
    ) -> Tuple[Optional[float], List[Dict]]:
        """
        Calculate expected price for bundle based on item breakdown
        
        Args:
            items: List from LLM's item_breakdown
            
        Returns:
            (total_expected_price, matched_items_from_table)
        """
        if not items:
            return None, []
        
        total_price = 0.0
        matched_items = []
        
        for item in items:
            model = item.get('model', '').replace(' ', '')  # "664XL" -> "664XL"
            color = item.get('color', '')
            qty = item.get('quantity', 1)
            
            # Normalize model to extract base and XL
            is_xl = 'XL' in model.upper()
            base_model = model.replace('XL', '').replace('xl', '')
            
            # Normalize color
            color_normalized = self._normalize_color(color)
            
            # Lookup in price table
            key = (base_model, is_xl, color_normalized)
            price_entry = self.price_lookup.get(key)
            
            if price_entry:
                item_price = price_entry['price_brl'] * qty
                total_price += item_price
                matched_items.append(price_entry)
            else:
                # Can't find match for this item
                # Try variations
                for try_color in ["Preto", "Colorido"]:
                    key_try = (base_model, is_xl, try_color)
                    price_entry = self.price_lookup.get(key_try)
                    if price_entry:
                        item_price = price_entry['price_brl'] * qty
                        total_price += item_price
                        matched_items.append(price_entry)
                        break
        
        if not matched_items:
            return None, []
        
        return total_price, matched_items
    
    def _normalize_color(self, color: str) -> str:
        """Normalize color to match price table"""
        color_lower = color.lower()
        
        if 'preto' in color_lower or 'black' in color_lower or 'negro' in color_lower:
            return "Preto"
        elif 'color' in color_lower or 'tricolor' in color_lower or 'tri-color' in color_lower:
            return "Colorido"
        else:
            return "Colorido"  # Default assumption
    
    def _categorize_price_risk(
        self, 
        deviation_pct: Optional[float]
    ) -> Tuple[str, bool]:
        """
        Categorize price risk based on deviation percentage
        
        Returns:
            (risk_level, is_suspicious)
        """
        if deviation_pct is None:
            return "UNKNOWN", False
        
        if deviation_pct < -70:
            return "CRITICAL", True  # 70%+ discount - almost certainly fake
        elif deviation_pct < -50:
            return "HIGH", True  # 50-70% discount - very suspicious
        elif deviation_pct < -30:
            return "MEDIUM", True  # 30-50% discount - suspicious
        elif deviation_pct < -10:
            return "LOW", False  # 10-30% discount - possible sale/promotion
        elif deviation_pct < 20:
            return "NORMAL", False  # Within normal range
        else:
            return "PREMIUM", False  # Above retail (markup or premium seller)
    
    def _generate_notes(
        self,
        bundle_qty: int,
        items: List[Dict],
        matched_items: List[Dict],
        deviation_pct: Optional[float]
    ) -> str:
        """Generate explanatory notes"""
        notes = []
        
        if bundle_qty > 1:
            notes.append(f"Bundle of {bundle_qty} cartridges")
        
        if len(matched_items) == 0:
            notes.append("⚠️ Could not match to price table")
        elif len(matched_items) != len(items):
            notes.append(f"⚠️ Partial match: {len(matched_items)}/{len(items)} items matched")
        
        if deviation_pct is not None:
            if deviation_pct < -30:
                notes.append(f"🚩 {abs(deviation_pct):.1f}% below retail - SUSPICIOUS")
            elif deviation_pct > 50:
                notes.append(f"Premium pricing: {deviation_pct:.1f}% above retail")
        
        return "; ".join(notes) if notes else "Normal pricing"


# Usage example
if __name__ == "__main__":
    from pipeline.llm_product_analyzer import LLMProductAnalyzer, ProductStructure
    
    # Simulate LLM product structure result
    llm_result = ProductStructure(
        is_bundle=True,
        bundle_quantity=2,
        item_breakdown=[
            {"model": "664XL", "color": "Preto", "quantity": 1},
            {"model": "664XL", "color": "Colorido", "quantity": 1}
        ],
        model_primary="664XL",
        is_xl=True,
        colors_in_bundle=["Preto", "Colorido"],
        confidence=1.0,
        notes=""
    )
    
    test_product = {
        "id": "MLB_TEST",
        "preco": "295.00",  # Listed price
        "titulo": "Kit 2 Cartuchos HP 664XL Preto + Color"
    }
    
    analyzer = PriceAnalyzer()
    analysis = analyzer.analyze(test_product, llm_result)
    
    print(f"Listed Price: R$ {analysis.listed_price:.2f}")
    print(f"Bundle Quantity: {analysis.bundle_quantity}")
    print(f"Price per Unit: R$ {analysis.price_per_unit:.2f}")
    print(f"Expected Total: R$ {analysis.expected_bundle_price:.2f}")
    print(f"Deviation: {analysis.deviation_pct:.1f}%")
    print(f"Risk Level: {analysis.price_risk_level}")
    print(f"Suspicious: {analysis.is_suspicious_price}")
    print(f"Notes: {analysis.notes}")

