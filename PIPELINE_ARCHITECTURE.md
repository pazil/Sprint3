# Anti-Piracy Detection Pipeline Architecture

## Project Goal
Identify counterfeit HP cartridge sellers on Mercado Livre using ML/DL with multi-signal analysis combining pricing, reviews, seller patterns, and LLM-powered sentiment analysis.

---

## 🏗️ Pipeline Stages Overview

```
┌──────────────────────────────────────────────────────────────────────────┐
│                    STAGE 1: DATA INTEGRATION                             │
│  Load → Index → Join → Enrich → Validate                                │
└────────────────────┬─────────────────────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                    STAGE 2: FEATURE EXTRACTION                           │
│  Price Analysis │ Review Analysis │ Seller Profiling │ Product Features │
└────────────────────┬─────────────────────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                    STAGE 3: LLM ENRICHMENT                               │
│  Sentiment Analysis │ Keyword Extraction │ Authenticity Signals         │
└────────────────────┬─────────────────────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                    STAGE 4: FEATURE ENGINEERING                          │
│  Review Weights │ Risk Scores │ Aggregated Metrics                      │
└────────────────────┬─────────────────────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                    STAGE 5: ML MODEL TRAINING                            │
│  Training Dataset │ Model Selection │ Evaluation                         │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## STAGE 1: Data Integration & Enrichment

### 1.1 Load and Index

```javascript
class DataIntegrator {
  async loadAllData() {
    // Load files
    const mainData = await loadJSON('664_dataset_javascript_*.json');
    const reviewsData = await loadJSON('664_reviews.json');
    const sellersData = await loadJSON('664_vendedores.json');
    const priceTable = await loadCSV('Tabela de Preços Sugeridos.xlsx');
    
    // Create fast lookup indexes
    this.reviewsIndex = new Map(
      reviewsData.map(r => [r.product_id, r])
    );
    
    this.sellersIndex = new Map(
      sellersData.dados_vendedores.map(s => [String(s.id), s])
    );
    
    this.priceIndex = new Map(
      priceTable.map(p => [p.PN || p.Família, p])
    );
    
    return mainData.produtos;
  }
}
```

### 1.2 Unified Product Object

```javascript
function createUnifiedProduct(product) {
  const reviews = reviewsIndex.get(product.id);
  const seller = sellersIndex.get(product.seller_id);
  const suggestedPrice = findSuggestedPrice(product);
  
  return {
    // Identifiers
    product_id: product.id,
    seller_id: product.seller_id,
    
    // Product Info
    title: product.titulo,
    link: product.link,
    price: parseFloat(product.preco),
    original_price: parseFloat(product.preco_original) || null,
    discount: product.desconto,
    brand: product.marca,
    model: product.modelo,
    is_xl: detectXL(product),
    is_bundle: detectBundle(product),
    bundle_quantity: extractBundleQuantity(product),
    
    // Price Analysis
    suggested_price: suggestedPrice?.['Preço Sugerido'],
    price_deviation_pct: calculateDeviation(product.preco, suggestedPrice),
    
    // Review Statistics
    rating_average: product.rating_medio,
    total_reviews: product.total_reviews,
    rating_distribution: {
      5: product.rating_5_estrelas,
      4: product.rating_4_estrelas,
      3: product.rating_3_estrelas,
      2: product.rating_2_estrelas,
      1: product.rating_1_estrela
    },
    
    // Detailed Reviews
    reviews_data: {
      extracted_count: reviews?.total_reviews_extracted || 0,
      reviews_with_text: reviews?.reviews.filter(r => r.text).length || 0,
      reviews_with_images: reviews?.reviews.filter(r => r.has_images).length || 0,
      detailed_reviews: reviews?.reviews || []
    },
    
    // Seller Info
    seller: {
      id: seller?.id,
      nickname: seller?.nickname,
      location: `${seller?.address?.city}, ${seller?.address?.state}`,
      state: seller?.address?.state,
      user_type: seller?.user_type,
      reputation_level: seller?.seller_reputation?.level_id,
      power_seller: seller?.seller_reputation?.power_seller_status,
      total_transactions: seller?.seller_reputation?.transactions?.total,
      is_authorized: checkAuthorizedSeller(seller)
    },
    
    // Shipping
    free_shipping: product.frete_gratis,
    
    // Raw data for future analysis
    raw_description: product.descricao || '',
    raw_data: product.dados_brutos
  };
}
```

---

## STAGE 2: Feature Extraction

### 2.1 Price Analysis Module

**Key Goals:**
- Detect bundle pricing
- Calculate per-unit price
- Compare against HP suggested retail
- Flag suspicious discounts

```javascript
class PriceAnalyzer {
  
  detectBundle(product) {
    const bundleKeywords = [
      /kit/i,
      /\d+\s*unid/i,
      /\d+\s*peças/i,
      /combo/i,
      /pacote/i,
      /\d+x/i
    ];
    
    const title = product.titulo.toLowerCase();
    return bundleKeywords.some(pattern => pattern.test(title));
  }
  
  extractBundleQuantity(product) {
    // Match patterns like "2x", "02 unidades", "kit 3 peças"
    const patterns = [
      /(\d+)\s*x/i,
      /(\d+)\s*unid/i,
      /(\d+)\s*peças/i,
      /kit\s*(\d+)/i
    ];
    
    for (const pattern of patterns) {
      const match = product.titulo.match(pattern);
      if (match) return parseInt(match[1]);
    }
    
    return 1; // Default to 1 if no bundle detected
  }
  
  calculateUnitPrice(product) {
    const totalPrice = parseFloat(product.preco);
    const quantity = this.extractBundleQuantity(product);
    return totalPrice / quantity;
  }
  
  calculatePriceDeviation(product, suggestedPrice) {
    const unitPrice = this.calculateUnitPrice(product);
    const suggested = parseFloat(suggestedPrice);
    
    if (!suggested) return null;
    
    const deviation = ((unitPrice - suggested) / suggested) * 100;
    
    return {
      unit_price: unitPrice,
      suggested_price: suggested,
      deviation_pct: deviation,
      is_suspicious: deviation < -30, // 30% or more below retail
      risk_level: this.categorizeRisk(deviation)
    };
  }
  
  categorizeRisk(deviation) {
    if (deviation < -70) return 'CRITICAL'; // 70%+ discount
    if (deviation < -50) return 'HIGH';      // 50-70% discount
    if (deviation < -30) return 'MEDIUM';    // 30-50% discount
    if (deviation < -10) return 'LOW';       // 10-30% discount
    return 'NORMAL';                         // Within normal range
  }
  
