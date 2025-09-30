"""
Main Anti-Piracy Detection Pipeline
Orchestrates the complete analysis flow
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from tqdm import tqdm
import time
import importlib.util
import sys

def load_module(module_path, module_name):
    """Load a module from file path"""
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

# Load modules
pipeline_dir = Path(__file__).parent
data_loader_mod = load_module(pipeline_dir / "01_data_loader.py", "data_loader")
product_analyzer_mod = load_module(pipeline_dir / "02_llm_product_analyzer.py", "product_analyzer")
review_analyzer_mod = load_module(pipeline_dir / "03_llm_review_analyzer.py", "review_analyzer")
stat_analyzer_mod = load_module(pipeline_dir / "04_statistical_review_analyzer.py", "stat_analyzer")
price_analyzer_mod = load_module(pipeline_dir / "05_price_analyzer.py", "price_analyzer")
aggregator_mod = load_module(pipeline_dir / "06_review_aggregator.py", "aggregator")
weight_calc_mod = load_module(pipeline_dir / "07_review_weight_calculator.py", "weight_calculator")

# Extract classes
DataLoader = data_loader_mod.DataLoader
LLMProductAnalyzer = product_analyzer_mod.LLMProductAnalyzer
LLMReviewAnalyzer = review_analyzer_mod.LLMReviewAnalyzer
StatisticalReviewAnalyzer = stat_analyzer_mod.StatisticalReviewAnalyzer
ReviewAggregator = aggregator_mod.ReviewAggregator
ReviewWeightCalculator = weight_calc_mod.ReviewWeightCalculator
PriceAnalyzer = price_analyzer_mod.PriceAnalyzer


class AntiPiracyPipeline:
    """Main pipeline orchestrator"""
    
    def __init__(self, data_dir: str = "dataset_bruto", output_dir: str = "output"):
        self.data_dir = data_dir
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Initialize all analyzers
        print("🚀 Initializing Anti-Piracy Detection Pipeline...\n")
        
        self.data_loader = DataLoader(data_dir)
        self.product_llm = LLMProductAnalyzer()
        self.review_llm = LLMReviewAnalyzer()
        self.stat_analyzer = StatisticalReviewAnalyzer()
        self.review_aggregator = ReviewAggregator()
        self.weight_calculator = ReviewWeightCalculator()
        self.price_analyzer = PriceAnalyzer()
        
        print("✅ All analyzers initialized\n")
    
    def run_full_pipeline(self, limit: Optional[int] = None) -> List[Dict]:
        """
        Run complete pipeline on all products
        
        Args:
            limit: Optional limit for testing (process first N products only)
            
        Returns:
            List of enriched product objects with all analyses
        """
        print("="*70)
        print("STAGE 1: DATA LOADING")
        print("="*70)
        
        # Load datasets
        main_data, reviews_data, sellers_data = self.data_loader.load_all()
        produtos = main_data['produtos']
        
        if limit:
            produtos = produtos[:limit]
            print(f"\n⚠️  TESTING MODE: Processing first {limit} products only\n")
        
        # Process each product
        enriched_products = []
        
        print("\n" + "="*70)
        print("STAGE 2: PRODUCT ANALYSIS")
        print("="*70)
        
        for idx, product in enumerate(tqdm(produtos, desc="Analyzing products")):
            try:
                enriched = self._process_single_product(
                    product,
                    self.data_loader.review_index,
                    self.data_loader.seller_index
                )
                enriched_products.append(enriched)
                
                # Rate limiting (if needed)
                # time.sleep(0.1)
                
            except Exception as e:
                print(f"\n⚠️  Error processing product {product['id']}: {str(e)}")
                continue
        
        print(f"\n✅ Successfully processed {len(enriched_products)} products")
        
        # Save results
        self._save_results(enriched_products)
        
        return enriched_products
    
    def _process_single_product(
        self,
        product: Dict,
        review_index: Dict,
        seller_index: Dict
    ) -> Dict:
        """
        Process a single product through complete pipeline
        
        Returns:
            Enriched product with all analyses
        """
        product_id = product['id']
        
        # Get related data
        review_entry = review_index.get(product_id, {})
        
        seller_id_str = product.get('seller_id', '')
        seller = None
        if seller_id_str and seller_id_str != "":
            try:
                seller_id_int = int(seller_id_str)
                seller = seller_index.get(seller_id_int)
            except ValueError:
                pass
        
        # ============ LLM ANALYSIS 1: Product Structure ============
        llm_product_structure = self.product_llm.analyze_product_structure(product)
        
        # ============ STATISTICAL REVIEW ANALYSIS ============
        stat_features = self.stat_analyzer.analyze(product)
        
        # ============ LLM ANALYSIS 2: Review Text ============
        llm_review_features = None
        individual_review_analyses = []
        
        if review_entry.get('total_reviews_extracted', 0) > 0:
            reviews = review_entry['reviews']
            
            # Calculate expected page yield for this product
            expected_pages = self._get_expected_pages(llm_product_structure)
            
            # Analyze each review with LLM
            product_context = {
                'titulo': product.get('titulo', ''),
                'preco': product.get('preco', ''),
                'vendedor': product.get('vendedor', ''),
                'model': llm_product_structure.model_primary,
                'is_xl': llm_product_structure.is_xl,
                'expected_pages': expected_pages
            }
            
            individual_review_analyses = self.review_llm.analyze_all_reviews_for_product(
                reviews, product_context
            )
            
            # Aggregate to product level
            llm_review_features = self.review_aggregator.aggregate(
                individual_review_analyses
            )
        
        # ============ REVIEW WEIGHT CALCULATION ============
        review_weight = self.weight_calculator.calculate(
            stat_features, llm_review_features
        )
        
        # ============ PRICE ANALYSIS ============
        price_analysis = self.price_analyzer.analyze(
            product, llm_product_structure
        )
        
        # ============ SELLER ANALYSIS ============
        seller_info = self._extract_seller_info(seller, seller_id_str)
        
        # ============ COMPILE RESULTS ============
        enriched = {
            # Core identifiers
            'product_id': product_id,
            'titulo': product.get('titulo', ''),
            'link': product.get('link', ''),
            
            # Product structure (from LLM)
            'product_structure': {
                'is_bundle': llm_product_structure.is_bundle,
                'bundle_quantity': llm_product_structure.bundle_quantity,
                'item_breakdown': llm_product_structure.item_breakdown,
                'model': llm_product_structure.model_primary,
                'is_xl': llm_product_structure.is_xl,
                'colors': llm_product_structure.colors_in_bundle,
                'llm_confidence': llm_product_structure.confidence
            },
            
            # Price analysis
            'price_analysis': {
                'listed_price': price_analysis.listed_price,
                'price_per_unit': price_analysis.price_per_unit,
                'suggested_retail': price_analysis.suggested_retail,
                'deviation_pct': price_analysis.deviation_pct,
                'price_risk_level': price_analysis.price_risk_level,
                'is_suspicious_price': price_analysis.is_suspicious_price,
                'notes': price_analysis.notes
            },
            
            # Statistical review features
            'review_statistics': {
                'has_reviews': stat_features.has_reviews,
                'total_reviews': stat_features.total_reviews,
                'average_rating': stat_features.average_rating,
                'distribution': stat_features.rating_distribution,
                'distribution_pct': stat_features.distribution_percentages,
                'positive_pct': stat_features.positive_pct,
                'negative_pct': stat_features.negative_pct,
                'is_bimodal': stat_features.is_bimodal,
                'bimodal_score': stat_features.bimodal_score,
                'polarization_index': stat_features.polarization_index,
                'volume_confidence': stat_features.volume_confidence,
                'distribution_health': stat_features.distribution_health,
                'statistical_trust_score': stat_features.statistical_trust_score,
                'suspicious_patterns': stat_features.suspicious_patterns
            },
            
            # LLM review analysis (if available)
            'llm_review_analysis': self._format_llm_analysis(llm_review_features) if llm_review_features else None,
            
            # Individual review analyses (for detailed inspection)
            'individual_reviews': [
                self._format_review_analysis(ra) for ra in individual_review_analyses
            ] if individual_review_analyses else [],
            
            # Final review weight
            'review_weight': {
                'final_weight': review_weight.review_weight,
                'risk_score': review_weight.review_risk_score,
                'interpretation': review_weight.interpretation,
                'confidence': review_weight.confidence,
                'statistical_component': review_weight.statistical_component,
                'llm_component': review_weight.llm_component,
                'reasoning': review_weight.reasoning
            },
            
            # Seller information
            'seller': seller_info,
            
            # Metadata
            'image_url': product.get('imagem_url', ''),
            'free_shipping': product.get('frete_gratis', False),
            'descricao': product.get('descricao', '')[:500]  # First 500 chars
        }
        
        return enriched
    
    def _get_expected_pages(self, product_structure) -> int:
        """
        Get expected page yield for product based on model and type
        
        Args:
            product_structure: ProductStructure from LLM
            
        Returns:
            Expected page count
        """
        model = product_structure.model_primary
        is_xl = product_structure.is_xl
        
        # Use primary color from bundle (or first color)
        colors = product_structure.colors_in_bundle
        primary_color = colors[0] if colors else "Preto"
        
        # Normalize color
        if "preto" in primary_color.lower() or "black" in primary_color.lower():
            color_key = "Preto"
        else:
            color_key = "Colorido"
        
        # Lookup expected pages
        page_yields = {
            ("664", False, "Preto"): 120,
            ("664", False, "Colorido"): 100,
            ("664", True, "Preto"): 480,
            ("664", True, "Colorido"): 330,
            ("667", False, "Preto"): 120,
            ("667", False, "Colorido"): 100,
            ("667", True, "Preto"): 480,
            ("667", True, "Colorido"): 330,
            ("662", False, "Preto"): 120,
            ("662", False, "Colorido"): 100,
            ("662", True, "Preto"): 360,
            ("662", True, "Colorido"): 330
        }
        
        key = (model, is_xl, color_key)
        return page_yields.get(key, 120)  # Default to regular black if unknown
    
    def _extract_seller_info(self, seller: Optional[Dict], seller_id_str: str) -> Dict:
        """Extract seller information"""
        if not seller:
            return {
                'has_seller': False,
                'seller_id': seller_id_str,
                'notes': 'Seller data not available'
            }
        
        return {
            'has_seller': True,
            'seller_id': seller['id'],
            'nickname': seller.get('nickname', ''),
            'location': {
                'city': seller.get('address', {}).get('city', ''),
                'state': seller.get('address', {}).get('state', '')
            },
            'user_type': seller.get('user_type', ''),
            'reputation': {
                'level_id': seller.get('seller_reputation', {}).get('level_id'),
                'power_seller_status': seller.get('seller_reputation', {}).get('power_seller_status'),
                'total_transactions': seller.get('seller_reputation', {}).get('transactions', {}).get('total', 0)
            }
        }
    
    def _format_llm_analysis(self, llm_features) -> Dict:
        """Format LLM features for output"""
        return {
            'total_analyzed': llm_features.total_reviews_analyzed,
            'sentiment': {
                'average_score': llm_features.average_sentiment_score,
                'distribution': llm_features.sentiment_distribution,
                'distribution_pct': llm_features.sentiment_distribution_pct
            },
            'authenticity': {
                'counterfeit_signals': llm_features.counterfeit_signal_count,
                'authentic_signals': llm_features.authentic_signal_count,
                'authenticity_ratio': llm_features.authenticity_ratio
            },
            'complaints': {
                'frequency': llm_features.complaint_frequency,
                'top_3': llm_features.top_complaints
            },
            'keywords': {
                'counterfeit': llm_features.counterfeit_keywords_found,
                'authentic': llm_features.authentic_keywords_found
            },
            'issue_mentions': {
                'short_duration_pct': llm_features.pct_mention_short_duration,
                'printer_rejection_pct': llm_features.pct_mention_printer_rejection,
                'empty_cartridge_pct': llm_features.pct_mention_empty,
                'fake_claim_pct': llm_features.pct_mention_fake_claim,
                'authentic_claim_pct': llm_features.pct_mention_authentic_claim
            },
            'severity': {
                'critical_count': llm_features.critical_reviews,
                'high_count': llm_features.high_severity_reviews,
                'suspicious_count': llm_features.suspicious_review_count,
                'suspicious_pct': llm_features.suspicious_review_pct
            },
            'llm_risk_score': llm_features.llm_review_risk_score,
            'average_confidence': llm_features.average_confidence
        }
    
    def _format_review_analysis(self, review_analysis) -> Dict:
        """Format individual review analysis for output"""
        return {
            'review_number': review_analysis.review_number,
            'rating': review_analysis.original_rating,
            'text': review_analysis.original_text,
            'sentiment': review_analysis.sentiment,
            'sentiment_score': review_analysis.sentiment_score,
            'authenticity_signal': review_analysis.authenticity_signal,
            'counterfeit_keywords': review_analysis.counterfeit_keywords,
            'authentic_keywords': review_analysis.authentic_keywords,
            'is_suspicious': review_analysis.is_suspicious_review,
            'severity': review_analysis.severity
        }
    
    def _save_results(self, enriched_products: List[Dict]):
        """Save results to JSON file"""
        output_file = self.output_dir / "enriched_products_analysis.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(enriched_products, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Results saved to: {output_file}")
        
        # Also save a summary
        self._save_summary(enriched_products)
    
    def _save_summary(self, enriched_products: List[Dict]):
        """Save analysis summary"""
        summary = {
            'total_products_analyzed': len(enriched_products),
            'products_with_llm_review_analysis': sum(
                1 for p in enriched_products 
                if p['llm_review_analysis'] is not None
            ),
            'suspicious_by_price': sum(
                1 for p in enriched_products 
                if p['price_analysis']['is_suspicious_price']
            ),
            'suspicious_by_reviews': sum(
                1 for p in enriched_products
                if p['review_weight']['interpretation'] in ['SUSPICIOUS', 'HIGHLY_SUSPICIOUS']
            ),
            'bimodal_distributions': sum(
                1 for p in enriched_products
                if p['review_statistics']['is_bimodal']
            ),
            'critical_reviews_found': sum(
                p['llm_review_analysis']['severity']['critical_count']
                for p in enriched_products
                if p['llm_review_analysis'] is not None
            ),
            'avg_review_weight': sum(
                p['review_weight']['final_weight'] 
                for p in enriched_products
            ) / len(enriched_products) if enriched_products else 0,
            'avg_price_deviation_pct': sum(
                p['price_analysis']['deviation_pct']
                for p in enriched_products
                if p['price_analysis']['deviation_pct'] is not None
            ) / sum(
                1 for p in enriched_products
                if p['price_analysis']['deviation_pct'] is not None
            ) if enriched_products else 0
        }
        
        summary_file = self.output_dir / "analysis_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        print(f"📊 Summary saved to: {summary_file}")
        
        # Print summary
        print("\n" + "="*70)
        print("PIPELINE SUMMARY")
        print("="*70)
        for key, value in summary.items():
            print(f"{key}: {value}")
    
    def run_test_pipeline(self, product_id: str):
        """
        Test pipeline on a single product for validation
        
        Args:
            product_id: Product ID to test (e.g., "MLB3159055901")
        """
        print(f"🧪 Testing pipeline on product: {product_id}\n")
        
        # Load data
        main_data, reviews_data, sellers_data = self.data_loader.load_all()
        
        # Find product
        product = next(
            (p for p in main_data['produtos'] if p['id'] == product_id),
            None
        )
        
        if not product:
            print(f"❌ Product {product_id} not found")
            return
        
        # Process
        enriched = self._process_single_product(
            product,
            self.data_loader.review_index,
            self.data_loader.seller_index
        )
        
        # Pretty print results
        self._print_product_analysis(enriched)
        
        # Save single result
        test_output = self.output_dir / f"test_product_{product_id}.json"
        with open(test_output, 'w', encoding='utf-8') as f:
            json.dump(enriched, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Test result saved to: {test_output}")
    
    def _print_product_analysis(self, enriched: Dict):
        """Pretty print analysis results for a product"""
        print("\n" + "="*70)
        print(f"PRODUCT ANALYSIS: {enriched['product_id']}")
        print("="*70)
        
        print(f"\n📦 PRODUCT STRUCTURE:")
        ps = enriched['product_structure']
        print(f"  Title: {enriched['titulo'][:80]}...")
        print(f"  Bundle: {ps['is_bundle']} (Quantity: {ps['bundle_quantity']})")
        print(f"  Model: {ps['model']} {'XL' if ps['is_xl'] else 'Regular'}")
        print(f"  Colors: {', '.join(ps['colors'])}")
        print(f"  Item breakdown: {ps['item_breakdown']}")
        
        print(f"\n💰 PRICE ANALYSIS:")
        pa = enriched['price_analysis']
        print(f"  Listed: R$ {pa['listed_price']:.2f}")
        print(f"  Per Unit: R$ {pa['price_per_unit']:.2f}")
        if pa['suggested_retail']:
            print(f"  Expected: R$ {pa['suggested_retail']:.2f}")
            print(f"  Deviation: {pa['deviation_pct']:.1f}%")
        print(f"  Risk Level: {pa['price_risk_level']}")
        print(f"  Suspicious: {'🚩 YES' if pa['is_suspicious_price'] else '✓ No'}")
        
        print(f"\n⭐ REVIEW STATISTICS:")
        rs = enriched['review_statistics']
        print(f"  Total Reviews: {rs['total_reviews']}")
        print(f"  Average Rating: {rs['average_rating']:.2f}/5.0")
        print(f"  Positive: {rs['positive_pct']:.1f}%")
        print(f"  Negative: {rs['negative_pct']:.1f}%")
        print(f"  Bimodal: {rs['is_bimodal']} (score: {rs['bimodal_score']:.1f})")
        print(f"  Trust Score: {rs['statistical_trust_score']:.3f}")
        print(f"  Patterns: {', '.join(rs['suspicious_patterns'])}")
        
        if enriched['llm_review_analysis']:
            print(f"\n🤖 LLM REVIEW ANALYSIS:")
            llm = enriched['llm_review_analysis']
            print(f"  Analyzed: {llm['total_analyzed']} reviews")
            print(f"  Sentiment: {llm['sentiment']['average_score']:.2f}")
            print(f"  Counterfeit Signals: {llm['authenticity']['counterfeit_signals']}")
            print(f"  Authentic Signals: {llm['authenticity']['authentic_signals']}")
            print(f"  Authenticity Ratio: {llm['authenticity']['authenticity_ratio']:.2f}")
            
            if llm['keywords']['counterfeit']:
                print(f"  🚩 Counterfeit Keywords: {llm['keywords']['counterfeit']}")
            if llm['keywords']['authentic']:
                print(f"  ✓ Authentic Keywords: {llm['keywords']['authentic']}")
            
            if llm['complaints']['top_3']:
                print(f"  Top Complaints: {llm['complaints']['top_3']}")
            
            print(f"  LLM Risk Score: {llm['llm_risk_score']:.3f}")
        
        print(f"\n🎯 FINAL REVIEW WEIGHT:")
        rw = enriched['review_weight']
        print(f"  Weight: {rw['final_weight']:.3f}")
        print(f"  Risk: {rw['risk_score']:.3f}")
        print(f"  Interpretation: {rw['interpretation']}")
        print(f"  Confidence: {rw['confidence']}")
        print(f"  Reasoning: {rw['reasoning']}")
        
        print(f"\n👤 SELLER:")
        seller = enriched['seller']
        if seller['has_seller']:
            print(f"  Name: {seller['nickname']}")
            print(f"  Location: {seller['location']['city']}, {seller['location']['state']}")
            print(f"  Reputation: {seller['reputation']['level_id']}")
            print(f"  Power Seller: {seller['reputation']['power_seller_status']}")
            print(f"  Transactions: {seller['reputation']['total_transactions']:,}")
        else:
            print(f"  ⚠️ Seller data not available")


# Main execution
if __name__ == "__main__":
    import sys
    
    pipeline = AntiPiracyPipeline()
    
    # Check command line arguments
    if len(sys.argv) > 1:
        # Test mode with specific product
        product_id = sys.argv[1]
        pipeline.run_test_pipeline(product_id)
    else:
        # Full pipeline
        print("Starting FULL pipeline (all 229 products)")
        print("This will make ~500+ LLM API calls")
        print("Estimated time: 5-10 minutes")
        print("Estimated cost: $0.50-1.00")
        
        confirm = input("\nProceed? (yes/no): ")
        
        if confirm.lower() in ['yes', 'y']:
            enriched = pipeline.run_full_pipeline()
            print("\n✅ Pipeline complete!")
        else:
            print("❌ Cancelled")

