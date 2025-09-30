"""
Quick script to check pipeline progress
"""

from pathlib import Path
import json

jsonl_file = Path("output/enriched_products_incremental.jsonl")

print("="*70)
print("📊 PIPELINE PROGRESS CHECK")
print("="*70)

if jsonl_file.exists():
    # Count products
    with open(jsonl_file, 'r', encoding='utf-8') as f:
        lines = [line for line in f if line.strip()]
    
    completed = len(lines)
    total = 229
    remaining = total - completed
    progress_pct = (completed / total) * 100
    
    print(f"\n✅ Completed: {completed}/{total} products ({progress_pct:.1f}%)")
    print(f"⏳ Remaining: {remaining} products")
    
    # Show last few processed products
    if lines:
        print(f"\n📋 Last 3 processed products:")
        for i, line in enumerate(lines[-3:], 1):
            product = json.loads(line)
            print(f"   {i}. {product['product_id']} - {product['titulo'][:50]}...")
    
    print(f"\n💡 To continue: python resume_pipeline.py")
    
else:
    print("\n❌ No progress file found")
    print("💡 Start pipeline: python pipeline/00_main_pipeline.py")

print("="*70)

