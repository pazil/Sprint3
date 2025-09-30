"""
LLM Review Analyzer
Analyzes each individual review using LLM for:
- Sentiment analysis
- Counterfeit signal detection
- Complaint categorization
- Keyword extraction with context
"""

from openai import OpenAI
from dotenv import load_dotenv
import os
from typing import Dict, List, Optional
from dataclasses import dataclass
import json

load_dotenv(override=True)


@dataclass
class ReviewAnalysis:
    """LLM analysis result for a single review"""
    review_number: int
    original_rating: int
    original_text: str
    
    # Sentiment
    sentiment: str  # "positive", "negative", "neutral", "mixed"
    sentiment_score: float  # -1.0 to 1.0
    
    # Authenticity signals
    authenticity_signal: str  # "likely_counterfeit", "likely_authentic", "unclear", "not_relevant"
    confidence: float  # 0-1
    
    # Categorized findings
    complaint_categories: List[str]  # ["durability", "recognition", "quality", "leaking", etc.]
    praise_categories: List[str]  # ["quality", "original", "value", etc.]
    
    # Keyword extraction with context
    counterfeit_keywords: List[str]  # Specific phrases that indicate fake
    authentic_keywords: List[str]  # Specific phrases that indicate real
    
    # Specific issues
    mentions_short_duration: bool
    mentions_printer_rejection: bool
    mentions_empty_cartridge: bool
    mentions_leaking: bool
    mentions_fake_claim: bool  # Explicit "não é original", "falsificado"
    mentions_authentic_claim: bool  # "original mesmo", "genuíno", "lacrado"
    mentions_page_count: bool  # Review mentions specific page count
    page_count_mentioned: Optional[int]  # Actual number if mentioned
    page_count_vs_expected: Optional[str]  # "much_below", "below", "normal", "above"
    
    # Overall assessment
    is_suspicious_review: bool
    severity: str  # "none", "low", "medium", "high", "critical"
    