  matchSuggestedPrice(product, priceTable) {
    // Try to match by model number
    const model = product.modelo_alfanumerico || product.modelo;
    
    // Try direct match
    let match = priceTable.find(p => 
      p.Produto.includes(model) || 
      p.PN === product.PN
    );
    
    // Fuzzy match on title
    if (!match) {
      match = priceTable.find(p => 
        similarity(p.Produto, product.titulo) > 0.7
      );
    }
    
    return match;
  }
}
```

**Price Features Generated:**
- `unit_price`: Actual price per unit (bundle-adjusted)
- `price_deviation_pct`: % difference from suggested retail
- `is_suspicious_price`: Boolean flag for 30%+ discount
- `price_risk_level`: CRITICAL, HIGH, MEDIUM, LOW, NORMAL

---

### 2.2 Review Analysis Module (Statistical)

**Key Goals:**
- Analyze rating distribution patterns
- Detect suspicious review patterns (bimodal distribution)
- Calculate review quality metrics

```javascript
class ReviewStatisticalAnalyzer {
  
  analyzeRatingDistribution(product) {
    const dist = product.rating_distribution;
    const total = product.total_reviews;
    
    if (total === 0) return null;
    
    // Calculate percentages
    const percentages = {
      pct_5_star: (dist[5] / total) * 100,
      pct_4_star: (dist[4] / total) * 100,
      pct_3_star: (dist[3] / total) * 100,
      pct_2_star: (dist[2] / total) * 100,
      pct_1_star: (dist[1] / total) * 100
    };
    
    // Positive vs Negative ratio
    const positive = dist[5] + dist[4];
    const negative = dist[1] + dist[2];
    const neutral = dist[3];
    
    return {
      ...percentages,
      positive_count: positive,
      negative_count: negative,
      neutral_count: neutral,
      positive_pct: (positive / total) * 100,
      negative_pct: (negative / total) * 100,
      neutral_pct: (neutral / total) * 100,
      
      // Key metrics
      bimodal_score: this.calculateBimodalScore(dist),
      polarization_index: this.calculatePolarization(dist),
      trust_score: this.calculateTrustScore(product)
    };
  }
  
  calculateBimodalScore(dist) {
    // Detect if reviews are concentrated at extremes (5-star AND 1-star)
    // This is a red flag for mixed authentic/fake batches
    
    const total = Object.values(dist).reduce((a, b) => a + b, 0);
    const extremes = dist[5] + dist[1];
    const middle = dist[4] + dist[3] + dist[2];
    
    // High bimodal score = many 5-stars AND many 1-stars
    const extremesPct = extremes / total;
    const middlePct = middle / total;
    
    // Score 0-100: Higher = more bimodal (suspicious)
    return extremesPct > 0.7 && dist[5] > 0 && dist[1] > 0 
      ? (extremesPct * 100) 
      : 0;
  }
  
  calculatePolarization(dist) {
    // Measure variance in ratings
    const total = Object.values(dist).reduce((a, b) => a + b, 0);
    const values = [1, 2, 3, 4, 5];
    
    // Calculate weighted average
    const mean = values.reduce((sum, val, i) => 
      sum + (val * dist[val]) / total, 0
    );
    
    // Calculate standard deviation
    const variance = values.reduce((sum, val) => 
      sum + Math.pow(val - mean, 2) * (dist[val] / total), 0
    );
    
    return Math.sqrt(variance);
  }
  
  calculateTrustScore(product) {
    const avg = product.rating_average;
    const total = product.total_reviews;
    const dist = product.rating_distribution;
    
    // Base score from average rating
    let score = (avg / 5) * 100;
    
    // Penalty for low sample size
    if (total < 10) score *= 0.7;
    if (total < 5) score *= 0.5;
    
    // Penalty for high bimodal pattern
    const bimodal = this.calculateBimodalScore(dist);
    score -= bimodal * 0.3;
    
    // Penalty for below 4.5 average
    if (avg < 4.5) score *= 0.8;
    if (avg < 4.0) score *= 0.6;
    
    return Math.max(0, Math.min(100, score));
  }
  
  identifySuspiciousPatterns(product) {
    const flags = [];
    
    // Pattern 1: High ratings but low average (impossible unless bimodal)
    if (product.rating_5_estrelas > 20 && product.rating_average < 4.0) {
      flags.push('BIMODAL_DISTRIBUTION');
    }
    
    // Pattern 2: Low average (< 4.5)
    if (product.rating_average < 4.5 && product.total_reviews > 10) {
      flags.push('LOW_AVERAGE_RATING');
    }
    
    // Pattern 3: High negative review percentage
    const negativePct = (product.rating_1_estrela + product.rating_2_estrelas) 
                        / product.total_reviews * 100;
    if (negativePct > 20) {
      flags.push('HIGH_NEGATIVE_REVIEWS');
    }
    
    // Pattern 4: Few reviews for high price discount
    if (product.total_reviews < 5 && product.price_deviation_pct < -50) {
      flags.push('LOW_REVIEWS_SUSPICIOUS_PRICE');
    }
    
    return flags;
  }
}
```

**Statistical Features Generated:**
- `bimodal_score`: 0-100 (higher = more suspicious polarization)
- `polarization_index`: Standard deviation of ratings
- `positive_pct`, `negative_pct`, `neutral_pct`: Distribution percentages
- `trust_score`: 0-100 aggregate trustworthiness
- `suspicious_patterns`: Array of red flags

---

### 2.3 Review Text Analysis Module (LLM-Powered)

**Key Goals:**
- Sentiment analysis on review comments
- Extract counterfeit indicators from text
- Identify authenticity-related keywords

```javascript
class LLMReviewAnalyzer {
  
  constructor(openaiApiKey) {
    this.openai = new OpenAI({ apiKey: openaiApiKey });
  }
  
  async analyzeReviewBatch(reviews) {
    // Only analyze reviews with text
    const reviewsWithText = reviews.filter(r => r.text && r.text.length > 10);
    
    if (reviewsWithText.length === 0) {
      return { has_text_reviews: false };
    }
    
    // Batch reviews for cost efficiency (max 20 reviews per batch)
    const batches = this.createBatches(reviewsWithText, 20);
    const results = [];
    
    for (const batch of batches) {
      const result = await this.analyzeBatchWithGPT(batch);
      results.push(result);
    }
    
    return this.aggregateResults(results);
  }
  
