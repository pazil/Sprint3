"""
Statistical Review Analyzer
Analyzes rating distributions using mathematical/statistical methods
Works on ALL products (including those without review text)
"""

import math
from typing import Dict, List, Tuple
from dataclasses import dataclass


@dataclass
class StatisticalReviewFeatures:
    """Statistical features extracted from rating distribution"""
    # Basic metrics
    average_rating: float
    total_reviews: int
    has_reviews: bool
    
    # Distribution analysis
    rating_distribution: Dict[int, int]  # {5: count, 4: count, ...}
    distribution_percentages: Dict[int, float]  # {5: 86.0%, ...}
    
    # Positive/negative segmentation
    positive_count: int  # 4-5 star
    neutral_count: int   # 3 star
    negative_count: int  # 1-2 star
    positive_pct: float
    neutral_pct: float
    negative_pct: float
    
    # Pattern detection
    is_bimodal: bool
    bimodal_score: float  # 0-100, higher = more polarized
    polarization_index: float  # Standard deviation
    
    # Quality metrics
    volume_confidence: float  # 0-1, based on review count
    distribution_health: str  # "healthy", "polarized", "suspicious", "insufficient"
    
    # Trust score (0-1)
    statistical_trust_score: float
    
    # Flags
    suspicious_patterns: List[str]