class LLMReviewAnalyzer:
    """Analyze individual reviews with LLM"""
    
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.model = "gpt-5-nano"  # Using VALIDATED working model
        
        # Page yield expectations for context
        self.page_yields = {
            ("664", False, "Preto"): 120,
            ("664", False, "Colorido"): 100,
            ("664", True, "Preto"): 480,
            ("664", True, "Colorido"): 330
        }
        
    def analyze_review(self, review: Dict, product_context: Dict = None) -> ReviewAnalysis:
        """
        Analyze a single review using LLM
        
        Args:
            review: Review object with rating, date, text
            product_context: Optional product info for context
            
        Returns:
            ReviewAnalysis with structured findings
        """
        rating = review.get('rating', 0)
        text = review.get('text', '')
        date = review.get('date', '')
        likes = review.get('likes', 0)
        
        # Build prompts
        system_prompt = self._get_system_prompt(product_context)
        user_prompt = self._build_review_analysis_prompt(
            text, rating, date, likes, product_context
        )
        
        # Call LLM with VALIDATED working format
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )
        
        # Parse result (standard chat completions format)
        result = json.loads(response.choices[0].message.content)
        
        return ReviewAnalysis(
            review_number=review.get('review_number', 0),
            original_rating=rating,
            original_text=text,
            sentiment=result['sentiment'],
            sentiment_score=result['sentiment_score'],
            authenticity_signal=result['authenticity_signal'],
            confidence=result['confidence'],
            complaint_categories=result['complaint_categories'],
            praise_categories=result['praise_categories'],
            counterfeit_keywords=result['counterfeit_keywords'],
            authentic_keywords=result['authentic_keywords'],
            mentions_short_duration=result['mentions_short_duration'],
            mentions_printer_rejection=result['mentions_printer_rejection'],
            mentions_empty_cartridge=result['mentions_empty_cartridge'],
            mentions_leaking=result['mentions_leaking'],
            mentions_fake_claim=result['mentions_fake_claim'],
            mentions_authentic_claim=result['mentions_authentic_claim'],
            mentions_page_count=result.get('mentions_page_count', False),
            page_count_mentioned=result.get('page_count_mentioned'),
            page_count_vs_expected=result.get('page_count_vs_expected'),
            is_suspicious_review=result['is_suspicious_review'],
            severity=result['severity']
        )
    
    def analyze_all_reviews_for_product(
        self, 
        reviews: List[Dict],
        product_context: Dict = None
    ) -> List[ReviewAnalysis]:
        """
        Analyze all reviews for a product
        
        Args:
            reviews: List of review objects
            product_context: Product info for context
            
        Returns:
            List of ReviewAnalysis objects
        """
        analyses = []
        
        for review in reviews:
            text = review.get('text', '').strip()
            
            # Process all reviews with text (no filtering)
            if text:
                analysis = self.analyze_review(review, product_context)
                analyses.append(analysis)
        
        return analyses
    
    def _get_system_prompt(self, product_context: Dict = None) -> str:
        """System prompt defining the LLM's role with page yield context"""
        base_prompt = """You are an expert analyst specializing in detecting counterfeit HP printer cartridges through customer review analysis.

Your expertise includes:
- Understanding Portuguese customer reviews from Brazilian marketplace
- Identifying specific language patterns that indicate counterfeit products
- Distinguishing between product quality issues vs authenticity issues
- Extracting nuanced sentiment and context from brief or detailed text
- Understanding expected cartridge performance (page yields)

CONTEXT: HP Original cartridges are sold on Mercado Livre, but counterfeiters also sell:
1. Refilled/remanufactured cartridges claiming to be original (have less ink)
2. Empty or nearly-empty cartridges
3. Lower-quality counterfeits that fail quickly or aren't recognized by printers

EXPECTED PERFORMANCE (HP Original Cartridges):
- HP 664 Regular Black: Should print ~120 pages
- HP 664 Regular Color: Should print ~100 pages  
- HP 664XL Black: Should print ~480 pages (4x regular)
- HP 664XL Color: Should print ~330 pages (3x regular)

⚠️ COUNTERFEIT INDICATOR: Reviews mentioning "printed only 20-30 pages" when expecting 120+ pages suggest counterfeit with less ink.

Your analysis will be used to train a machine learning model for automated detection.
Be precise, contextual, and extract all relevant signals.

CRITICAL: You MUST return ONLY valid JSON. No other text, no markdown, no explanations.
Start your response with { and end with }."""
        
        # Add specific product yield if available
        if product_context and 'expected_pages' in product_context:
            base_prompt += f"\n\nTHIS PRODUCT should yield approximately {product_context['expected_pages']} pages."
        
        return base_prompt

    def _build_review_analysis_prompt(
        self, 
        text: str, 
        rating: int, 
        date: str, 
        likes: int,
        product_context: Dict = None
    ) -> str:
        """Build prompt for individual review analysis"""
        
        context_str = ""
        if product_context:
            expected_pages = product_context.get('expected_pages', 'Unknown')
            context_str = f"""
PRODUCT CONTEXT:
- Title: {product_context.get('titulo', 'Unknown')}
- Model: {product_context.get('model', 'Unknown')} {'XL' if product_context.get('is_xl') else 'Regular'}
- Expected Page Yield: {expected_pages} pages (HP specification)
- Price: R$ {product_context.get('preco', 'Unknown')}
- Seller: {product_context.get('vendedor', 'Unknown')}

⚠️ If review mentions specific page counts (e.g., "imprimiu 30 páginas"), compare to expected yield.
   If significantly below expected ({expected_pages} pages), this suggests counterfeit with less ink.
"""
        
        return f"""Analyze this customer review for an HP printer cartridge:

REVIEW:
- Rating: {rating} out of 5 stars
- Date: {date}
- Engagement: {likes} people found this useful
- Text: "{text}"
{context_str}

ANALYZE FOR:

1. **Sentiment Analysis**
   - Overall sentiment: positive, negative, neutral, or mixed
   - Sentiment score: -1.0 (very negative) to +1.0 (very positive)
   - Consider: Even short reviews like "Bom" are positive, "Ruim" is negative

2. **Authenticity Signals**
   - Does this review suggest the product is:
     * "likely_counterfeit" - indicates fake/refilled/defective
     * "likely_authentic" - confirms genuine HP product
     * "unclear" - doesn't provide authenticity info
     * "not_relevant" - review about shipping, packaging, etc.
   
3. **Complaint Categories** (if negative aspects mentioned):
   - "durability" - product ran out too quickly, didn't last
   - "recognition" - printer didn't recognize, blocked, rejected cartridge
   - "quality" - poor print quality, faded, streaks
   - "leaking" - ink leaking, spilling, messy
   - "empty" - cartridge came empty or nearly empty
   - "defective" - doesn't work, broken
   - "price" - too expensive, bad value
   - "shipping" - delivery issues
   - "packaging" - damaged packaging
   - "other" - specify in notes

4. **Praise Categories** (if positive aspects mentioned):
   - "quality" - good print quality
   - "original" - confirmed as genuine
   - "value" - good price, worth it
   - "durability" - lasted well, good yield
   - "compatibility" - worked perfectly with printer
   - "other" - specify in notes

5. **Keyword Extraction with Context**
   
   COUNTERFEIT INDICATORS (extract if present):
   - "não é original", "não original", "falso", "falsificado", "pirata", "fake"
   - "acabou rápido", "durou pouco", "acabou em X dias", "não durou"
   - "imprimiu X páginas" - CHECK: If X is much less than expected page yield, CRITICAL indicator
   - "veio vazio", "sem tinta", "pouca tinta", "seco"
   - "não reconhece", "não lê", "bloqueou", "não funciona", "impressora não reconheceu"
   - "vazou", "vazando", "sujou"
   - "recarregado", "recarga"
   
   ⚠️ PAGE YIELD ANALYSIS:
   - If review mentions "imprimiu 30 páginas" and expected is 120+ pages → STRONG counterfeit indicator
   - If mentions "imprimiu 100 páginas" and expected is 120 → Normal variation (acceptable)
   - If mentions "imprimiu 500 páginas" and expected is 480 → Better than expected (good sign)
   
   AUTHENTIC INDICATORS (extract if present):
   - "original mesmo", "genuíno", "lacrado", "HP reconheceu"
   - "original" (ONLY if positive context: "produto original, muito bom")
   - "duradouro", "rendeu bem", "dura bastante"
   - "qualidade HP", "perfeito", "conforme esperado"
   
   ⚠️ CONTEXT MATTERS: 
   - "Original" can be positive ("produto original") or negative ("diz ser original mas...")
   - Analyze the FULL sentence to determine context

6. **Specific Issue Flags** (boolean for each):
   - mentions_short_duration: Review mentions product ran out too fast
   - mentions_printer_rejection: Printer didn't recognize cartridge
   - mentions_empty_cartridge: Came empty or nearly empty
   - mentions_leaking: Ink leaking problems
   - mentions_fake_claim: Explicit claim of counterfeit
   - mentions_authentic_claim: Explicit confirmation of authenticity

7. **Overall Assessment**:
   - is_suspicious_review: Should this review raise counterfeit concerns? (boolean)
   - severity: "none", "low", "medium", "high", "critical"
     * "critical" - explicit fake claim or printer rejection
     * "high" - came empty, leaked, major defect
     * "medium" - ran out too quickly, quality issues
     * "low" - minor complaints
     * "none" - positive or neutral

Return JSON in this EXACT structure:
{{
  "sentiment": "positive|negative|neutral|mixed",
  "sentiment_score": float (-1.0 to 1.0),
  "authenticity_signal": "likely_counterfeit|likely_authentic|unclear|not_relevant",
  "confidence": float (0.0 to 1.0),
  "complaint_categories": [list of strings],
  "praise_categories": [list of strings],
  "counterfeit_keywords": [list of extracted phrases],
  "authentic_keywords": [list of extracted phrases],
  "mentions_short_duration": boolean,
  "mentions_printer_rejection": boolean,
  "mentions_empty_cartridge": boolean,
  "mentions_leaking": boolean,
  "mentions_fake_claim": boolean,
  "mentions_authentic_claim": boolean,
  "mentions_page_count": boolean (true if review mentions specific page count),
  "page_count_mentioned": integer or null (extract number: "30" from "imprimiu 30 páginas"),
  "page_count_vs_expected": "much_below|below|normal|above|null" (compare mentioned to expected if applicable),
  "is_suspicious_review": boolean,
  "severity": "none|low|medium|high|critical",
  "notes": "any additional context or ambiguities"
}}

IMPORTANT: Analyze in PORTUGUESE context. Many reviews are brief but meaningful.
"Ótimo" = great (positive), "Péssimo" = terrible (negative), "Não dura" = doesn't last (counterfeit signal)
"""