  async analyzeBatchWithGPT(reviewBatch) {
    const prompt = this.buildAnalysisPrompt(reviewBatch);
    
    const response = await this.openai.chat.completions.create({
      model: "gpt-4o-mini", // Cost-effective for batch analysis
      temperature: 0.1, // Low temp for consistent analysis
      response_format: { type: "json_object" },
      messages: [
        {
          role: "system",
          content: `You are an expert at analyzing product reviews to detect counterfeit products.
Focus on HP printer cartridges. Analyze reviews for authenticity indicators.
Return structured JSON with sentiment scores and detected patterns.`
        },
        {
          role: "user",
          content: prompt
        }
      ]
    });
    
    return JSON.parse(response.choices[0].message.content);
  }
  
  buildAnalysisPrompt(reviews) {
    return `Analyze these ${reviews.length} reviews for HP cartridge authenticity indicators.

REVIEWS:
${reviews.map((r, i) => `
${i + 1}. [${r.rating}★] ${r.date}: "${r.text}"
`).join('\n')}

COUNTERFEIT INDICATORS TO DETECT:
- "não é original", "falsificado", "pirata", "fake"
- "acabou rápido", "durou pouco", "não imprime"
- "recarregado", "recarga", "vazou"
- "impressora não reconhece", "não funciona"
- "veio vazio", "pouca tinta"
- "qualidade ruim", "impressão ruim"

AUTHENTIC INDICATORS:
- "original", "genuíno", "lacrado"
- "funcionou perfeitamente", "ótima qualidade"
- "duradouro", "rende bem"
- "HP reconheceu"

Return JSON:
{
  "overall_sentiment": {
    "score": -1 to 1 (negative to positive),
    "distribution": {"positive": X, "neutral": Y, "negative": Z}
  },
  "authenticity_signals": {
    "likely_counterfeit": X,
    "likely_authentic": Y,
    "ambiguous": Z
  },
  "key_complaints": [
    {"complaint": "short_duration", "count": X, "severity": "high"},
    {"complaint": "not_recognized", "count": Y, "severity": "critical"}
  ],
  "key_praises": [
    {"praise": "original_quality", "count": X}
  ],
  "counterfeit_keywords_found": ["acabou rápido", "não original"],
  "authentic_keywords_found": ["original", "lacrado"],
  "recommended_action": "FLAG_AS_SUSPICIOUS" | "LIKELY_AUTHENTIC" | "NEEDS_REVIEW"
}`;
  }
  
  aggregateResults(batchResults) {
    // Combine multiple batch results into single analysis
    return {
      has_text_reviews: true,
      total_analyzed: batchResults.reduce((sum, r) => sum + r.analyzed_count, 0),
      
      sentiment: {
        overall_score: this.averageScore(batchResults, 'overall_sentiment.score'),
        positive_count: this.sumField(batchResults, 'overall_sentiment.distribution.positive'),
        negative_count: this.sumField(batchResults, 'overall_sentiment.distribution.negative'),
        neutral_count: this.sumField(batchResults, 'overall_sentiment.distribution.neutral')
      },
      
      authenticity: {
        counterfeit_signals: this.sumField(batchResults, 'authenticity_signals.likely_counterfeit'),
        authentic_signals: this.sumField(batchResults, 'authenticity_signals.likely_authentic'),
        ambiguous_signals: this.sumField(batchResults, 'authenticity_signals.ambiguous')
      },
      
      complaints: this.aggregateComplaints(batchResults),
      praises: this.aggregatePraises(batchResults),
      
      counterfeit_keywords: this.uniqueKeywords(batchResults, 'counterfeit'),
      authentic_keywords: this.uniqueKeywords(batchResults, 'authentic'),
      
      llm_recommendation: this.determineConsensus(batchResults)
    };
  }
}
```

**LLM Features Generated:**
- `sentiment_score`: -1 to 1 (overall sentiment)
- `counterfeit_signal_count`: Number of counterfeit indicators
- `authentic_signal_count`: Number of authentic indicators
- `key_complaints`: Array of specific issues mentioned
- `counterfeit_keywords`: Extracted red-flag terms
- `llm_recommendation`: FLAG_AS_SUSPICIOUS | LIKELY_AUTHENTIC | NEEDS_REVIEW

---

### 2.4 Seller Profiling Module

```javascript
class SellerAnalyzer {
  
  analyzeSellerRisk(seller, sellerProducts) {
    return {
      // Basic metrics
      total_listings: sellerProducts.length,
      avg_price_deviation: this.calculateAvgDeviation(sellerProducts),
      
      // Location-based risk
      location_risk: this.assessLocationRisk(seller.address.state),
      
      // Reputation analysis
      reputation_score: this.scoreReputation(seller),
      is_power_seller: !!seller.seller_reputation.power_seller_status,
      
      // Product patterns
      xl_ratio: this.calculateXLRatio(sellerProducts),
      bundle_ratio: this.calculateBundleRatio(sellerProducts),
      
      // Review patterns across all listings
      avg_rating: this.calculateAvgRating(sellerProducts),
      products_below_4_5: sellerProducts.filter(p => p.rating_average < 4.5).length,
      
      // Authorization status
      is_authorized_dealer: this.checkAuthorizedDealer(seller),
      
      // Risk flags
      risk_flags: this.identifySellerRiskFlags(seller, sellerProducts)
    };
  }
  
  calculateXLRatio(products) {
    const xlCount = products.filter(p => p.is_xl).length;
    return xlCount / products.length;
  }
  
  identifySellerRiskFlags(seller, products) {
    const flags = [];
    
    // High XL ratio (counterfeiters focus on XL)
    if (this.calculateXLRatio(products) > 0.7) {
      flags.push('HIGH_XL_RATIO');
    }
    
    // Multiple low-rated products
    const lowRated = products.filter(p => p.rating_average < 4.0).length;
    if (lowRated / products.length > 0.3) {
      flags.push('MULTIPLE_LOW_RATED_PRODUCTS');
    }
    
    // Low reputation
    if (seller.seller_reputation.level_id === '1_red') {
      flags.push('LOW_SELLER_REPUTATION');
    }
    
    // Not authorized
    if (!this.checkAuthorizedDealer(seller)) {
      flags.push('NOT_AUTHORIZED_DEALER');
    }
    
    // Suspicious location patterns (if needed)
    // flags.push('SUSPICIOUS_LOCATION');
    
    return flags;
  }
}
```

**Seller Features Generated:**
- `total_listings`: Number of products seller has
- `avg_price_deviation`: Average price deviation across all products
- `xl_ratio`: Percentage of XL products (counterfeit indicator)
- `products_below_4_5`: Count of low-rated products
- `is_authorized_dealer`: Boolean from authorized list
- `seller_risk_flags`: Array of red flags

---

## STAGE 3: LLM Review Text Analysis (DETAILED)

### 3.1 Review-Level LLM Analysis

For the **39 products** with extracted review text, perform deep analysis:

```javascript
class DetailedReviewLLMAnalyzer {
  
