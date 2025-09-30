#!/usr/bin/env python3
"""
Extract only products with LLM review analysis to a separate file
Outputs both pretty JSON (readable) and JSONL (one per line) formats
"""
import json
import sys
import os

def extract_llm_analyzed_products(
    input_file="output/enriched_products_incremental.jsonl",
    output_format="both"  # "json", "jsonl", or "both"
):
    """
    Extract products with LLM analysis to new file(s)
    
    Args:
        input_file: Source JSONL file
        output_format: "json" (pretty array), "jsonl" (line-by-line), or "both"
    """
    
    products_with_llm = []
    
    # Read and collect products with LLM analysis
    print(f"📖 Reading from: {input_file}")
    with open(input_file, 'r', encoding='utf-8') as infile:
        for line_num, line in enumerate(infile, 1):
            try:
                product = json.loads(line.strip())
                
                # Check if llm_review_analysis exists and is not null
                if product.get('llm_review_analysis') is not None:
                    products_with_llm.append(product)
                    
            except json.JSONDecodeError as e:
                print(f"⚠️  Error parsing line {line_num}: {e}", file=sys.stderr)
                continue
    
    print(f"✓ Found {len(products_with_llm)} products with LLM analysis\n")
    
    # Output files
    base_name = "output/llm_analyzed_products"
    
    # Write JSONL format (one product per line, compact)
    if output_format in ["jsonl", "both"]:
        jsonl_file = f"{base_name}.jsonl"
        with open(jsonl_file, 'w', encoding='utf-8') as outfile:
            for product in products_with_llm:
                json.dump(product, outfile, ensure_ascii=False)
                outfile.write('\n')
        print(f"✓ JSONL (compact): {jsonl_file}")
        print(f"  Format: One product per line (for processing)")
    
    # Write pretty JSON format (readable array with indentation)
    if output_format in ["json", "both"]:
        json_file = f"{base_name}_pretty.json"
        with open(json_file, 'w', encoding='utf-8') as outfile:
            json.dump(products_with_llm, outfile, ensure_ascii=False, indent=2)
        
        # Get file size
        size_mb = os.path.getsize(json_file) / (1024 * 1024)
        print(f"✓ JSON (pretty): {json_file}")
        print(f"  Format: Single array with full indentation (for reading)")
        print(f"  Size: {size_mb:.2f} MB")
    
    print(f"\n📊 Summary:")
    print(f"   Total products extracted: {len(products_with_llm)}")
    print(f"   Products with reviews analyzed by LLM")
    
    return len(products_with_llm)

def main():
    """Main entry point with argument parsing"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Extract products with LLM-analyzed reviews',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Extract both formats (default)
  python extract_llm_analyzed.py
  
  # Extract only pretty JSON (best for reading)
  python extract_llm_analyzed.py --format json
  
  # Extract only JSONL (best for processing)
  python extract_llm_analyzed.py --format jsonl
  
  # Custom input file
  python extract_llm_analyzed.py input.jsonl --format both
        """
    )
    
    parser.add_argument(
        'input_file',
        nargs='?',
        default='output/enriched_products_incremental.jsonl',
        help='Input JSONL file (default: output/enriched_products_incremental.jsonl)'
    )
    
    parser.add_argument(
        '--format',
        choices=['json', 'jsonl', 'both'],
        default='both',
        help='Output format: json (pretty), jsonl (compact), or both (default: both)'
    )
    
    args = parser.parse_args()
    
    extract_llm_analyzed_products(args.input_file, args.format)

if __name__ == "__main__":
    if len(sys.argv) == 1:
        # No arguments - use defaults
        extract_llm_analyzed_products()
    else:
        # Parse arguments
        main()
