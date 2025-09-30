"""
Review Weight Calculator
Combines statistical and LLM features into final review trustworthiness weight
"""

from typing import Dict, Optional
from dataclasses import dataclass


@dataclass
class ReviewWeight:
    """Final review weight with component breakdown"""
    # Final weight (0-1, where 1 = highly trustworthy reviews)
    review_weight: float
    
    # Inverted for risk (0-1, where 1 = high risk from reviews)
    review_risk_score: float
    
    # Component scores
    statistical_component: float  # 0-1
    llm_component: Optional[float]  # 0-1, None if no LLM data
    
    # Weights applied
    statistical_weight: float  # Weight used for statistical
    llm_weight: float  # Weight used for LLM
    
    # Interpretation
    interpretation: str  # "HIGHLY_TRUSTWORTHY", "TRUSTWORTHY", etc.
    confidence: str  # "HIGH", "MEDIUM", "LOW"
    
    # Explanation
    reasoning: str


class ReviewWeightCalculator:
    """Calculate final review weights combining multiple signals"""
    
    def calculate(
        self,
        statistical_features,  # StatisticalReviewFeatures
        llm_features = None  # ProductLevelReviewAnalysis (optional)
    ) -> ReviewWeight:
        """
        Calculate final review weight
        
        Logic:
        - If product has LLM analysis: Combine statistical + LLM
        - If no LLM analysis: Use statistical only with adjusted weights
        - Statistical always contributes (covers ALL reviews)
        - LLM adds semantic depth (when available)
        
        Args:
            statistical_features: From StatisticalReviewAnalyzer
            llm_features: From ReviewAggregator (None if no text reviews)
            
        Returns:
            ReviewWeight with final scores
        """
        # Get statistical trust score (0-1)
        stat_score = statistical_features.statistical_trust_score
        
        # Check if we have LLM data
        has_llm = llm_features is not None and llm_features.total_reviews_analyzed > 0
        
        if has_llm:
            # Scenario: We have BOTH statistical and LLM
            final_weight, reasoning = self._combine_statistical_and_llm(
                statistical_features, llm_features
            )
            stat_weight_used = 0.4
            llm_weight_used = 0.6
            confidence = self._assess_confidence(
                statistical_features, llm_features
            )
        else:
            # Scenario: Statistical ONLY
            final_weight = stat_score
            stat_weight_used = 1.0
            llm_weight_used = 0.0
            confidence = "LOW" if statistical_features.total_reviews < 10 else "MEDIUM"
            reasoning = "Based on statistical distribution only (no review text available)"
        
        # Invert for risk score
        risk_score = 1.0 - final_weight
        
        # Interpret
        interpretation = self._interpret_weight(final_weight)
        
        return ReviewWeight(
            review_weight=final_weight,
            review_risk_score=risk_score,
            statistical_component=stat_score,
            llm_component=1.0 - llm_features.llm_review_risk_score if has_llm else None,
            statistical_weight=stat_weight_used,
            llm_weight=llm_weight_used,
            interpretation=interpretation,
            confidence=confidence,
            reasoning=reasoning
        )
    
    def _combine_statistical_and_llm(
        self,
        stat_features,
        llm_features
    ) -> tuple[float, str]:
        """
        Combine statistical and LLM signals
        
        Logic:
        - Statistical covers ALL reviews (volume signal)
        - LLM covers SAMPLE of reviews (semantic signal)
        - Weight LLM higher if it analyzed many reviews
        - Weight statistical higher if LLM only saw few reviews
        
        Returns:
            (combined_weight, reasoning)
        """
        stat_score = stat_features.statistical_trust_score
        
        # Convert LLM risk to trust (invert)
        llm_trust = 1.0 - llm_features.llm_review_risk_score
        
        # Adjust weights based on LLM coverage
        total_reviews = stat_features.total_reviews
        analyzed_reviews = llm_features.total_reviews_analyzed
        
        if total_reviews > 0:
            llm_coverage = min(1.0, analyzed_reviews / total_reviews)
        else:
            llm_coverage = 1.0
        
        # Dynamic weighting based on coverage
        # High coverage (analyzed 80%+): Weight LLM more (60%)
        # Low coverage (analyzed <20%): Weight statistical more (70%)
        
        if llm_coverage >= 0.8:
            stat_w, llm_w = 0.4, 0.6
            coverage_note = "high LLM coverage"
        elif llm_coverage >= 0.5:
            stat_w, llm_w = 0.5, 0.5
            coverage_note = "moderate LLM coverage"
        elif llm_coverage >= 0.2:
            stat_w, llm_w = 0.6, 0.4
            coverage_note = "limited LLM coverage"
        else:
            stat_w, llm_w = 0.7, 0.3
            coverage_note = "sparse LLM coverage"
        
        # Combine
        combined = (stat_score * stat_w) + (llm_trust * llm_w)
        
        # Build reasoning
        reasoning_parts = [
            f"Combined statistical ({stat_score:.2f}) and LLM ({llm_trust:.2f})",
            f"Weights: {stat_w:.0%} statistical, {llm_w:.0%} LLM",
            f"Coverage: {llm_coverage:.0%} ({coverage_note})"
        ]
        
        # Add specific signals
        if llm_features.critical_reviews > 0:
            reasoning_parts.append(f"⚠️ {llm_features.critical_reviews} critical reviews found")
        
        if llm_features.pct_mention_fake_claim > 0:
            reasoning_parts.append(f"🚩 {llm_features.pct_mention_fake_claim:.0f}% mention counterfeit")
        
        reasoning = "; ".join(reasoning_parts)
        
        return combined, reasoning
    
    def _assess_confidence(
        self,
        stat_features,
        llm_features
    ) -> str:
        """
        Assess confidence level in the review weight
        
        Returns:
            "HIGH", "MEDIUM", "LOW"
        """
        # High confidence requires:
        # - Good review volume (50+)
        # - Good LLM analysis coverage
        # - High LLM confidence scores
        
        volume = stat_features.total_reviews
        llm_analyzed = llm_features.total_reviews_analyzed if llm_features else 0
        llm_conf = llm_features.average_confidence if llm_features else 0
        
        if volume >= 50 and llm_analyzed >= 20 and llm_conf >= 0.8:
            return "HIGH"
        elif volume >= 20 and llm_analyzed >= 5:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _interpret_weight(self, weight: float) -> str:
        """Interpret review weight value"""
        if weight >= 0.85:
            return "HIGHLY_TRUSTWORTHY"
        elif weight >= 0.70:
            return "TRUSTWORTHY"
        elif weight >= 0.50:
            return "MODERATELY_TRUSTWORTHY"
        elif weight >= 0.35:
            return "UNCERTAIN"
        elif weight >= 0.20:
            return "SUSPICIOUS"
        else:
            return "HIGHLY_SUSPICIOUS"