  async analyzeIndividualReviews(reviewsData) {
    const results = [];
    
    for (const review of reviewsData.reviews) {
      if (!review.text || review.text.length < 5) continue;
      
      const analysis = await this.analyzeReviewWithGPT(review);
      results.push({
        review_number: review.review_number,
        rating: review.rating,
        original_text: review.text,
        ...analysis
      });
    }
    
    return results;
  }
  
  async analyzeReviewWithGPT(review) {
    const response = await this.openai.chat.completions.create({
      model: "gpt-4o-mini",
      temperature: 0.1,
      response_format: { type: "json_object" },
      messages: [
        {
          role: "system",
          content: `Analyze HP cartridge reviews for authenticity. 
Extract: sentiment, counterfeit indicators, specific complaints/praises.
Return structured JSON.`
        },
        {
          role: "user",
          content: `Review: [${review.rating}★] "${review.text}"
          
Classify this review and extract:
1. Sentiment: positive/neutral/negative
2. Authenticity signal: likely_counterfeit/likely_authentic/unclear
3. Key topics mentioned
4. Specific complaints or praises
5. Keywords indicating fake/original

Return JSON:
{
  "sentiment": "positive|neutral|negative",
  "sentiment_score": -1 to 1,
  "authenticity_signal": "counterfeit|authentic|unclear",
  "confidence": 0 to 1,
  "topics": ["durability", "price", "quality"],
  "complaints": ["short_duration", "not_original"],
  "praises": ["good_quality", "original"],
  "keywords": {
    "counterfeit_indicators": ["acabou rápido", "não original"],
    "authentic_indicators": ["original", "lacrado"]
  },
  "is_suspicious": true/false
}`
        }
      ]
    });
    
    return JSON.parse(response.choices[0].message.content);
  }
}
```

### 3.2 Product Description LLM Analysis

```javascript
class DescriptionAnalyzer {
  
  async analyzeProductDescription(product) {
    const description = product.raw_description || product.titulo;
    
    if (!description || description.length < 20) {
      return { has_description: false };
    }
    
    const response = await this.openai.chat.completions.create({
      model: "gpt-4o-mini",
      temperature: 0.1,
      response_format: { type: "json_object" },
      messages: [
        {
          role: "system",
          content: `Analyze HP cartridge product descriptions for authenticity signals.
Counterfeiters often use misleading language or overpromise.
Authentic sellers are straightforward with official specs.`
        },
        {
          role: "user",
          content: `Title: ${product.titulo}
Description: ${description}

Analyze for:
1. Claims of "original" or authenticity
2. Suspicious language patterns
3. Overpromising or exaggeration
4. Technical accuracy vs HP specs
5. Bundle/kit indicators

Return JSON:
{
  "claims_original": true/false,
  "authenticity_language_score": 0 to 1,
  "suspicious_phrases": ["promoção imperdível", "super desconto"],
  "technical_accuracy": 0 to 1,
  "is_bundle": true/false,
  "bundle_quantity": number,
  "model_detected": "664XL",
  "color_detected": "Preto|Colorido",
  "overpromise_score": 0 to 1,
  "description_risk_level": "low|medium|high"
}`
        }
      ]
    });
    
    return JSON.parse(response.choices[0].message.content);
  }
}
```

---

## STAGE 4: Review Weight Calculation

### 4.1 Weighted Review Score

**The key innovation: Multi-dimensional review weighting**

```javascript
class ReviewWeightCalculator {
  
  calculateWeightedReviewScore(product) {
    const weights = {
      // Statistical component (40% weight)
      statistical: {
        weight: 0.4,
        score: this.calculateStatisticalScore(product)
      },
      
      // LLM sentiment component (30% weight)
      llm_sentiment: {
        weight: 0.3,
        score: product.llm_analysis?.sentiment?.overall_score || 0.5
      },
      
      // LLM authenticity signals (30% weight)
      llm_authenticity: {
        weight: 0.3,
        score: this.calculateAuthenticityScore(product.llm_analysis)
      }
    };
    
    // Weighted sum
    const totalScore = Object.values(weights).reduce(
      (sum, component) => sum + (component.score * component.weight), 
      0
    );
    
    return {
      weighted_review_score: totalScore,
      components: weights,
      interpretation: this.interpretScore(totalScore)
    };
  }
  
  calculateStatisticalScore(product) {
    // Convert statistical metrics to 0-1 scale
    const avgRating = product.rating_average / 5; // 0-1
    const trustScore = product.trust_score / 100; // 0-1
    const bimodalPenalty = product.bimodal_score / 100; // 0-1 (inverted)
    
    // Combine
    const score = (
      avgRating * 0.5 + 
      trustScore * 0.3 + 
      (1 - bimodalPenalty) * 0.2
    );
    
    return score;
  }
  
  calculateAuthenticityScore(llmAnalysis) {
    if (!llmAnalysis) return 0.5; // Neutral if no LLM data
    
    const { counterfeit_signals, authentic_signals, ambiguous_signals } = 
      llmAnalysis.authenticity || {};
    
    const total = counterfeit_signals + authentic_signals + ambiguous_signals;
    if (total === 0) return 0.5;
    
    // Score based on authentic vs counterfeit ratio
    const authenticRatio = authentic_signals / total;
    const counterfeitRatio = counterfeit_signals / total;
    
    return authenticRatio - counterfeitRatio; // -1 to 1, normalize to 0-1
  }
  
  interpretScore(score) {
    if (score >= 0.8) return 'LIKELY_AUTHENTIC';
    if (score >= 0.6) return 'PROBABLY_AUTHENTIC';
    if (score >= 0.4) return 'UNCERTAIN';
    if (score >= 0.2) return 'PROBABLY_COUNTERFEIT';
    return 'LIKELY_COUNTERFEIT';
  }
}
```

---

## STAGE 5: Final Risk Scoring

### 5.1 Multi-Signal Risk Score

```javascript
class FinalRiskScorer {
  
