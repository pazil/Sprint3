#!/usr/bin/env python3
"""
Script to find and display products with LLM review analysis
"""
import json
import sys

def find_llm_analyzed_products(input_file="output/enriched_products_incremental.jsonl"):
    """Find all products where LLM analyzed reviews"""
    
    products_with_llm = []
    products_without_llm = []
    
    with open(input_file, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            try:
                product = json.loads(line.strip())
                
                # Check if llm_review_analysis exists and is not null
                if product.get('llm_review_analysis') is not None:
                    products_with_llm.append({
                        'line': line_num,
                        'product_id': product.get('product_id'),
                        'titulo': product.get('titulo', '')[:80],  # First 80 chars
                        'total_reviews': product.get('review_statistics', {}).get('total_reviews', 0),
                        'llm_analyzed': product.get('llm_review_analysis', {}).get('total_analyzed', 0),
                        'sentiment_avg': product.get('llm_review_analysis', {}).get('sentiment', {}).get('average_score', 0),
                        'llm_risk_score': product.get('llm_review_analysis', {}).get('llm_risk_score', 0),
                    })
                else:
                    products_without_llm.append(product.get('product_id'))
                    
            except json.JSONDecodeError as e:
                print(f"Error parsing line {line_num}: {e}", file=sys.stderr)
                continue
    
    # Display results
    print("=" * 100)
    print(f"PRODUCTS WITH LLM REVIEW ANALYSIS: {len(products_with_llm)}")
    print("=" * 100)
    print()
    
    if products_with_llm:
        print(f"{'Line':<6} {'Product ID':<18} {'Reviews':<10} {'Analyzed':<10} {'Sentiment':<10} {'Risk':<8} Title")
        print("-" * 100)
        
        for p in products_with_llm:
            print(f"{p['line']:<6} {p['product_id']:<18} {p['total_reviews']:<10} {p['llm_analyzed']:<10} "
                  f"{p['sentiment_avg']:<10.2f} {p['llm_risk_score']:<8.3f} {p['titulo'][:50]}")
        
        print()
        print("=" * 100)
        print(f"Total: {len(products_with_llm)} products with LLM analysis")
        print(f"Total: {len(products_without_llm)} products WITHOUT LLM analysis")
        print("=" * 100)
        print()
        print("To view a specific product's LLM analysis, use:")
        print("  sed -n '<line_number>p' output/enriched_products_incremental.jsonl | python -m json.tool")
        
    else:
        print("No products with LLM analysis found.")
    
    return products_with_llm

if __name__ == "__main__":
    input_file = sys.argv[1] if len(sys.argv) > 1 else "output/enriched_products_incremental.jsonl"
    find_llm_analyzed_products(input_file)