# Usage example
if __name__ == "__main__":
    from pipeline.statistical_review_analyzer import StatisticalReviewAnalyzer, StatisticalReviewFeatures
    from pipeline.review_aggregator import ProductLevelReviewAnalysis
    
    # Test product with good reviews
    test_product_good = {
        "rating_medio": 4.7,
        "total_reviews": 43,
        "rating_5_estrelas": 37,
        "rating_4_estrelas": 1,
        "rating_3_estrelas": 1,
        "rating_2_estrelas": 1,
        "rating_1_estrela": 3
    }
    
    stat_analyzer = StatisticalReviewAnalyzer()
    stat_features = stat_analyzer.analyze(test_product_good)
    
    # Simulate LLM analysis result
    llm_features = ProductLevelReviewAnalysis(
        total_reviews_analyzed=3,
        reviews_with_text=3,
        sentiment_distribution={"positive": 2, "negative": 1},
        sentiment_distribution_pct={"positive": 66.7, "negative": 33.3},
        average_sentiment_score=0.5,
        authenticity_distribution={"likely_authentic": 2, "likely_counterfeit": 1},
        counterfeit_signal_count=1,
        authentic_signal_count=2,
        unclear_signal_count=0,
        authenticity_ratio=0.67,
        complaint_frequency={"durability": 1},
        top_complaints=[("durability", 1)],
        counterfeit_keywords_found=["não dura"],
        authentic_keywords_found=["ótimo", "original"],
        pct_mention_short_duration=33.3,
        pct_mention_printer_rejection=0.0,
        pct_mention_empty=0.0,
        pct_mention_leaking=0.0,
        pct_mention_fake_claim=0.0,
        pct_mention_authentic_claim=0.0,
        severity_distribution={"none": 2, "medium": 1},
        critical_reviews=0,
        high_severity_reviews=0,
        suspicious_review_count=1,
        suspicious_review_pct=33.3,
        average_confidence=0.85,
        llm_review_risk_score=0.3
    )
    
    calculator = ReviewWeightCalculator()
    weight = calculator.calculate(stat_features, llm_features)
    
    print(f"Review Weight: {weight.review_weight:.3f}")
    print(f"Review Risk: {weight.review_risk_score:.3f}")
    print(f"Interpretation: {weight.interpretation}")
    print(f"Confidence: {weight.confidence}")
    print(f"\nComponents:")
    print(f"  Statistical: {weight.statistical_component:.3f} (weight: {weight.statistical_weight:.0%})")
    print(f"  LLM: {weight.llm_component:.3f} (weight: {weight.llm_weight:.0%})")
    print(f"\nReasoning: {weight.reasoning}")