  calculateOverallRiskScore(enrichedProduct) {
    const signals = {
      // Price signal (25% weight)
      price: {
        weight: 0.25,
        score: this.scorePriceRisk(enrichedProduct),
        evidence: enrichedProduct.price_deviation_pct
      },
      
      // Review signal (35% weight) - HIGHEST WEIGHT
      reviews: {
        weight: 0.35,
        score: 1 - enrichedProduct.weighted_review_score, // Invert (high review = low risk)
        evidence: enrichedProduct.weighted_review_score
      },
      
      // Seller signal (25% weight)
      seller: {
        weight: 0.25,
        score: this.scoreSellerRisk(enrichedProduct.seller),
        evidence: enrichedProduct.seller.risk_flags
      },
      
      // Product characteristics (15% weight)
      product: {
        weight: 0.15,
        score: this.scoreProductRisk(enrichedProduct),
        evidence: { is_xl: enrichedProduct.is_xl, is_bundle: enrichedProduct.is_bundle }
      }
    };
    
    // Weighted risk score (0-100, higher = more suspicious)
    const riskScore = Object.values(signals).reduce(
      (sum, signal) => sum + (signal.score * signal.weight * 100),
      0
    );
    
    return {
      overall_risk_score: riskScore,
      risk_category: this.categorizeRisk(riskScore),
      signal_breakdown: signals,
      flags: this.collectAllFlags(enrichedProduct),
      recommendation: this.generateRecommendation(riskScore, signals)
    };
  }
  
  scorePriceRisk(product) {
    const deviation = product.price_deviation_pct;
    
    if (deviation === null) return 0.3; // Unknown = moderate risk
    if (deviation < -70) return 1.0;    // 70%+ discount = max risk
    if (deviation < -50) return 0.8;
    if (deviation < -30) return 0.6;
    if (deviation < -10) return 0.3;
    return 0.1; // Normal pricing = low risk
  }
  
  scoreSellerRisk(seller) {
    let risk = 0;
    
    // Not authorized dealer
    if (!seller.is_authorized) risk += 0.4;
    
    // Low reputation
    if (seller.reputation_level?.includes('red')) risk += 0.3;
    if (seller.reputation_level?.includes('orange')) risk += 0.2;
    
    // Few transactions
    if (seller.total_transactions < 100) risk += 0.2;
    
    // Risk flags
    risk += seller.risk_flags.length * 0.1;
    
    return Math.min(1.0, risk);
  }
  
  scoreProductRisk(product) {
    let risk = 0;
    
    // XL products (counterfeiters prefer these)
    if (product.is_xl) risk += 0.3;
    
    // Bundles (harder to verify)
    if (product.is_bundle && product.bundle_quantity > 2) risk += 0.2;
    
    return Math.min(1.0, risk);
  }
  
  categorizeRisk(score) {
    if (score >= 75) return 'CRITICAL';
    if (score >= 60) return 'HIGH';
    if (score >= 40) return 'MEDIUM';
    if (score >= 20) return 'LOW';
    return 'MINIMAL';
  }
  
  generateRecommendation(score, signals) {
    if (score >= 75) {
      return {
        action: 'PRIORITY_INVESTIGATION',
        priority: 1,
        suggested_actions: [
          'Flag for immediate review',
          'Report to Mercado Livre',
          'Add to monitoring list'
        ]
      };
    }
    
    if (score >= 60) {
      return {
        action: 'INVESTIGATE',
        priority: 2,
        suggested_actions: [
          'Manual review required',
          'Collect additional evidence',
          'Monitor seller activity'
        ]
      };
    }
    
    if (score >= 40) {
      return {
        action: 'MONITOR',
        priority: 3,
        suggested_actions: [
          'Add to watchlist',
          'Periodic review'
        ]
      };
    }
    
    return {
      action: 'LOW_PRIORITY',
      priority: 4,
      suggested_actions: ['Routine monitoring']
    };
  }
}
```

---

## 💡 Key Innovation: Review Weight Strategy

### Three-Tier Review Analysis

```
┌─────────────────────────────────────────────────────────────────┐
│  TIER 1: All Products (229 products)                            │
│  - Statistical analysis of rating distributions                 │
│  - Bimodal detection                                            │
│  - Basic trust scoring                                          │
│  - Weight: 40% of final review score                            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  TIER 2: Products with Extracted Reviews (39 products)          │
│  - LLM sentiment analysis on review text                        │
│  - Keyword extraction (counterfeit vs authentic)                │
│  - Complaint categorization                                     │
│  - Weight: 30% of final review score                            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  TIER 3: Product Descriptions (All products)                    │
│  - LLM analysis of advertisement text                           │
│  - Authenticity claim verification                              │
│  - Bundle detection and quantity extraction                     │
│  - Weight: 30% of final review score                            │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📈 Output Dataset Structure

### Final Enriched Product Schema

