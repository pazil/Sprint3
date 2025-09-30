"""
Restart Pipeline with Maximum Optimization
- Aggressive memory management
- Faster checkpointing (every 5 products)
- Silent mode to reduce console buffer accumulation
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
print("🚀 OPTIMIZED PIPELINE - Maximum Performance")
print("="*70)
print("\n⚡ Optimizations:")
print("   ✓ Checkpoint every 5 products (faster memory clearing)")
print("   ✓ Aggressive garbage collection")
print("   ✓ LLM client recreation at each checkpoint")
print("   ✓ Silent mode (reduced console output)")
print("   ✓ Auto-resume capability")

# Initialize pipeline
pipeline = AntiPiracyPipeline()

# Check if there's existing progress
jsonl_file = Path("output/enriched_products_incremental.jsonl")
resume = False

if jsonl_file.exists():
    # Count existing products
    with open(jsonl_file, 'r', encoding='utf-8') as f:
        existing_count = sum(1 for line in f if line.strip())
    
    print(f"\n📊 Existing progress: {existing_count}/229 products")
    print(f"⏳ Remaining: {229 - existing_count} products")
    
    resume_input = input(f"\n▶️  Resume from checkpoint? (yes/no, default: yes): ").strip().lower()
    resume = resume_input in ['yes', 'y', '']
    
    if not resume:
        print("🗑️  Starting fresh (will delete existing progress)")
        confirm = input("   Confirm deletion? (yes/no): ").strip().lower()
        if confirm not in ['yes', 'y']:
            print("❌ Cancelled")
            sys.exit(0)
else:
    print(f"\n🆕 Starting fresh pipeline run")

print(f"\n{'🔄 Resuming' if resume else '🚀 Starting'} pipeline with optimized settings...")
print("="*70)
print()

try:
    # Run with aggressive optimization
    enriched = pipeline.run_full_pipeline(
        checkpoint_every=5,  # Save every 5 products for faster memory clearing
        resume=resume
    )
    print("\n✅ Pipeline complete!")
    print(f"📊 Processed {len(enriched)} products")
    
except KeyboardInterrupt:
    print("\n\n⏸️  Pipeline interrupted by user")
    print("💡 Your progress has been saved!")
    print("   Run this script again to resume from the last checkpoint")
    
except Exception as e:
    print(f"\n\n❌ Pipeline error: {e}")
    print("💡 Your progress has been saved!")
    print("   Run this script again to resume from the last checkpoint")
    raise

