"""
Review Aggregator
Aggregates individual review LLM analyses into product-level features
"""

from typing import List, Dict, Tuple
from dataclasses import dataclass
from collections import Counter


@dataclass
class ProductLevelReviewAnalysis:
    """Aggregated analysis of all reviews for a product"""
    # Volume metrics
    total_reviews_analyzed: int
    reviews_with_text: int
    
    # Sentiment aggregation
    sentiment_distribution: Dict[str, int]  # {"positive": 20, "negative": 3, ...}
    sentiment_distribution_pct: Dict[str, float]
    average_sentiment_score: float  # -1 to 1
    
    # Authenticity aggregation
    authenticity_distribution: Dict[str, int]  # {"likely_counterfeit": 5, ...}
    counterfeit_signal_count: int
    authentic_signal_count: int
    unclear_signal_count: int
    authenticity_ratio: float  # authentic / (authentic + counterfeit), 0-1
    
    # Complaint analysis
    complaint_frequency: Dict[str, int]  # {"durability": 5, "recognition": 2, ...}
    top_complaints: List[Tuple[str, int]]  # Top 3 complaints
    
    # Keyword aggregation
    counterfeit_keywords_found: List[str]
    authentic_keywords_found: List[str]
    
    # Issue flags (% of reviews mentioning each)
    pct_mention_short_duration: float
    pct_mention_printer_rejection: float
    pct_mention_empty: float
    pct_mention_leaking: float
    pct_mention_fake_claim: float
    pct_mention_authentic_claim: float
    
    # Severity distribution
    severity_distribution: Dict[str, int]
    critical_reviews: int  # Count of "critical" severity
    high_severity_reviews: int
    
    # Overall LLM assessment
    suspicious_review_count: int
    suspicious_review_pct: float
    
    # Confidence
    average_confidence: float
    
    # Risk score (0-1, 1 = high risk from reviews)
    llm_review_risk_score: float


