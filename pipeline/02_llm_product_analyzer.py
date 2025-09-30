"""
LLM Product Analyzer
Uses OpenAI to extract structured information from product titles and descriptions
- Bundle detection and quantity
- Model identification
- Color distribution in bundles
- XL detection
"""

from openai import OpenAI
from dotenv import load_dotenv
import os
from typing import Dict, List, Optional
from dataclasses import dataclass
import json

# Load environment variables (override system env vars)
load_dotenv(override=True)


@dataclass
class ProductStructure:
    """Structured product information extracted by LLM"""
    is_bundle: bool
    bundle_quantity: int
    item_breakdown: List[Dict[str, str]]  # [{"model": "664XL", "color": "Preto", "quantity": 2}, ...]
    model_primary: str  # "664" or "664XL" or "667" etc.
    is_xl: bool
    colors_in_bundle: List[str]  # ["Preto", "Colorido"]
    confidence: float  # 0-1 how confident the LLM is
    notes: str  # Any ambiguities or special cases


class LLMProductAnalyzer:
    """Analyze product titles and descriptions using LLM"""
    
    def __init__(self):
        # Load API key with debugging
        api_key = os.getenv('OPENAI_API_KEY')
        
        print(f"\n🔑 DEBUG - LLM Product Analyzer Init:")
        print(f"   API Key loaded: {'Yes' if api_key else 'No'}")
        if api_key:
            print(f"   API Key prefix: {api_key[:15]}...")
            print(f"   API Key length: {len(api_key)} chars")
        else:
            print(f"   ⚠️  WARNING: No API key found in environment!")
        
        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-5-nano"  # Using VALIDATED working model
        print(f"   Model: {self.model}")
        print(f"   Client initialized: Yes")
        
    def analyze_product_structure(self, product: Dict) -> ProductStructure:
        """
        Analyze product title and description to extract:
        - Bundle status and quantity
        - Model numbers
        - Color distribution
        - XL status
        
        Args:
            product: Product object from main dataset
            
        Returns:
            ProductStructure with extracted information
        """
        titulo = product.get('titulo', '')
        descricao = product.get('descricao', '')[:1000]  # First 1000 chars
        
        # Create prompts
        system_prompt = """You are an expert at analyzing HP printer cartridge product listings.
Your task is to extract structured information about bundles, models, and colors.
Be precise and handle Portuguese text.

CRITICAL: You MUST return ONLY valid JSON. No other text, no markdown, no explanations.
Start your response with { and end with }."""
        
        user_prompt = self._build_product_analysis_prompt(titulo, descricao)
        
        print(f"\n📡 DEBUG - Making API call:")
        print(f"   Model: {self.model}")
        print(f"   Endpoint: chat.completions.create()")
        print(f"   Title length: {len(titulo)} chars")
        print(f"   Description length: {len(descricao)} chars")
        
        try:
            # Call OpenAI with VALIDATED working format
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                reasoning_effort="minimal"
            )
            
            print(f"   ✓ API call successful")
            
        except Exception as e:
            print(f"\n❌ API Call Failed:")
            print(f"   Error type: {type(e).__name__}")
            print(f"   Error message: {str(e)}")
            
            # Check if it's a quota/auth issue
            if "quota" in str(e).lower():
                print(f"\n💡 QUOTA ISSUE DETECTED:")
                print(f"   This means the API key is working but account has no credits")
                print(f"   Check: https://platform.openai.com/account/billing")
            elif "authentication" in str(e).lower() or "unauthorized" in str(e).lower():
                print(f"\n💡 AUTHENTICATION ISSUE:")
                print(f"   API key may be invalid or expired")
            elif "model" in str(e).lower():
                print(f"\n💡 MODEL ISSUE:")
                print(f"   gpt-5 may not be available on your account")
                print(f"   Try switching to gpt-4o-mini")
            
            raise
        
        # Parse response (standard chat API format)
        result = json.loads(response.choices[0].message.content)
        print(f"   ✓ Response parsed successfully")
        
        return ProductStructure(
            is_bundle=result['is_bundle'],
            bundle_quantity=result['bundle_quantity'],
            item_breakdown=result['item_breakdown'],
            model_primary=result['model_primary'],
            is_xl=result['is_xl'],
            colors_in_bundle=result['colors_in_bundle'],
            confidence=result['confidence'],
            notes=result.get('notes', '')
        )
    
    def _build_product_analysis_prompt(self, titulo: str, descricao: str) -> str:
        """Build prompt for product structure extraction"""
        
        return f"""Analyze this HP printer cartridge product listing and extract structured information.

TITLE: {titulo}

DESCRIPTION (first 1000 chars): {descricao}

Extract the following information and return as JSON:

1. **is_bundle**: Is this a kit/bundle or single unit? (boolean)

2. **bundle_quantity**: Total number of cartridges in the package (integer)
   - If single unit: 1
   - If bundle: extract from title or description
   - Examples: "Kit 2 Cartuchos" = 2, "3 Unidades" = 3

3. **item_breakdown**: Array describing each item type in the bundle
   - For single unit: [{{"model": "664", "color": "Preto", "quantity": 1}}]
   - For bundle: [{{"model": "664XL", "color": "Preto", "quantity": 2}}, {{"model": "664XL", "color": "Colorido", "quantity": 1}}]
   - Models: "664", "664XL", "667", "667XL", "662", "662XL"
   - Colors: "Preto" (black), "Colorido" (color/tri-color), "Mixed" if unclear

4. **model_primary**: The main model number ("664", "664XL", "667", etc.)
   - If bundle with mixed models, use the most prominent one

5. **is_xl**: Is this an XL model? (boolean)
   - XL cartridges have more ink (8.5ml vs 2ml)
   - Look for "XL" in title, description, or volume indicators

6. **colors_in_bundle**: List of colors included
   - ["Preto"] for black only
   - ["Colorido"] for color only  
   - ["Preto", "Colorido"] for kit with both
   - ["Tricolor"] for tri-color cartridges

7. **confidence**: How confident are you in this extraction? (0.0 to 1.0)
   - 1.0 = very clear information
   - 0.5 = ambiguous, had to infer
   - Lower if information is contradictory or unclear

8. **notes**: Any ambiguities, special cases, or warnings (string)

EXAMPLES:

Input: "Cartucho HP 664 Preto"
Output:
{{
  "is_bundle": false,
  "bundle_quantity": 1,
  "item_breakdown": [{{"model": "664", "color": "Preto", "quantity": 1}}],
  "model_primary": "664",
  "is_xl": false,
  "colors_in_bundle": ["Preto"],
  "confidence": 1.0,
  "notes": "Clear single unit, regular 664 black cartridge"
}}

Input: "Kit 2 Cartuchos HP 664XL Preto + Color"
Output:
{{
  "is_bundle": true,
  "bundle_quantity": 2,
  "item_breakdown": [
    {{"model": "664XL", "color": "Preto", "quantity": 1}},
    {{"model": "664XL", "color": "Colorido", "quantity": 1}}
  ],
  "model_primary": "664XL",
  "is_xl": true,
  "colors_in_bundle": ["Preto", "Colorido"],
  "confidence": 1.0,
  "notes": "Clear 2-unit bundle, one black and one color XL cartridge"
}}

Input: "3 Cartuchos HP 664XL Preto 2 Color"
Output:
{{
  "is_bundle": true,
  "bundle_quantity": 3,
  "item_breakdown": [
    {{"model": "664XL", "color": "Preto", "quantity": 2}},
    {{"model": "664XL", "color": "Colorido", "quantity": 1}}
  ],
  "model_primary": "664XL",
  "is_xl": true,
  "colors_in_bundle": ["Preto", "Colorido"],
  "confidence": 0.95,
  "notes": "3-unit bundle: 2 black + 1 color XL cartridges"
}}

Return ONLY the JSON object, no additional text.
"""


# Usage example
if __name__ == "__main__":
    # Test with a real product
    test_product = {
        "titulo": "Kit 2 Cartuchos Hp 664xl (preto + Color) 2136 2676",
        "descricao": "Kit com 2 cartuchos originais HP 664XL. Conteúdo: 1 cartucho preto + 1 cartucho colorido..."
    }
    
    analyzer = LLMProductAnalyzer()
    result = analyzer.analyze_product_structure(test_product)
    
    print(f"Bundle: {result.is_bundle}")
    print(f"Quantity: {result.bundle_quantity}")
    print(f"Model: {result.model_primary}")
    print(f"Is XL: {result.is_xl}")
    print(f"Item breakdown: {result.item_breakdown}")
    print(f"Confidence: {result.confidence}")