```javascript
{
  // Core identifiers
  "product_id": "MLB3159055901",
  "seller_id": "677845209",
  
  // Product info
  "title": "Kit Cartuchos Originais Hp 664...",
  "model": "664",
  "is_xl": false,
  "is_bundle": true,
  "bundle_quantity": 2,
  
  // PRICE FEATURES
  "price_analysis": {
    "listed_price": 209.99,
    "unit_price": 104.99,
    "suggested_price": 74.90,
    "deviation_pct": -40.2,
    "risk_level": "MEDIUM",
    "is_suspicious": true
  },
  
  // REVIEW FEATURES (Statistical)
  "review_statistics": {
    "average_rating": 4.7,
    "total_reviews": 43,
    "distribution": {
      "5_star_pct": 86.0,
      "4_star_pct": 2.3,
      "3_star_pct": 2.3,
      "2_star_pct": 2.3,
      "1_star_pct": 2.3
    },
    "bimodal_score": 12.5,
    "polarization_index": 0.8,
    "trust_score": 78.4,
    "suspicious_patterns": ["BIMODAL_DISTRIBUTION"]
  },
  
  // REVIEW FEATURES (LLM - if text available)
  "review_llm_analysis": {
    "has_text_reviews": true,
    "analyzed_count": 3,
    "sentiment": {
      "overall_score": 0.6,
      "positive_count": 2,
      "negative_count": 1,
      "neutral_count": 0
    },
    "authenticity": {
      "counterfeit_signals": 1,
      "authentic_signals": 2,
      "ambiguous_signals": 0
    },
    "key_complaints": [
      { "type": "short_duration", "count": 1, "severity": "high" }
    ],
    "key_praises": [
      { "type": "original_quality", "count": 2 }
    ],
    "counterfeit_keywords": ["não dura"],
    "authentic_keywords": ["original", "ótimo"],
    "llm_recommendation": "LIKELY_AUTHENTIC"
  },
  
  // DESCRIPTION FEATURES (LLM)
  "description_analysis": {
    "claims_original": true,
    "bundle_detected": true,
    "bundle_quantity": 2,
    "model_detected": "664",
    "overpromise_score": 0.3,
    "description_risk_level": "low"
  },
  
  // SELLER FEATURES
  "seller_analysis": {
    "nickname": "YELLOWCELL ACESSORIOS",
    "location": "São Paulo, BR-SP",
    "state": "BR-SP",
    "reputation_level": "5_green",
    "power_seller": "gold",
    "total_transactions": 11918,
    "is_authorized": false,
    "total_listings": 15,
    "avg_price_deviation": -35.2,
    "xl_ratio": 0.73,
    "products_below_4_5": 2,
    "seller_risk_flags": [
      "NOT_AUTHORIZED_DEALER",
      "HIGH_XL_RATIO"
    ]
  },
  
  // FINAL SCORING
  "risk_assessment": {
    "overall_risk_score": 58.7,
    "risk_category": "MEDIUM",
    "signal_breakdown": {
      "price": { weight: 0.25, score: 0.6, evidence: -40.2 },
      "reviews": { weight: 0.35, score: 0.4, evidence: 0.6 },
      "seller": { weight: 0.25, score: 0.7, evidence: [...] },
      "product": { weight: 0.15, score: 0.5, evidence: {...} }
    },
    "all_flags": [
      "MEDIUM_PRICE_DISCOUNT",
      "BIMODAL_DISTRIBUTION",
      "NOT_AUTHORIZED_DEALER",
      "HIGH_XL_RATIO"
    ],
    "recommendation": {
      "action": "INVESTIGATE",
      "priority": 2,
      "suggested_actions": [
        "Manual review required",
        "Collect additional evidence",
        "Monitor seller activity"
      ]
    }
  },
  
  // ML MODEL FEATURES (Flattened for training)
  "ml_features": {
    "price_deviation": -40.2,
    "avg_rating": 4.7,
    "total_reviews": 43,
    "negative_pct": 4.6,
    "bimodal_score": 12.5,
    "sentiment_score": 0.6,
    "counterfeit_signals": 1,
    "authentic_signals": 2,
    "seller_transactions": 11918,
    "is_authorized": 0,
    "is_xl": 0,
    "is_bundle": 1,
    "xl_seller_ratio": 0.73,
    "location_risk": 0.2
    // ... more features
  }
}
```

---

## 🔧 Implementation Roadmap

### Phase 1: Data Integration (Week 1)
```javascript
// tasks.js
async function phase1_DataIntegration() {
  // 1.1 Load all JSON files
  const products = await loadMainDataset();
  const reviews = await loadReviews();
  const sellers = await loadSellers();
  const prices = await loadPriceTable();
  
  // 1.2 Create indexes
  const indexes = createIndexes({ products, reviews, sellers, prices });
  
  // 1.3 Join data
  const unifiedDataset = products.map(p => 
    joinProductData(p, indexes)
  );
  
  // 1.4 Validate relationships
  const validation = validateDataIntegrity(unifiedDataset);
  
  // 1.5 Save unified dataset
  await saveJSON('unified_dataset.json', unifiedDataset);
  
  return { unifiedDataset, validation };
}
```

### Phase 2: Statistical Analysis (Week 1-2)
```javascript
async function phase2_StatisticalAnalysis() {
  const dataset = await loadJSON('unified_dataset.json');
  
  const analyzed = dataset.map(product => ({
    ...product,
    price_analysis: priceAnalyzer.analyze(product),
    review_statistics: reviewStatAnalyzer.analyze(product),
    seller_analysis: sellerAnalyzer.analyze(product)
  }));
  
  await saveJSON('dataset_with_stats.json', analyzed);
  
  return analyzed;
}
```

### Phase 3: LLM Enrichment (Week 2-3)
```javascript
async function phase3_LLMEnrichment() {
  const dataset = await loadJSON('dataset_with_stats.json');
  
  // Process in batches to manage API costs
  const enriched = [];
  
  for (const product of dataset) {
    // Only run LLM on reviews with text (39 products)
    const reviewAnalysis = product.reviews_data.extracted_count > 0
      ? await llmReviewAnalyzer.analyze(product.reviews_data.detailed_reviews)
      : { has_text_reviews: false };
    
    // Run LLM on all product descriptions
    const descAnalysis = await descriptionAnalyzer.analyze(product);
    
    enriched.push({
      ...product,
      review_llm_analysis: reviewAnalysis,
      description_analysis: descAnalysis
    });
    
    // Rate limiting
    await sleep(100); // 10 req/sec max
  }
  
  await saveJSON('dataset_llm_enriched.json', enriched);
  
  return enriched;
}
```

### Phase 4: Feature Engineering (Week 3)
```javascript
async function phase4_FeatureEngineering() {
  const dataset = await loadJSON('dataset_llm_enriched.json');
  
  const withFeatures = dataset.map(product => ({
    ...product,
    weighted_review_score: reviewWeightCalc.calculate(product),
    risk_assessment: riskScorer.calculate(product),
    ml_features: featureExtractor.extract(product)
  }));
  
  // Create final training dataset
  const trainingData = withFeatures.map(p => ({
    features: p.ml_features,
    labels: {
      risk_score: p.risk_assessment.overall_risk_score,
      is_counterfeit: p.risk_assessment.overall_risk_score > 60 // Threshold
    }
  }));
  
  await saveJSON('ml_training_dataset.json', trainingData);
  await saveCSV('ml_features.csv', trainingData);
  
  return { withFeatures, trainingData };
}
```

---

## 🎯 Review Weight Calculation - DETAILED STRATEGY

### The Multi-Dimensional Approach

#### Dimension 1: Statistical Metrics (No LLM needed)
**Applied to ALL 229 products**