class ReviewAggregator:
    """Aggregate individual review analyses to product level"""
    
    def aggregate(
        self, 
        review_analyses: List
    ) -> ProductLevelReviewAnalysis:
        """
        Aggregate multiple ReviewAnalysis objects into product-level metrics
        
        Args:
            review_analyses: List of ReviewAnalysis from LLM
            
        Returns:
            ProductLevelReviewAnalysis
        """
        if not review_analyses:
            return self._create_empty_analysis()
        
        total = len(review_analyses)
        
        # Sentiment aggregation
        sentiment_counts = Counter(r.sentiment for r in review_analyses)
        sentiment_pcts = {
            sent: (count / total * 100) 
            for sent, count in sentiment_counts.items()
        }
        avg_sentiment = sum(r.sentiment_score for r in review_analyses) / total
        
        # Authenticity aggregation
        authenticity_counts = Counter(r.authenticity_signal for r in review_analyses)
        counterfeit_count = authenticity_counts.get('likely_counterfeit', 0)
        authentic_count = authenticity_counts.get('likely_authentic', 0)
        unclear_count = authenticity_counts.get('unclear', 0) + authenticity_counts.get('not_relevant', 0)
        
        # Calculate authenticity ratio (1.0 = all authentic, 0.0 = all counterfeit)
        if counterfeit_count + authentic_count > 0:
            auth_ratio = authentic_count / (authentic_count + counterfeit_count)
        else:
            auth_ratio = 0.5  # Neutral if no clear signals
        
        # Complaint frequency
        all_complaints = []
        for r in review_analyses:
            all_complaints.extend(r.complaint_categories)
        complaint_freq = Counter(all_complaints)
        top_complaints = complaint_freq.most_common(3)
        
        # Keyword aggregation (unique keywords)
        counterfeit_kw = []
        authentic_kw = []
        for r in review_analyses:
            counterfeit_kw.extend(r.counterfeit_keywords)
            authentic_kw.extend(r.authentic_keywords)
        
        counterfeit_kw_unique = list(set(counterfeit_kw))
        authentic_kw_unique = list(set(authentic_kw))
        
        # Issue flag percentages
        pct_short_duration = sum(
            1 for r in review_analyses if r.mentions_short_duration
        ) / total * 100
        
        pct_printer_rejection = sum(
            1 for r in review_analyses if r.mentions_printer_rejection
        ) / total * 100
        
        pct_empty = sum(
            1 for r in review_analyses if r.mentions_empty_cartridge
        ) / total * 100
        
        pct_leaking = sum(
            1 for r in review_analyses if r.mentions_leaking
        ) / total * 100
        
        pct_fake_claim = sum(
            1 for r in review_analyses if r.mentions_fake_claim
        ) / total * 100
        
        pct_auth_claim = sum(
            1 for r in review_analyses if r.mentions_authentic_claim
        ) / total * 100
        
        # Severity distribution
        severity_counts = Counter(r.severity for r in review_analyses)
        critical_count = severity_counts.get('critical', 0)
        high_count = severity_counts.get('high', 0)
        
        # Suspicious review count
        suspicious_count = sum(1 for r in review_analyses if r.is_suspicious_review)
        suspicious_pct = (suspicious_count / total * 100) if total > 0 else 0
        
        # Average confidence
        avg_confidence = sum(r.confidence for r in review_analyses) / total
        
        # Calculate LLM review risk score (0-1, higher = more risky)
        llm_risk = self._calculate_llm_risk_score(
            counterfeit_count,
            authentic_count,
            suspicious_count,
            total,
            pct_printer_rejection,
            pct_fake_claim,
            avg_sentiment
        )
        
        return ProductLevelReviewAnalysis(
            total_reviews_analyzed=total,
            reviews_with_text=total,
            sentiment_distribution=dict(sentiment_counts),
            sentiment_distribution_pct=sentiment_pcts,
            average_sentiment_score=avg_sentiment,
            authenticity_distribution=dict(authenticity_counts),
            counterfeit_signal_count=counterfeit_count,
            authentic_signal_count=authentic_count,
            unclear_signal_count=unclear_count,
            authenticity_ratio=auth_ratio,
            complaint_frequency=dict(complaint_freq),
            top_complaints=top_complaints,
            counterfeit_keywords_found=counterfeit_kw_unique,
            authentic_keywords_found=authentic_kw_unique,
            pct_mention_short_duration=pct_short_duration,
            pct_mention_printer_rejection=pct_printer_rejection,
            pct_mention_empty=pct_empty,
            pct_mention_leaking=pct_leaking,
            pct_mention_fake_claim=pct_fake_claim,
            pct_mention_authentic_claim=pct_auth_claim,
            severity_distribution=dict(severity_counts),
            critical_reviews=critical_count,
            high_severity_reviews=high_count,
            suspicious_review_count=suspicious_count,
            suspicious_review_pct=suspicious_pct,
            average_confidence=avg_confidence,
            llm_review_risk_score=llm_risk
        )
    
    def _create_empty_analysis(self) -> ProductLevelReviewAnalysis:
        """Create analysis object for products with no text reviews"""
        return ProductLevelReviewAnalysis(
            total_reviews_analyzed=0,
            reviews_with_text=0,
            sentiment_distribution={},
            sentiment_distribution_pct={},
            average_sentiment_score=0.0,
            authenticity_distribution={},
            counterfeit_signal_count=0,
            authentic_signal_count=0,
            unclear_signal_count=0,
            authenticity_ratio=0.5,
            complaint_frequency={},
            top_complaints=[],
            counterfeit_keywords_found=[],
            authentic_keywords_found=[],
            pct_mention_short_duration=0.0,
            pct_mention_printer_rejection=0.0,
            pct_mention_empty=0.0,
            pct_mention_leaking=0.0,
            pct_mention_fake_claim=0.0,
            pct_mention_authentic_claim=0.0,
            severity_distribution={},
            critical_reviews=0,
            high_severity_reviews=0,
            suspicious_review_count=0,
            suspicious_review_pct=0.0,
            average_confidence=0.0,
            llm_review_risk_score=0.5  # Neutral when no data
        )
    
    def _calculate_llm_risk_score(
        self,
        counterfeit_count: int,
        authentic_count: int,
        suspicious_count: int,
        total: int,
        pct_printer_rejection: float,
        pct_fake_claim: float,
        avg_sentiment: float
    ) -> float:
        """
        Calculate overall risk score from LLM signals (0-1)
        
        Higher score = higher risk of counterfeit
        """
        # Component 1: Authenticity ratio (inverted)
        # High authentic = low risk, high counterfeit = high risk
        if counterfeit_count + authentic_count > 0:
            auth_component = counterfeit_count / (counterfeit_count + authentic_count)
        else:
            auth_component = 0.5
        
        # Component 2: Suspicious review percentage
        susp_component = suspicious_count / total if total > 0 else 0.5
        
        # Component 3: Critical issue flags
        critical_component = (pct_printer_rejection + pct_fake_claim) / 200  # Normalize to 0-1
        
        # Component 4: Sentiment (inverted and normalized)
        # -1 sentiment → 1.0 risk, +1 sentiment → 0.0 risk
        sentiment_component = (1 - avg_sentiment) / 2  # -1 to 1 → 1 to 0
        
        # Weighted combination
        risk_score = (
            auth_component * 0.35 +
            susp_component * 0.25 +
            critical_component * 0.25 +
            sentiment_component * 0.15
        )
        
        return max(0.0, min(1.0, risk_score))