# Usage example
if __name__ == "__main__":
    analyzer = LLMReviewAnalyzer()
    
    # Test reviews
    test_reviews = [
        {
            "review_number": 1,
            "rating": 5,
            "date": "06 jun. 2024",
            "text": "Ótimo produto.",
            "likes": 0
        },
        {
            "review_number": 2,
            "rating": 1,
            "date": "12 nov. 2023",
            "text": "Não dura nada o produto.",
            "likes": 0
        },
        {
            "review_number": 3,
            "rating": 1,
            "date": "17 jul. 2020",
            "text": "Tive problemas com a impressora ( ficou tudo falhado a impressão) no dia seguinte vou tirar o cartucho, no visor da impressora consta que está acabando a tinta ( como pode se nem usei ??)",
            "likes": 8
        }
    ]
    
    print("Analyzing reviews with LLM...\n")
    
    for review in test_reviews:
        print(f"Review {review['review_number']} [{review['rating']}★]: {review['text'][:50]}...")
        analysis = analyzer.analyze_review(review)
        print(f"  Sentiment: {analysis.sentiment} ({analysis.sentiment_score:.2f})")
        print(f"  Authenticity: {analysis.authenticity_signal}")
        print(f"  Suspicious: {analysis.is_suspicious_review}")
        print(f"  Severity: {analysis.severity}")
        if analysis.counterfeit_keywords:
            print(f"  🚩 Counterfeit keywords: {analysis.counterfeit_keywords}")
        print()