class StatisticalReviewAnalyzer:
    """Statistical analysis of rating distributions"""
    
    def analyze(self, product: Dict) -> StatisticalReviewFeatures:
        """
        Perform complete statistical analysis on product reviews
        
        Args:
            product: Product object from main dataset
            
        Returns:
            StatisticalReviewFeatures with all metrics
        """
        # Extract rating data
        avg_rating = product.get('rating_medio', 0.0)
        total = product.get('total_reviews', 0)
        
        distribution = {
            5: product.get('rating_5_estrelas', 0),
            4: product.get('rating_4_estrelas', 0),
            3: product.get('rating_3_estrelas', 0),
            2: product.get('rating_2_estrelas', 0),
            1: product.get('rating_1_estrela', 0)
        }
        
        # Handle no-review case
        if total == 0:
            return self._create_zero_review_features(product)
        
        # Calculate percentages
        percentages = {
            star: (count / total * 100) if total > 0 else 0
            for star, count in distribution.items()
        }
        
        # Positive/negative segmentation
        positive = distribution[5] + distribution[4]
        neutral = distribution[3]
        negative = distribution[1] + distribution[2]
        
        positive_pct = (positive / total * 100) if total > 0 else 0
        neutral_pct = (neutral / total * 100) if total > 0 else 0
        negative_pct = (negative / total * 100) if total > 0 else 0
        
        # Pattern detection
        bimodal, bimodal_score = self._detect_bimodal(distribution, total)
        polarization = self._calculate_polarization(distribution, total)
        
        # Volume confidence
        volume_conf = self._calculate_volume_confidence(total)
        
        # Distribution health
        health = self._assess_distribution_health(
            avg_rating, negative_pct, bimodal_score, total
        )
        
        # Trust score
        trust_score = self._calculate_trust_score(
            avg_rating, total, bimodal_score, negative_pct, volume_conf
        )
        
        # Suspicious patterns
        patterns = self._identify_suspicious_patterns(
            avg_rating, total, distribution, bimodal_score, negative_pct
        )
        
        return StatisticalReviewFeatures(
            average_rating=avg_rating,
            total_reviews=total,
            has_reviews=True,
            rating_distribution=distribution,
            distribution_percentages=percentages,
            positive_count=positive,
            neutral_count=neutral,
            negative_count=negative,
            positive_pct=positive_pct,
            neutral_pct=neutral_pct,
            negative_pct=negative_pct,
            is_bimodal=bimodal,
            bimodal_score=bimodal_score,
            polarization_index=polarization,
            volume_confidence=volume_conf,
            distribution_health=health,
            statistical_trust_score=trust_score,
            suspicious_patterns=patterns
        )
    
    def _create_zero_review_features(self, product: Dict) -> StatisticalReviewFeatures:
        """Create features object for products with no reviews"""
        return StatisticalReviewFeatures(
            average_rating=0.0,
            total_reviews=0,
            has_reviews=False,
            rating_distribution={5: 0, 4: 0, 3: 0, 2: 0, 1: 0},
            distribution_percentages={5: 0.0, 4: 0.0, 3: 0.0, 2: 0.0, 1: 0.0},
            positive_count=0,
            neutral_count=0,
            negative_count=0,
            positive_pct=0.0,
            neutral_pct=0.0,
            negative_pct=0.0,
            is_bimodal=False,
            bimodal_score=0.0,
            polarization_index=0.0,
            volume_confidence=0.0,
            distribution_health="insufficient",
            statistical_trust_score=0.5,  # Neutral when no data
            suspicious_patterns=["NO_REVIEWS"]
        )
    
    def _detect_bimodal(
        self, 
        distribution: Dict[int, int], 
        total: int
    ) -> Tuple[bool, float]:
        """
        Detect bimodal distribution pattern (high 5-star AND high 1-star)
        
        Returns:
            (is_bimodal, bimodal_score)
            bimodal_score: 0-100, higher = more polarized
        """
        if total < 10:
            return False, 0.0
        
        five_star_pct = distribution[5] / total
        one_star_pct = distribution[1] / total
        extreme_pct = five_star_pct + one_star_pct
        
        # Calculate bimodal score (product of extremes)
        # High when both extremes are high
        bimodal_score = (five_star_pct * one_star_pct) * 400  # Scale to 0-100
        
        # Flag as bimodal if:
        # - More than 70% at extremes AND
        # - More than 10% are 1-star (lowered threshold per our discussion)
        is_bimodal = extreme_pct > 0.7 and one_star_pct > 0.1
        
        return is_bimodal, bimodal_score
    
    def _calculate_polarization(
        self, 
        distribution: Dict[int, int], 
        total: int
    ) -> float:
        """
        Calculate polarization index (standard deviation of ratings)
        
        Higher value = more spread out = more polarized
        """
        if total == 0:
            return 0.0
        
        # Calculate weighted mean
        mean = sum(
            star * count for star, count in distribution.items()
        ) / total
        
        # Calculate variance
        variance = sum(
            (star - mean) ** 2 * count 
            for star, count in distribution.items()
        ) / total
        
        # Standard deviation
        return math.sqrt(variance)
    
    def _calculate_volume_confidence(self, total: int) -> float:
        """
        Calculate confidence based on review volume
        More reviews = higher confidence in the signal
        
        Returns: 0-1 scale
        """
        if total == 0:
            return 0.0
        elif total < 5:
            return 0.3
        elif total < 10:
            return 0.5
        elif total < 30:
            return 0.7
        elif total < 100:
            return 0.9
        else:
            return 1.0
    
    def _assess_distribution_health(
        self,
        avg_rating: float,
        negative_pct: float,
        bimodal_score: float,
        total: int
    ) -> str:
        """
        Categorize distribution health
        
        Returns:
            "healthy", "polarized", "suspicious", "insufficient"
        """
        if total < 5:
            return "insufficient"
        
        if bimodal_score > 25 or negative_pct > 25:
            return "suspicious"
        
        if bimodal_score > 15 or negative_pct > 15:
            return "polarized"
        
        if avg_rating >= 4.5 and negative_pct < 10:
            return "healthy"
        
        return "polarized"
    
    def _calculate_trust_score(
        self,
        avg_rating: float,
        total: int,
        bimodal_score: float,
        negative_pct: float,
        volume_confidence: float
    ) -> float:
        """
        Calculate overall statistical trust score (0-1)
        
        Combines multiple signals:
        - Average rating (higher = better)
        - Volume confidence (more reviews = more reliable)
        - Bimodal penalty (polarized = less trustworthy)
        - Negative review penalty
        
        Returns: 0-1 scale, 1 = highly trustworthy reviews
        """
        # Component 1: Average rating score (0-1)
        rating_score = avg_rating / 5.0
        
        # Component 2: Volume confidence (0-1)
        # Already calculated
        
        # Component 3: Bimodal penalty (reduce trust if polarized)
        bimodal_penalty = bimodal_score / 100  # 0-1
        
        # Component 4: Negative review penalty
        negative_penalty = min(negative_pct / 100, 0.5)  # Cap at 0.5
        
        # Weighted combination
        trust = (
            rating_score * 0.4 +
            volume_confidence * 0.2 +
            (1 - bimodal_penalty) * 0.2 +
            (1 - negative_penalty) * 0.2
        )
        
        # Ensure 0-1 range
        return max(0.0, min(1.0, trust))
    
    def _identify_suspicious_patterns(
        self,
        avg_rating: float,
        total: int,
        distribution: Dict[int, int],
        bimodal_score: float,
        negative_pct: float
    ) -> List[str]:
        """
        Identify suspicious patterns in rating distribution
        
        Returns:
            List of pattern flags
        """
        patterns = []
        
        if total == 0:
            patterns.append("NO_REVIEWS")
            return patterns
        
        # Pattern 1: Bimodal distribution
        if bimodal_score > 25:
            patterns.append("BIMODAL_DISTRIBUTION")
        elif bimodal_score > 15:
            patterns.append("MODERATE_POLARIZATION")
        
        # Pattern 2: Low average with volume
        if avg_rating < 4.5 and total > 10:
            patterns.append("LOW_AVERAGE_WITH_VOLUME")
        
        # Pattern 3: High negative percentage
        if negative_pct > 25:
            patterns.append("HIGH_NEGATIVE_PERCENTAGE")
        elif negative_pct > 15:
            patterns.append("MODERATE_NEGATIVE_PERCENTAGE")
        
        # Pattern 4: Low volume
        if total < 5:
            patterns.append("LOW_VOLUME")
        
        # Pattern 5: Perfect ratings (suspicious if too perfect with volume)
        if avg_rating == 5.0 and total > 50:
            patterns.append("SUSPICIOUSLY_PERFECT")
        
        # Pattern 6: Many 1-stars
        if distribution[1] > 10 and total > 50:
            patterns.append("MANY_ONE_STAR_REVIEWS")
        
        return patterns if patterns else ["NORMAL_DISTRIBUTION"]