# Usage example
if __name__ == "__main__":
    from pipeline.llm_review_analyzer import ReviewAnalysis
    
    # Simulate some review analyses
    test_analyses = [
        ReviewAnalysis(
            review_number=1,
            original_rating=5,
            original_text="Ótimo produto",
            sentiment="positive",
            sentiment_score=0.9,
            authenticity_signal="likely_authentic",
            confidence=0.8,
            complaint_categories=[],
            praise_categories=["quality"],
            counterfeit_keywords=[],
            authentic_keywords=["ótimo"],
            mentions_short_duration=False,
            mentions_printer_rejection=False,
            mentions_empty_cartridge=False,
            mentions_leaking=False,
            mentions_fake_claim=False,
            mentions_authentic_claim=False,
            is_suspicious_review=False,
            severity="none"
        ),
        ReviewAnalysis(
            review_number=2,
            original_rating=1,
            original_text="Não dura nada",
            sentiment="negative",
            sentiment_score=-0.8,
            authenticity_signal="likely_counterfeit",
            confidence=0.9,
            complaint_categories=["durability"],
            praise_categories=[],
            counterfeit_keywords=["não dura"],
            authentic_keywords=[],
            mentions_short_duration=True,
            mentions_printer_rejection=False,
            mentions_empty_cartridge=False,
            mentions_leaking=False,
            mentions_fake_claim=False,
            mentions_authentic_claim=False,
            is_suspicious_review=True,
            severity="medium"
        )
    ]
    
    aggregator = ReviewAggregator()
    product_analysis = aggregator.aggregate(test_analyses)
    
    print(f"Analyzed {product_analysis.total_reviews_analyzed} reviews")
    print(f"Sentiment: {product_analysis.average_sentiment_score:.2f}")
    print(f"Counterfeit signals: {product_analysis.counterfeit_signal_count}")
    print(f"Authentic signals: {product_analysis.authentic_signal_count}")
    print(f"Authenticity ratio: {product_analysis.authenticity_ratio:.2f}")
    print(f"Suspicious reviews: {product_analysis.suspicious_review_pct:.1f}%")
    print(f"LLM Risk Score: {product_analysis.llm_review_risk_score:.2f}")

