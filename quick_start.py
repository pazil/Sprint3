#!/usr/bin/env python3
"""
Quick Start Script for Anti-Piracy Pipeline
Run this to test the pipeline on a single product
"""

import sys
from pathlib import Path
import importlib.util

# Load the main pipeline module directly
pipeline_file = Path(__file__).parent / "pipeline" / "00_main_pipeline.py"

spec = importlib.util.spec_from_file_location("main_pipeline", pipeline_file)
main_pipeline_module = importlib.util.module_from_spec(spec)
sys.modules['main_pipeline'] = main_pipeline_module
spec.loader.exec_module(main_pipeline_module)

AntiPiracyPipeline = main_pipeline_module.AntiPiracyPipeline


def main():
    """Quick test on a product with reviews"""
    
    print("🚀 HP Anti-Piracy Detection Pipeline - Quick Start\n")
    
    # Test product with reviews (from schema analysis)
    test_product_id = "MLB3159055901"
    
    print(f"Testing pipeline on product: {test_product_id}")
    print("This product has:")
    print("  - 43 total reviews")
    print("  - 3 extracted review texts")
    print("  - 4.7 average rating")
    print("  - Is a bundle (2 cartridges)")
    print("\nExpected LLM calls:")
    print("  - 1 call for product structure analysis")
    print("  - 3 calls for review analysis (one per review)")
    print("  Total: 4 API calls (~$0.01)")
    print("\n" + "="*70)
    
    # Run pipeline
    pipeline = AntiPiracyPipeline()
    pipeline.run_test_pipeline(test_product_id)
    
    print("\n✅ Test complete! Check output/test_product_*.json for results")
    print("\nNext steps:")
    print("  1. Review the output to validate LLM extractions")
    print("  2. Adjust prompts if needed")
    print("  3. Run full pipeline: python pipeline/00_main_pipeline.py")


if __name__ == "__main__":
    main()