```python
def calculate_statistical_review_weight(product):
    """
    Statistical features from rating distribution alone
    """
    features = {}
    
    # 1. AVERAGE RATING SCORE
    features['avg_rating_normalized'] = product['rating_medio'] / 5.0
    
    # 2. REVIEW VOLUME CONFIDENCE
    # More reviews = more confidence
    total = product['total_reviews']
    features['volume_confidence'] = min(1.0, total / 100)  # Cap at 100 reviews
    
    # 3. BIMODAL DISTRIBUTION DETECTION
    # High 5-star AND high 1-star = suspicious
    dist = product['rating_distribution']
    total_ratings = sum(dist.values())
    
    pct_5 = dist[5] / total_ratings
    pct_1 = dist[1] / total_ratings
    
    # Bimodal if both extremes > 20%
    features['is_bimodal'] = (pct_5 > 0.2 and pct_1 > 0.2)
    features['bimodal_score'] = (pct_5 * pct_1) * 100  # Product of extremes
    
    # 4. NEGATIVE REVIEW PERCENTAGE
    negative = dist[1] + dist[2]
    features['negative_pct'] = (negative / total_ratings) * 100
    
    # 5. VARIANCE/POLARIZATION
    ratings = [1, 2, 3, 4, 5]
    mean = sum(r * dist[r] for r in ratings) / total_ratings
    variance = sum((r - mean)**2 * dist[r] for r in ratings) / total_ratings
    features['polarization'] = variance ** 0.5
    
    # 6. SUSPICIOUS PATTERN FLAGS
    flags = []
    if features['negative_pct'] > 20:
        flags.append('HIGH_NEGATIVE_RATIO')
    if features['bimodal_score'] > 25:
        flags.append('BIMODAL_PATTERN')
    if product['rating_medio'] < 4.5 and total > 10:
        flags.append('LOW_AVERAGE_WITH_VOLUME')
    
    features['suspicious_patterns'] = flags
    
    # 7. FINAL STATISTICAL WEIGHT (0-1 scale, 1 = trustworthy)
    stat_weight = (
        features['avg_rating_normalized'] * 0.4 +
        features['volume_confidence'] * 0.2 +
        (1 - features['bimodal_score'] / 100) * 0.2 +
        (1 - features['negative_pct'] / 100) * 0.2
    )
    
    features['statistical_weight'] = max(0, min(1, stat_weight))
    
    return features
```

#### Dimension 2: LLM Sentiment Analysis
**Applied to 39 products with text reviews**

```python
async def calculate_llm_sentiment_weight(reviews_with_text):
    """
    Deep semantic analysis using GPT-4
    """
    # Batch reviews for cost efficiency
    batch_size = 20
    
    prompt = f"""Analyze these HP cartridge reviews for authenticity.

REVIEWS:
{format_reviews_for_prompt(reviews_with_text)}

For each review, detect:
1. Sentiment (-1 to 1)
2. Counterfeit indicators: "não é original", "acabou rápido", "falso", "vazou", "não funciona"
3. Authentic indicators: "original", "lacrado", "HP reconheceu", "ótima qualidade"
4. Specific complaints about: duration, recognition, print quality, leaking

Return JSON with aggregated analysis."""
    
    response = await openai.chat.completions.create(
        model="gpt-4o-mini",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": COUNTERFEIT_DETECTOR_SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ]
    )
    
    analysis = json.loads(response.choices[0].message.content)
    
    # Calculate LLM weight
    llm_weight = (
        (analysis['sentiment_score'] + 1) / 2 * 0.4 +  # Normalize -1:1 to 0:1
        (analysis['authentic_signals'] / 
         (analysis['authentic_signals'] + analysis['counterfeit_signals'] + 1)) * 0.6
    )
    
    return {
        'llm_sentiment_weight': llm_weight,
        'llm_analysis': analysis
    }
```

#### Dimension 3: Description Analysis
**Applied to ALL products**

```python
async def analyze_product_description_llm(product):
    """
    Analyze advertisement description for red flags
    """
    prompt = f"""Analyze this HP cartridge product listing:

TITLE: {product['titulo']}
DESCRIPTION: {product['descricao'][:500]}  # First 500 chars
PRICE: R$ {product['preco']} (HP Suggested: R$ {product['suggested_price']})

Detect:
1. Bundle/kit indicators and quantity
2. Claims of "original" or authenticity
3. Suspicious promotional language ("promoção imperdível", "super oferta")
4. XL model indicators
5. Technical specification accuracy
6. Overpromising patterns

Return JSON with analysis."""
    
    response = await openai.chat.completions.create(
        model="gpt-4o-mini",
        response_format={"type": "json_object"},
        messages=[...
]
    )
    
    return json.loads(response.choices[0].message.content)
```

---

## 🧮 Final Review Weight Formula

### Composite Score Calculation

```python
def calculate_final_review_weight(product):
    """
    Combine all review dimensions into single trustworthiness score
    """
    
    # Component 1: Statistical (ALWAYS available - 40% weight)
    stat_weight = product['review_statistics']['statistical_weight']
    
    # Component 2: LLM Sentiment (CONDITIONAL - 30% weight if available)
    if product['review_llm_analysis']['has_text_reviews']:
        sentiment_weight = product['review_llm_analysis']['llm_sentiment_weight']
    else:
        # Fallback: use statistical as proxy
        sentiment_weight = stat_weight
    
    # Component 3: Description Analysis (ALWAYS available - 30% weight)
    desc_weight = product['description_analysis']['authenticity_score']
    
    # Weighted combination
    final_weight = (
        stat_weight * 0.40 +
        sentiment_weight * 0.30 +
        desc_weight * 0.30
    )
    
    return {
        'review_weight': final_weight,  # 0-1 scale (1 = highly trustworthy)
        'review_risk': 1 - final_weight,  # Invert for risk score
        'components': {
            'statistical': stat_weight,
            'sentiment': sentiment_weight,
            'description': desc_weight
        },
        'interpretation': interpret_weight(final_weight)
    }

def interpret_weight(weight):
    if weight >= 0.8:
        return 'HIGHLY_TRUSTWORTHY'
    elif weight >= 0.6:
        return 'TRUSTWORTHY'
    elif weight >= 0.4:
        return 'UNCERTAIN'
    elif weight >= 0.2:
        return 'SUSPICIOUS'
    else:
        return 'HIGHLY_SUSPICIOUS'
```

---

## 📊 Proposed ML Features Matrix

### Feature Categories for Model Training

