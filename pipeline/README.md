# Anti-Piracy Detection Pipeline

## Overview

This pipeline analyzes HP printer cartridge listings on Mercado Livre to detect potential counterfeit products using a combination of:
- **LLM semantic analysis** (product structure, review text)
- **Statistical analysis** (rating distributions, patterns)
- **Price deviation analysis** (vs HP suggested retail)
- **Seller reputation analysis**

## Pipeline Architecture

```
01_data_loader.py           → Load and index 3 JSON datasets
02_llm_product_analyzer.py  → Extract bundle info, model, colors via LLM
03_llm_review_analyzer.py   → Analyze each review text via LLM
04_statistical_review_analyzer.py → Statistical rating distribution analysis
05_price_analyzer.py         → Calculate price deviations
06_review_aggregator.py      → Aggregate review-level LLM to product-level
07_review_weight_calculator.py → Combine stats + LLM into final weight
00_main_pipeline.py          → Orchestrate full pipeline
```

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create `.env` file with your OpenAI API key:
```
OPENAI_API_KEY=your_key_here
```

3. Ensure data files are in `dataset_bruto/` directory:
- `664_dataset_javascript_sem_reviews_20250930_012112.json`
- `664_reviews.json`
- `664_vendedores.json`

## Usage

### Test on Single Product
```bash
python pipeline/00_main_pipeline.py MLB3159055901
```

### Run Full Pipeline
```bash
python pipeline/00_main_pipeline.py
```

This will:
- Process all 229 products
- Make ~500-700 LLM API calls
- Take 5-10 minutes
- Cost ~$0.50-1.00
- Save results to `output/enriched_products_analysis.json`

## Output Structure

Each product in output has:
```json
{
  "product_id": "MLB3159055901",
  "titulo": "...",
  
  "product_structure": {
    "is_bundle": true,
    "bundle_quantity": 2,
    "item_breakdown": [...],
    "model": "664XL",
    "is_xl": true
  },
  
  "price_analysis": {
    "listed_price": 209.99,
    "price_per_unit": 104.99,
    "deviation_pct": -39.2,
    "price_risk_level": "MEDIUM"
  },
  
  "review_statistics": {
    "average_rating": 4.7,
    "total_reviews": 43,
    "bimodal_score": 12.5,
    "statistical_trust_score": 0.78
  },
  
  "llm_review_analysis": {
    "sentiment": {...},
    "authenticity": {...},
    "counterfeit_signals": 1,
    "authentic_signals": 2
  },
  
  "review_weight": {
    "final_weight": 0.73,
    "risk_score": 0.27,
    "interpretation": "TRUSTWORTHY",
    "confidence": "MEDIUM"
  }
}
```

## Key Features

### LLM-Powered Extraction
- **No regex fragility** - Semantic understanding handles variations
- **Bundle detection** - Handles complex bundles ("2 Preto + 1 Color")
- **Contextual keywords** - Distinguishes "original bom" vs "diz ser original mas..."
- **Granular analysis** - Each review analyzed individually for precision

### Statistical Rigor
- **Bimodal detection** - Flags mixed authentic/fake batches
- **Polarization index** - Measures rating variance
- **Volume confidence** - Adjusts for sample size
- **Pattern recognition** - Multiple suspicious pattern flags

### Price Intelligence
- **Bundle-aware** - Calculates per-unit pricing
- **Model-specific** - Different expected prices for 664 vs 664XL
- **Color-specific** - Black vs color have different prices
- **Risk categorization** - CRITICAL, HIGH, MEDIUM, LOW, NORMAL

## Modules

### 01_data_loader.py
- Loads 3 JSON files
- Creates fast lookup indexes
- Validates data integrity
- Handles edge cases (empty seller_id)

### 02_llm_product_analyzer.py
- Extracts bundle quantity from title/description
- Identifies model numbers (664, 664XL, 667, etc.)
- Detects color distribution in bundles
- Returns structured JSON with high confidence

### 03_llm_review_analyzer.py
- Analyzes each review individually
- Extracts sentiment (-1 to 1)
- Detects counterfeit vs authentic signals
- Categorizes complaints
- Flags specific issues (printer rejection, empty cartridge, etc.)

### 04_statistical_review_analyzer.py
- Analyzes rating distributions
- Calculates bimodal scores
- Detects suspicious patterns
- Works on ALL products (including those without text)

### 05_price_analyzer.py
- Matches products to HP price table
- Handles bundles with multiple SKUs
- Calculates deviations
- Risk categorization

### 06_review_aggregator.py
- Combines individual review LLM analyses
- Aggregates to product-level metrics
- Counts complaint types
- Calculates product-level risk from reviews

### 07_review_weight_calculator.py
- Combines statistical + LLM features
- Dynamic weighting based on data availability
- Handles products with/without LLM analysis
- Produces final 0-1 trustworthiness score

## Next Steps After Running Pipeline

1. **Inspect `enriched_products_analysis.json`**
   - Review products flagged as suspicious
   - Validate LLM extractions make sense

2. **Build ML Training Dataset**
   - Extract features from enriched products
   - Create labels (semi-supervised)
   - Export to CSV for model training

3. **Seller-Level Aggregation**
   - Group products by seller
   - Calculate seller risk scores
   - Identify systematic offenders

4. **Manual Validation**
   - Review top 20 high-risk products
   - Confirm counterfeit indicators
   - Refine thresholds

## Cost Optimization

- Using gpt-4o-mini (cheap, fast)
- Processing all 229 products + 494 reviews ≈ $0.50-1.00
- Can limit to high-priority products first
- Results cached in output files