# Usage example
if __name__ == "__main__":
    # Test with real product data
    test_product = {
        "id": "MLB3159055901",
        "rating_medio": 4.7,
        "total_reviews": 43,
        "rating_5_estrelas": 37,
        "rating_4_estrelas": 1,
        "rating_3_estrelas": 1,
        "rating_2_estrelas": 1,
        "rating_1_estrela": 1
    }
    
    analyzer = StatisticalReviewAnalyzer()
    features = analyzer.analyze(test_product)
    
    print(f"Product: {test_product['id']}")
    print(f"Average Rating: {features.average_rating}")
    print(f"Total Reviews: {features.total_reviews}")
    print(f"\nDistribution:")
    for star, pct in sorted(features.distribution_percentages.items(), reverse=True):
        print(f"  {star}★: {pct:.1f}%")
    print(f"\nPositive: {features.positive_pct:.1f}%")
    print(f"Negative: {features.negative_pct:.1f}%")
    print(f"\nBimodal: {features.is_bimodal} (score: {features.bimodal_score:.1f})")
    print(f"Polarization: {features.polarization_index:.2f}")
    print(f"Trust Score: {features.statistical_trust_score:.2f}")
    print(f"Health: {features.distribution_health}")
    print(f"Patterns: {features.suspicious_patterns}")