| Category | Feature Name | Type | Source | Description |
|----------|--------------|------|--------|-------------|
| **PRICE** | `price_deviation_pct` | float | Calculated | % deviation from suggested |
| | `unit_price` | float | Calculated | Bundle-adjusted price |
| | `is_suspicious_price` | bool | Calculated | <-30% threshold |
| | `price_risk_level` | categorical | Calculated | CRITICAL/HIGH/MEDIUM/LOW |
| **REVIEW STATS** | `avg_rating` | float | Dataset | 0-5 scale |
| | `total_reviews` | int | Dataset | Review count |
| | `negative_pct` | float | Calculated | % of 1-2 star reviews |
| | `bimodal_score` | float | Calculated | 0-100 polarization |
| | `polarization_index` | float | Calculated | Std deviation |
| | `trust_score` | float | Calculated | 0-100 trustworthiness |
| **REVIEW LLM** | `sentiment_score` | float | LLM | -1 to 1 |
| | `counterfeit_signal_count` | int | LLM | # of fake indicators |
| | `authentic_signal_count` | int | LLM | # of real indicators |
| | `complaint_severity` | float | LLM | Weighted severity 0-1 |
| **DESCRIPTION** | `claims_original` | bool | LLM | Advertises as original |
| | `overpromise_score` | float | LLM | 0-1 exaggeration |
| | `desc_risk_level` | categorical | LLM | low/medium/high |
| **SELLER** | `seller_transactions` | int | Dataset | Total sales |
| | `is_authorized` | bool | Calculated | In authorized list |
| | `seller_reputation` | categorical | Dataset | 5_green, 1_red, etc. |
| | `xl_ratio` | float | Calculated | % of XL products |
| | `avg_seller_rating` | float | Calculated | Across all listings |
| **PRODUCT** | `is_xl` | bool | Extracted | XL model flag |
| | `is_bundle` | bool | Extracted | Kit/bundle flag |
| | `bundle_quantity` | int | Extracted | Items in bundle |
| **COMPOSITE** | `review_weight` | float | Calculated | Final 0-1 score |
| | `overall_risk_score` | float | Calculated | 0-100 risk |
| | `risk_category` | categorical | Calculated | Target variable |

**Total Features:** ~40 features for ML model

---

## 💰 LLM Cost Optimization Strategy

### Token Usage Estimation

```
Products with text reviews: 39
Avg reviews per product: ~20
Avg tokens per review: ~50
Total review tokens: 39 × 20 × 50 = 39,000 tokens (input)

Product descriptions: 229
Avg tokens per description: ~200
Total description tokens: 229 × 200 = 45,800 tokens (input)

TOTAL INPUT: ~85,000 tokens
TOTAL OUTPUT: ~30,000 tokens (structured JSON)
TOTAL: ~115,000 tokens

Cost with GPT-4o-mini:
- Input: $0.15 / 1M tokens = $0.0128
- Output: $0.60 / 1M tokens = $0.018
TOTAL COST: ~$0.03 per full dataset analysis
```

### Batch Processing Strategy

```javascript
class CostOptimizedLLMPipeline {
  
  async processDataset(products) {
    const results = [];
    
    // Tier 1: High priority (suspicious prices + reviews)
    const highPriority = products.filter(p => 
      p.price_deviation_pct < -50 || 
      p.rating_average < 4.0
    );
    
    // Tier 2: Medium priority (moderately suspicious)
    const mediumPriority = products.filter(p =>
      p.price_deviation_pct < -30 && 
      !highPriority.includes(p)
    );
    
    // Tier 3: Low priority (normal indicators)
    const lowPriority = products.filter(p =>
      !highPriority.includes(p) && 
      !mediumPriority.includes(p)
    );
    
    // Process with different strategies
    results.push(...await this.deepAnalysis(highPriority)); // Full LLM
    results.push(...await this.standardAnalysis(mediumPriority)); // Batched LLM
    results.push(...await this.lightAnalysis(lowPriority)); // Statistical only
    
    return results;
  }
}
```

---

## 🚀 Quick Start: Immediate Value Extraction

### Step 1: Basic Integration (No LLM - Fast)

```javascript
// quick_analysis.js
const basicAnalysis = products.map(product => {
  const reviews = reviewsMap.get(product.id);
  const seller = sellersMap.get(product.seller_id);
  
  return {
    product_id: product.id,
    title: product.titulo,
    price: product.preco,
    rating: product.rating_medio,
    
    // IMMEDIATE RED FLAGS
    flags: [
      product.rating_medio < 4.5 && 'LOW_RATING',
      product.total_reviews > 10 && product.rating_1_estrela > 5 && 'MULTIPLE_1_STARS',
      !seller && 'SELLER_NOT_FOUND',
      seller?.seller_reputation?.level_id === '1_red' && 'BAD_SELLER_REP'
    ].filter(Boolean),
    
    // Quick risk score
    quick_risk: (
      (product.rating_medio < 4.5 ? 30 : 0) +
      (product.rating_1_estrela > 5 ? 20 : 0) +
      (!seller ? 50 : 0)
    )
  };
});

// Sort by risk
const prioritized = basicAnalysis
  .sort((a, b) => b.quick_risk - a.quick_risk)
  .slice(0, 50);  // Top 50 suspicious

console.log('Top suspicious products:', prioritized);
```

---

## 📋 Suggested Next Steps

### Immediate Actions:
1. ✅ **Load price table** - Parse XLSX to get suggested retail prices
2. ✅ **Create unified dataset** - Join all 3 JSONs
3. ✅ **Implement price analysis** - Detect bundles, calculate deviations
4. ✅ **Statistical review analysis** - Bimodal detection, trust scores

### Short-term (This Week):
5. 🔄 **Set up OpenAI API** - Configure for LLM pipeline
6. 🔄 **Test LLM prompts** - Iterate on review analysis prompts
7. 🔄 **Process 39 products with reviews** - Full LLM enrichment
8. 🔄 **Validate results** - Manual check of LLM outputs

### Medium-term (Next 2 Weeks):
9. 🔄 **Feature engineering** - Create ML training features
10. 🔄 **Export training dataset** - CSV format for ML
11. 🔄 **Initial ML model** - Random Forest or Gradient Boosting
12. 🔄 **Evaluate model** - Precision/Recall for counterfeit detection

---

## 🎓 My Recommendations

### Priority Order:

1. **START HERE: Price + Statistical Review Analysis**
   - No LLM needed, fast results
   - Can identify ~60-70% of obvious fakes
   - Low cost, high value

2. **THEN: LLM on High-Risk Subset**
   - Focus on products already flagged by price/stats
   - ~50 products instead of 229
   - Cost: ~$0.01, Time: 5 minutes

3. **FINALLY: Full Pipeline with ML**
   - Once you have ground truth labels
   - Train supervised model
   - Use LLM features as inputs

### Suggested Tools:

```javascript
// Recommended stack
{
  "data_processing": "Node.js + TypeScript",
  "llm_calls": "OpenAI API (gpt-4o-mini)",
  "ml_model": "Python + scikit-learn or XGBoost",
  "visualization": "React dashboard for results",
  "database": "JSON files → SQLite → PostgreSQL (as scales)"
}
```

Would you like me to:
1. **Build the unified dataset script first?**
2. **Create the price analysis module?**
3. **Set up the LLM review analyzer with OpenAI?**
4. **Generate the feature engineering pipeline?**

Let me know which component to implement first!
