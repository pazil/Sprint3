"""
Data Loader Module
Loads and indexes all three JSON datasets with validation
"""

import json
from pathlib import Path
from typing import Dict, List, Tuple
from dataclasses import dataclass


@dataclass
class DatasetStats:
    """Statistics about loaded datasets"""
    total_products: int
    total_reviews_entries: int
    total_sellers: int
    products_with_extracted_reviews: int
    total_individual_reviews: int
    orphan_products: List[str]  # Products without seller_id
    

class DataLoader:
    """Load and validate all three datasets"""
    
    def __init__(self, data_dir: str = "dataset_bruto"):
        self.data_dir = Path(data_dir)
        
        # Will be populated by load_all()
        self.main_data = None
        self.reviews_data = None
        self.sellers_data = None
        
        # Indexes for fast lookup
        self.review_index: Dict = {}
        self.seller_index: Dict = {}
        self.products_by_seller: Dict[int, List] = {}
        
        # Stats
        self.stats: DatasetStats = None
    
    def load_all(self) -> Tuple[Dict, List, Dict]:
        """
        Load all three JSON files and create indexes
        
        Returns:
            (main_data, reviews_data, sellers_data)
        """
        print("Loading datasets...")
        
        # Load main product dataset
        main_file = list(self.data_dir.glob("664_dataset_javascript_*.json"))[0]
        with open(main_file, 'r', encoding='utf-8') as f:
            self.main_data = json.load(f)
        print(f"✓ Loaded {len(self.main_data['produtos'])} products from main dataset")
        
        # Load reviews dataset
        reviews_file = self.data_dir / "664_reviews.json"
        with open(reviews_file, 'r', encoding='utf-8') as f:
            self.reviews_data = json.load(f)
        print(f"✓ Loaded {len(self.reviews_data)} review entries")
        
        # Load sellers dataset
        sellers_file = self.data_dir / "664_vendedores.json"
        with open(sellers_file, 'r', encoding='utf-8') as f:
            self.sellers_data = json.load(f)
        print(f"✓ Loaded {len(self.sellers_data['dados_vendedores'])} sellers")
        
        # Create indexes
        self._create_indexes()
        
        # Validate
        self._validate_integrity()
        
        return self.main_data, self.reviews_data, self.sellers_data
    
    def _create_indexes(self):
        """Create fast lookup indexes"""
        print("\nCreating indexes...")
        
        # Index reviews by product_id (O(1) lookup)
        self.review_index = {
            entry['product_id']: entry 
            for entry in self.reviews_data
        }
        print(f"✓ Indexed {len(self.review_index)} review entries")
        
        # Index sellers by id (O(1) lookup)
        # Note: seller.id is INTEGER, we index by int
        self.seller_index = {
            seller['id']: seller 
            for seller in self.sellers_data['dados_vendedores']
        }
        print(f"✓ Indexed {len(self.seller_index)} sellers")
        
        # Index products by seller (one-to-many)
        from collections import defaultdict
        self.products_by_seller = defaultdict(list)
        
        for product in self.main_data['produtos']:
            seller_id_str = product.get('seller_id', '')
            if seller_id_str and seller_id_str != "":
                try:
                    seller_id_int = int(seller_id_str)
                    self.products_by_seller[seller_id_int].append(product)
                except ValueError:
                    pass
        
        print(f"✓ Mapped products to {len(self.products_by_seller)} sellers")
    
    def _validate_integrity(self):
        """Validate data integrity and relationships"""
        print("\nValidating data integrity...")
        
        produtos = self.main_data['produtos']
        
        # Check 1: Product-Review ID match
        product_ids = set(p['id'] for p in produtos)
        review_ids = set(r['product_id'] for r in self.reviews_data)
        
        if product_ids == review_ids:
            print("✓ Perfect 1:1 match between products and reviews")
        else:
            missing = product_ids - review_ids
            extra = review_ids - product_ids
            if missing:
                print(f"⚠️  Products missing from reviews: {missing}")
            if extra:
                print(f"⚠️  Orphan reviews: {extra}")
        
        # Check 2: Seller ID references
        orphan_products = []
        missing_sellers = set()
        
        for product in produtos:
            seller_id_str = product.get('seller_id', '')
            
            if not seller_id_str or seller_id_str == "":
                orphan_products.append(product['id'])
                continue
            
            try:
                seller_id_int = int(seller_id_str)
                if seller_id_int not in self.seller_index:
                    missing_sellers.add(seller_id_int)
            except ValueError:
                orphan_products.append(product['id'])
        
        if orphan_products:
            print(f"⚠️  {len(orphan_products)} products without valid seller_id: {orphan_products}")
        
        if missing_sellers:
            print(f"⚠️  {len(missing_sellers)} seller IDs not found in sellers dataset")
        else:
            print("✓ All seller IDs valid (excluding orphans)")
        
        # Calculate stats
        products_with_text = sum(
            1 for entry in self.reviews_data 
            if entry['total_reviews_extracted'] > 0
        )
        
        total_reviews = sum(
            len(entry['reviews']) 
            for entry in self.reviews_data
        )
        
        self.stats = DatasetStats(
            total_products=len(produtos),
            total_reviews_entries=len(self.reviews_data),
            total_sellers=len(self.seller_index),
            products_with_extracted_reviews=products_with_text,
            total_individual_reviews=total_reviews,
            orphan_products=orphan_products
        )
        
        print(f"\n📊 Dataset Statistics:")
        print(f"   Products: {self.stats.total_products}")
        print(f"   Products with review text: {self.stats.products_with_extracted_reviews} ({self.stats.products_with_extracted_reviews/self.stats.total_products*100:.1f}%)")
        print(f"   Total individual reviews: {self.stats.total_individual_reviews}")
        print(f"   Unique sellers: {self.stats.total_sellers}")
        print(f"   Orphan products: {len(self.stats.orphan_products)}")
    
    def get_product_with_relations(self, product_id: str) -> Dict:
        """
        Get a product with all its related data joined
        
        Args:
            product_id: Product ID (e.g., "MLB3159055901")
            
        Returns:
            Unified product object with reviews and seller info
        """
        # Find product
        product = next(
            (p for p in self.main_data['produtos'] if p['id'] == product_id), 
            None
        )
        
        if not product:
            return None
        
        # Get reviews
        reviews_entry = self.review_index.get(product_id, {})
        
        # Get seller
        seller = None
        seller_id_str = product.get('seller_id', '')
        if seller_id_str and seller_id_str != "":
            try:
                seller_id_int = int(seller_id_str)
                seller = self.seller_index.get(seller_id_int)
            except ValueError:
                pass
        
        return {
            'product': product,
            'reviews_entry': reviews_entry,
            'seller': seller,
            'has_seller': seller is not None,
            'has_reviews': reviews_entry.get('total_reviews_extracted', 0) > 0
        }


# Usage example
if __name__ == "__main__":
    loader = DataLoader()
    main_data, reviews_data, sellers_data = loader.load_all()
    
    print("\n✅ Data loaded successfully!")
    print(f"\nAccess data via:")
    print(f"  loader.main_data['produtos']")
    print(f"  loader.review_index[product_id]")
    print(f"  loader.seller_index[seller_id_int]")
    print(f"  loader.products_by_seller[seller_id_int]")

