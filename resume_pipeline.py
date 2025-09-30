"""
Resume Pipeline - Continue from last checkpoint
Use this if the pipeline was interrupted
"""

import sys
sys.path.insert(0, 'pipeline')

from pathlib import Path

# Import pipeline
import importlib.util
spec = importlib.util.spec_from_file_location("main_pipeline", "pipeline/00_main_pipeline.py")
pipeline_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pipeline_module)

AntiPiracyPipeline = pipeline_module.AntiPiracyPipeline

print("="*70)
print("🔄 RESUME PIPELINE - Continue from Last Checkpoint")
print("="*70)

# Initialize pipeline
pipeline = AntiPiracyPipeline()

# Check if there's existing progress
jsonl_file = Path("output/enriched_products_incremental.jsonl")
if jsonl_file.exists():
    # Count existing products
    with open(jsonl_file, 'r', encoding='utf-8') as f:
        existing_count = sum(1 for line in f if line.strip())
    
    print(f"\n✓ Found existing progress: {existing_count} products already processed")
    print(f"📊 Total products: 229")
    print(f"⏳ Remaining: {229 - existing_count} products")
    print(f"\n💡 The pipeline will:")
    print(f"   1. Load {existing_count} existing results")
    print(f"   2. Skip those products")
    print(f"   3. Process remaining {229 - existing_count} products")
    print(f"   4. Combine all results at the end")
    
    confirm = input(f"\n▶️  Resume processing? (yes/no): ")
    
    if confirm.lower() in ['yes', 'y']:
        print("\n🚀 Resuming pipeline...\n")
        enriched = pipeline.run_full_pipeline(resume=True, checkpoint_every=10)
        print("\n✅ Pipeline complete!")
    else:
        print("❌ Cancelled")
else:
    print("\n❌ No existing progress found!")
    print("💡 Run 'python pipeline/00_main_pipeline.py' to start fresh")

