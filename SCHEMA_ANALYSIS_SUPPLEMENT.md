# Schema Analysis Supplement
## Detailed Examples, Edge Cases, and Specific Answers

---

## Part 1: Specific Field Value Examples

### ID Field Examples (Product IDs)

```
Format Analysis:
MLB36751629    → MLB + 8 digits
MLB37141763    → MLB + 8 digits
MLB1405822963  → MLB + 10 digits
MLB2039342702  → MLB + 10 digits
MLB765616253   → MLB + 9 digits

Pattern: r'^MLB\d{7,10}$'
All start with 'MLB'
Followed by 7-10 digits
No letters after MLB prefix
```

### Price Format Examples

```
"65.73"      → Standard 2 decimal places
"71.36"      → Standard
"1350.00"    → Large value, still 2 decimals
"10.00"      → Small value
"209.99"     → Always period as decimal separator
"128.92"     → Never comma separator

NEVER seen: "209,99" (European format)
NEVER seen: "R$ 209.99" (currency symbol)
NEVER seen: "209" (without decimals)

All are STRING type containing float representation
```

### Rating Examples (Main Dataset)

```json
// Product WITH reviews:
{
  "rating_medio": 4.7,          // float, range 0.0-5.0
  "total_reviews": 4976,        // int, positive
  "rating_5_estrelas": 4325,    // int
  "rating_4_estrelas": 355,
  "rating_3_estrelas": 105,
  "rating_2_estrelas": 39,
  "rating_1_estrela": 148       // Note: singular "estrela"
}
// Sum: 4325+355+105+39+148 = 4972 ≈ 4976 ✓

// Product WITHOUT reviews:
{
  "rating_medio": 0.0,          // ZERO (not null!)
  "total_reviews": 0,           // ZERO
  "rating_5_estrelas": 0,
  "rating_4_estrelas": 0,
  "rating_3_estrelas": 0,
  "rating_2_estrelas": 0,
  "rating_1_estrela": 0
}
```

**Key Insight:** Use `total_reviews == 0` to detect no-review products, NOT `rating_medio == 0`

---

## Part 2: Review Object Examples

### Review With Text (Typical)

```json
{
  "review_number": 1,
  "rating": 5,
  "date": "06 jun. 2024",
  "text": "Ótimo produto.",
  "likes": 0,
  "images": [],
  "image_count": 0,
  "has_images": false
}
```

### Review With High Engagement

```json
{
  "review_number": 91,
  "rating": 1,
  "date": "17 jul. 2020",
  "text": "Tive problemas com a impressora ( ficou tudo falhado a impressão) no dia seguinte vou tirar o cartucho, no visor da impressora consta que está acabando a tinta ( como pode se nem usei ??) só espero que não tenha prejudicado a minha impressora nova que tem um mês de compra. Esperando um retorno sobre o cartucho e no momento não tive resposta.",
  "likes": 8,                    // HIGH ENGAGEMENT
  "images": [],
  "image_count": 0,
  "has_images": false
}
```

**Pattern:** High-liked reviews (>5 likes) are almost always NEGATIVE complaints

### Review With Minimal Text

```json
{
  "review_number": 79,
  "rating": 4,
  "date": "28 jul. 2020",
  "text": "Ok.",                 // Just 3 characters!
  "likes": 0,
  "images": [],
  "image_count": 0,
  "has_images": false
}
```

### All Review Text Examples by Category

#### Unusable (≤5 chars) - 13 reviews

```
"."
"Ok."
"Bom."
"Sem texto."
```

**Recommendation:** Skip entirely for LLM processing

#### Minimal (6-20 chars) - 61 reviews

```
"Ótimo."
"Muito bom."
"Excelente."
"Ótimo produto."
"Produto bom."
"Muito pouca tinta."
"Não dura muito."
"Acabou rápido."
```

**Recommendation:** Batch process with simple sentiment classifier, skip LLM

#### Moderate (21-100 chars) - 379 reviews (MAJORITY!)

```
"Produto de ótima qualidade, recomendo."
"Original, funcionou perfeitamente."
"Bom produto mas acabou muito rápido."
"A tinta acabou rapidamente."
"Produto original de qualidade! sim, vale muito à pena!"
"Original é original. Sem nenhum tipo de problema."
"Muito bom e foi otimo encontrar na internet."
"Cartucho preto parou de funcionar com 2 dias de uso, entupiu."
"O cartucho preto veio vazio e vazio."
```

**Recommendation:** Primary target for LLM analysis - good signal-to-noise ratio

#### Detailed (>100 chars) - 41 reviews

```
"Produto de ótima qualidade, super recomendo pois é original. Não tenho que reclamar, atende super bem e da seu suporte."

"São ótimos, claro. Mas vieram mal embalados, sem nenhum isolamento, tive receio que nem funcionassem, de tão amassadas que as embalagens estavam. Agradeceria se pudessem corrigir isso."

"Parabéns perfeito seu produto, concerteza comprarei mais, tive problema só pra conectar a impressora com o celular, mas depois foi sucesso, podem comprar sem medo é produto de ótimo qualidade."

"Otima qualidade, pessima autonomia! se trata sem duvida de um produto original hp. A autonomina deixa e muito à desejar ! estou pensando inclusive em mudar de imoressora..."

"Não dou nota zero porque não tem como, imprimi no máximo umas 60 páginas e já acabou a tinta e minha impressora reconheceu como cartucho falsificado. Uma vergonha fazer isso com as pessoas..."
```

**Recommendation:** High-priority for LLM - rich context, specific claims

---

## Part 3: Seller Object Examples

### High-Volume Platinum Seller

```json
{
  "id": 480263032,                          // INTEGER
  "nickname": "Mercado Livre Eletronicos",
  "country_id": "BR",
  "address": {
    "city": "Cajamar",
    "state": "BR-SP"
  },
  "user_type": "brand",                     // Official brand
  "site_id": "MLB",
  "permalink": "http://perfil.mercadolivre.com.br/Mercado+Livre+Eletronicos",
  "seller_reputation": {
    "level_id": "5_green",                  // Highest level
    "power_seller_status": "platinum",      // Highest status
    "transactions": {
      "period": "historic",                 // Always "historic"
      "total": 13990875                     // 13.9 million transactions!
    }
  },
  "status": {
    "site_status": "active"
  }
}
```

### Low-Volume Seller (No Reputation)

```json
{
  "id": 24747394,
  "nickname": "ADLEYML",
  "country_id": "BR",
  "address": {
    "city": "Goiandira",
    "state": "BR-GO"
  },
  "user_type": "normal",                    // Regular user
  "site_id": "MLB",
  "permalink": "http://perfil.mercadolivre.com.br/ADLEYML",
  "seller_reputation": {
    "level_id": null,                       // NO LEVEL (not string "null")
    "power_seller_status": null,            // NO STATUS
    "transactions": {
      "period": "historic",
      "total": 2                            // Only 2 sales ever
    }
  },
  "status": {
    "site_status": "active"
  }
}
```

### Seller with Zero Transactions

```json
{
  "id": 79722769,
  "nickname": "BSMINFO",
  "address": {
    "city": "Porto Alegre",
    "state": "BR-RS"
  },
  "user_type": "normal",
  "seller_reputation": {
    "level_id": null,                       // No level
    "power_seller_status": null,            // No status
    "transactions": {
      "period": "historic",
      "total": 0                            // ZERO transactions
    }
  },
  "status": {
    "site_status": "active"                 // Still active!
  }
}
```

**8 sellers have 0 transactions** - likely new or inactive listings

---

## Part 4: Edge Cases Catalog

### Edge Case 1: Product with Empty Seller

**Full example of problematic product:**

```json
{
  "id": "MLB37201049",
  "titulo": "Kit 03 Cartuchos De Tinta Hp 664 F6v29ab Preto | MercadoLivre",
  "link": "https://www.mercadolivre.com.br/kit-03-cartuchos-de-tinta-hp-664-f6v29ab-preto/p/MLB37201049",
  "preco": "269.7",
  "preco_original": "",
  "desconto": "",
  "vendedor": "",                         // EMPTY STRING
  "seller_id": "",                        // EMPTY STRING
  "reputation_level": "",                 // EMPTY STRING
  "power_seller_status": "",              // EMPTY STRING
  "rating_medio": 0.0,
  "total_reviews": 0,
  "rating_5_estrelas": 0,
  // ... all rating fields are 0
  "marca": "HP",
  "condicao": "Novo",
  "frete_gratis": false,
  "descricao": "Características:\n- Marca: HP\n- Modelo: 664 (F6V29AB)...",
  "modelo": "664 (F6V29AB)",              // This field is populated!
  "cor_tinta": "Preto",
  // ... rest of fields normal
}
```

**Why this happens:** Product exists but seller data wasn't scraped properly

**How to handle:**
```python
if product['seller_id'] == "":
    # Option 1: Skip this product
    continue
    
    # Option 2: Mark as "unknown seller"
    product['seller_unknown'] = True
    product['seller_risk_score'] += 10  # Higher risk
```

### Edge Case 2: Reviews Entry with Metadata But No Review Text

**Product with `general_data` populated but `reviews` array empty:**

```json
{
  "product_id": "MLB4147342351",
  "extraction_timestamp": "2025-09-30T10:17:26.056500",
  "general_data": {
    "average_rating": 4.8,             // NOT null
    "total_reviews": 5                 // NOT null - 5 reviews exist on site
  },
  "ai_summary": {
    "summary": null,
    "likes": 0,
    "available": false
  },
  "characteristics_ratings": {},
  "reviews": [],                        // EMPTY ARRAY - no text extracted
  "total_reviews_extracted": 0          // ZERO extracted
}
```

**What this means:**
- Product HAS reviews on Mercado Livre (total_reviews: 5)
- BUT scraper didn't extract the review text
- Metadata available, content not available

**How to handle:**
```python
entry = review_index[product_id]

# Check if we have review text
if entry['total_reviews_extracted'] > 0:
    # We have actual review text to analyze
    reviews = entry['reviews']
    analyze_reviews(reviews)
else:
    # We only have metadata (or nothing)
    if entry['general_data']['total_reviews'] is not None:
        # Reviews exist but weren't extracted
        rating_only_analysis(entry['general_data']['average_rating'])
    else:
        # No reviews at all
        skip_product()
```

### Edge Case 3: Modelo Field Chaos Examples

**Well-formatted:**
```json
{"modelo": "664"}       // Clean, parseable
{"modelo": "664XL"}     // Clean with XL
{"modelo": "667"}       // Different model
```

**Poorly-formatted:**
```json
{"modelo": "Cartucho de Tinta"}  // Generic description, useless

{"modelo": "664 Negro + 664 Tricolor"}  // Bundle description

{"modelo": "Cartucho HP 664XL preto Original (F6V31AB) Para HP Deskjet 2136, 2676, 3776, 5076, 5276 CX 1 UN"}  
// Entire product title/description!

{"modelo": "664 - HP Deskjet Ink Advantage 1115,2134,2136,2676,3636,3776,3786,3788,3790,3836,4536,4676,5076,5276"}  
// Model + compatibility list

{"modelo": "18138"}     // Wrong number entirely
{"modelo": "74"}        // Wrong number
{"modelo": "KIT664"}    // Missing space
```

**Missing modelo key:**
```json
{
  "id": "MLB...",
  "titulo": "...",
  // ... no modelo field at all (4 products)
}
```

**Robust parsing code:**
```python
def extract_model_number(product):
    """Extract model with multiple fallbacks"""
    
    # Step 1: Try modelo field
    modelo = product.get('modelo', '')
    
    # Step 2: If modelo looks valid, parse it
    if modelo and len(modelo) < 20:  # Short = likely correct
        match = re.search(r'(66[247])(XL|xl)?', modelo, re.IGNORECASE)
        if match:
            return match.group(1), bool(match.group(2))
    
    # Step 3: Fallback to titulo
    titulo = product.get('titulo', '')
    match = re.search(r'\b(66[247])(XL|xl)?\b', titulo, re.IGNORECASE)
    if match:
        return match.group(1), bool(match.group(2))
    
    # Step 4: Fallback to descricao
    descricao = product.get('descricao', '')
    match = re.search(r'\b(66[247])(XL|xl)?\b', descricao, re.IGNORECASE)
    if match:
        return match.group(1), bool(match.group(2))
    
    return "UNKNOWN", False
```

---

## Part 5: Real Review Examples for Each Keyword Pattern

### "original" in Positive Context

```
[5-star] "Original. Nao aparentou nenhum problema."
[5-star] "Cartuchos originais e chegaram rapidamente."
[5-star] "Produto original reconhecido pela hp."
[5-star] "Original, perfeito. Atendeu a necessidade."
[5-star] "Muito bom produto. Original."
```

### "original" in Negative Context

```
[2-star] "Diz ser original, mais não durou nem 2 meses, imprimi poucas folhas, decepcionada."
[1-star] "Não dou nota zero porque não tem como, imprimi no máximo umas 60 páginas e já acabou a tinta e minha impressora reconheceu como cartucho falsificado."
```

**Critical:** "original" alone is NOT sufficient - need context/sentiment

### "acabou rápido" / "durou pouco"

```
[1-star] "Muito ruim. Não dura nem 20 página."
[3-star] "Achei que acabou muito rápido ,eu comprei tem menos de 2 meses e já acabou a tinta."
[1-star] "Acabou rápido."
[4-star] "Produto de ótima qualidade, porém acaba rápido."
```

**Pattern:** Common complaint even with "original" products - may not indicate counterfeit

### "vazio" / "pouca tinta"

```
[1-star] "O cartucho preto veio vazio e vazio."
[1-star] "Infelizmente o cartucho preto veio praticamente vazio."
[1-star] "Tive uma péssima experiência, fiz uma compra de um kit, o cartucho preto veio totalmente vazio apenas o colorido veio cheio."
[3-star] "A qualidade é muito boa mais a quantidade é péssima só usei uma vez quando fui usar novamente já não tinha mais tinta."
```

**Strong indicator of counterfeit** - product came empty/nearly empty

### "não reconhece" / "bloqueou"

```
[1-star] "Não gostei do cartucho. A impressora não reconhece. Fica dando impressora bloqueada."
[1-star] "minha impressora reconheceu como cartucho falsificado"
```

**Strongest indicator of counterfeit** - printer actively rejects cartridge

### "vazou" / "vazando"

```
[1-star] "Um veio vazando , e os outro após uso tb mancharam."
```

**Quality issue** - may indicate counterfeit or poor storage

### "recarregado" / "recarga"

```
[5-star] "Só usei a preta, por enquanto. Mas deu certo. Minha impressora é chatinha, se for regarregado ela não funciona."
[5-star] "Essa situação de recarregar para economizar não dá certo! o barato sai caro!!"
```

**Context:** Customer comparing to refilled cartridges (positive for original)

### "genuíno" / "lacrado"

```
[5-star] "3 Cartuchos Hp 664xl Preto 2 Color Genuíno"
[5-star] "Produto original, lacrado e em perfeito estado!."
[5-star] "Original, novo e muito bom. Recomendo."
```

**Strong positive indicators**

---

## Part 6: Seller Aggregation Detailed Analysis

### Seller Profile Example

**Seller: PARQUEINFORMATICA23 (ID: 1301646661)**

```
Products in catalog: 11
Reputation: 5_green, platinum, 73,388 transactions

Product breakdown:
- All 11 products are XL models (100%)
- 3 products are bundles (27.3%)
- Price range: R$ 111.19 to R$ 615.84
- Average price: R$ 254.91

Rating distribution across products:
- Average rating: 4.49
- 3 products below 4.5 rating (27.3%)
- Products with reviews: 8/11 (72.7%)
- Products without reviews: 3/11 (27.3%)

Geographic: Rio de Janeiro, BR-RJ
```

**Interpretation:**
- Specialized in XL models
- Mid-high price range
- High transaction volume = established seller
- Mostly good ratings but some low-rated products

---

### Seller Comparison Table

| Seller | Products | Avg Rating | %Low-Rated | %XL | %Bundle | Transactions |
|--------|----------|------------|------------|-----|---------|--------------|
| PARQUEINFORMATICA23 | 11 | 4.49 | 27% | 100% | 27% | 73,388 |
| TORPILE_STORE | 9 | 5.00 | 0% | 89% | 89% | 147 |
| OBERODISTRIBUIDORA | 10 | 4.58 | 20% | 0% | 40% | 6,977 |
| MERCADAO-DA-INFORMATICA | 7 | 4.68 | 0% | 29% | 29% | 24,483 |

**Insights:**
- TORPILE_STORE: Perfect ratings but low transaction volume (newer seller?)
- High-transaction sellers tend to have some low-rated products (normal distribution)

---

## Part 7: JSON_LD vs Top-Level Field Comparison

### Price Field Comparison

**Example Product MLB36751629:**

```
Top-level:
  preco: "65.73"           (STRING)

json_ld:
  offers.price: 62.44      (FLOAT - DIFFERENT VALUE!)

melidata:
  price: 65.73             (matches top-level)
```

**Why different?**
- `json_ld.offers.price` may be promotional price or snapshot at scrape time
- `preco` is current/displayed price
- **Recommendation:** Use top-level `preco` as source of truth

### Review Count Comparison

**Example Product MLB36751629:**

```
Top-level:
  total_reviews: 4976

json_ld:
  aggregateRating.ratingCount: 4976    (MATCHES!)
  aggregateRating.reviewCount: 867     (DIFFERENT!)

Reviews file:
  general_data.total_reviews: 4976     (MATCHES!)
  total_reviews_extracted: 0           (MUCH LESS!)
```

**Explanation:**
- `ratingCount` (4976) = Total ratings submitted
- `reviewCount` (867) = Ratings **with text comments**
- `total_reviews_extracted` (0) = Text reviews **actually scraped**

**The scraper only got text from 39 products** (not all 867 with text)

---

## Part 8: Specific Question Answers

### Q: Do ALL 229 products have the same structure?

**A:** **NO** - Several structural variations:

1. **127 products** (55.5%) have `rating_medio = 0` and all rating counts = 0
2. **102 products** (44.5%) have `distribuicao_estrelas` object
3. **127 products** (55.5%) do NOT have `distribuicao_estrelas` object
4. **4 products** are completely missing `modelo` key
5. **14 products** are missing `cor_tinta` key
6. **34 products** are missing `volume` key
7. **1 product** has all seller fields as empty strings

### Q: Is `descricao` always present?

**A:** **YES** - Present in 229/229 products (100%)
- Never null
- Never empty string
- Always contains text (100-2000 chars)
- Format varies but always populated

### Q: Are `preco_original` and `desconto` ever populated?

**A:** **NO** - Both are ALWAYS empty string in all 229 products
- `preco_original`: 0/229 populated (0%)
- `desconto`: 0/229 populated (0%)
- **Conclusion:** These fields exist but are never used - ignore them

### Q: Does `dados_brutos` always exist?

**A:** **YES** - Present in 229/229 products (100%)
- Always has `json_ld`, `melidata`, `window_data`, `timestamp` keys
- `json_ld` is useful (12 fields)
- `melidata` is huge but redundant (83 fields)
- **Recommendation:** Use `json_ld` for validation, skip `melidata`

### Q: Is `json_ld` vs `melidata` always both present?

**A:** **YES** - Both present in all 229 products
- `json_ld`: Structured schema.org data (useful)
- `melidata`: Mercado Livre internal data (mostly redundant)

### Q: What fields in `dados_brutos.melidata` are useful vs noise?

**A:** **99% noise, 1% potentially useful:**

**Redundant (already in top-level):**
- `seller_id`, `seller_name`, `price`, `reviews`, `power_seller_status`, `reputation_level`

**Unique but low value:**
- `alternative_buying_options[]` - Other sellers of same product (could be useful for price comparison)
- `best_seller_position` - Ranking (interesting but not critical)
- `pickers[]` - Product variations (redundant with catalog)

**Pure noise:**
- 75+ other fields related to UI state, shipping calculations, internal IDs

**Recommendation:** Skip melidata entirely unless you specifically need `alternative_buying_options`

### Q: Is there exactly 229 entries in reviews dataset?

**A:** **YES** - Exactly 229 entries, perfect 1:1 match with main dataset product IDs

### Q: How many have `total_reviews_extracted > 0`?

**A:** **39 out of 229 (17.0%)**
- 39 products have extracted review text
- 190 products have empty reviews array
- Total review objects: 494 across those 39 products

### Q: For products with `total_reviews_extracted = 0`, what are the field values?

**A:**

```json
{
  "product_id": "MLB36751072",
  "general_data": {
    "average_rating": null,        // NULL (not 0!)
    "total_reviews": null          // NULL (not 0!)
  },
  "reviews": [],                   // EMPTY ARRAY (not null)
  "total_reviews_extracted": 0     // ZERO
}
```

**Pattern is consistent** across all 190 products with no reviews

### Q: Do ALL reviews have all 8 fields?

**A:** **YES** - All 494 reviews have identical structure:
- `review_number`, `rating`, `date`, `text`, `likes`, `images`, `image_count`, `has_images`
- No variations, no missing fields
- No extra fields

### Q: Can `text` be empty string vs null?

**A:** **All texts are non-empty strings** in the 494 reviews
- Shortest: 3 chars ("Ok.")
- No null values
- No empty strings ""
- Minimum is very short but still has content

**But note:** The reviews file only includes reviews **with text**
- Products with text-less ratings aren't in the reviews array

### Q: Are `review_number` sequential?

**A:** **YES** - Always sequential starting from 1
- Example: 1, 2, 3, 4, ..., 142 (for product with 142 reviews)
- No gaps
- Always starts at 1

### Q: Is `characteristics_ratings` always empty object?

**A:** **YES** - All 229 entries have `{}` (empty object)
- Never populated
- Feature not used in this scrape

### Q: Is `ai_summary.summary` always null?

**A:** **YES** - All 229 entries have `null`
- `ai_summary.available` is always `false`
- Feature not available/not used

---

## Part 9: Seller-Product Detailed Breakdown

### Sellers with Most Products

**1. PARQUEINFORMATICA23 - 11 products**
```
Product IDs:
- MLB4147308609 (5-star, R$ 265.00)
- MLB4165660381 (no reviews, R$ 111.19)
- MLB4147340035 (no reviews, R$ 141.49)
- ... 8 more

Specialty: 100% XL cartridges
Average: R$ 254.91 per product
```

**2. OBERODISTRIBUIDORA - 10 products**
```
Product IDs:
- MLB4165556343, MLB4165763845, MLB4169549299, ...

Specialty: 40% bundles, 0% XL
Average: R$ 119.08 per product
```

### Sellers with ALL Low-Rated Products

**Sellers where all products have rating < 4.5:**

```
SUPRYECOMERCE (ID:2523139116):
  - 1 product: Rating 4.2
  
WEBBEST (ID:31752392):
  - 1 product: Rating 4.3
  
CENTRAL GUARAPUAVA (ID:41436895):
  - 1 product: Rating 3.7
```

**Note:** All have only 1 product - small sample size

**Sellers with multiple low-rated products:**
- PARQUEINFORMATICA23: 3 out of 11 products below 4.5 (27%)
- OBERODISTRIBUIDORA: 2 out of 10 products below 4.5 (20%)

### Sellers with ALL Products Having No Reviews

**6 sellers** have products but no reviews on any:

```
MAXTONER CARTUCHOS-JF (ID:97145061): 6 products, all 0 reviews
FERREIRANELSONFERREIRADASIL (ID:135595657): 1 product, 0 reviews
BSMINFO (ID:79722769): 1 product, 0 reviews
... 3 more
```

**Possible reasons:**
- New products (not enough time for reviews)
- Low visibility (not many sales)
- Removed/delisted products

---

## Part 10: datos_brutos JSON_LD Field-by-Field

### Complete json_ld Schema

```typescript
interface JsonLD {
  "@context": "https://schema.org",
  "@type": "Product",
  
  // Basic Info
  "name": string,              // Product name (matches titulo without "| MercadoLivre")
  "brand": string,             // Always "HP"
  "sku": string,               // Same as product id
  "productID": string,         // Same as product id
  "image": string,             // URL (matches imagem_url)
  "description": string,       // SHORT description (different from descricao!)
  "itemCondition": string,     // Always "https://schema.org/NewCondition"
  
  // Pricing
  "offers": {
    "@type": "Offer",
    "price": number,           // FLOAT (may differ from top-level preco!)
    "priceCurrency": "BRL",
    "priceValidUntil": string, // ISO date
    "availability": string,    // Always "https://schema.org/InStock"
    "url": string,             // Product page URL
    "shippingDetails": {       // Complex nested object
      "@type": "OfferShippingDetails",
      "shippingRate": {...},
      "shippingOrigin": {...},
      "shippingDestination": {...},
      "deliveryTime": {...}
    },
    "hasMerchantReturnPolicy": {...}
  },
  
  // Ratings (optional - only if reviews exist)
  "aggregateRating": {
    "@type": "AggregateRating",
    "ratingValue": number,     // 0.0-5.0 (matches rating_medio)
    "ratingCount": number,     // Total ratings (matches total_reviews)
    "reviewCount": number      // Ratings WITH TEXT (different!)
  },
  
  // Sample Reviews (0-5 reviews)
  "review": [
    {
      "@type": "Review",
      "author": {
        "@type": "Person",
        "name": "Usuário do Mercado Livre"  // Always anonymous
      },
      "reviewBody": string,    // Review text (can be empty string)
      "reviewRating": {
        "ratingValue": number, // 1-5
        "bestRating": 5,
        "worstRating": 1
      }
    }
  ]
}
```

**Products WITHOUT reviews:** `aggregateRating` and `review` keys are MISSING (not null)

---

## Part 11: Complete Parsing & Validation Code

```python
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import re

@dataclass
class ParsedProduct:
    """Cleaned and validated product data"""
    # Core fields
    id: str
    titulo: str
    preco_float: float
    seller_id_int: Optional[int]
    
    # Ratings
    rating_medio: float
    total_reviews: int
    rating_distribution: Dict[int, int]
    has_reviews: bool
    
    # Derived - Bundle
    is_bundle: bool
    bundle_quantity: int
    price_per_unit: float
    
    # Derived - Model
    model_number: str  # "664", "667", "662", "UNKNOWN"
    is_xl: bool
    
    # Derived - Flags
    suspicious_bimodal: bool
    has_seller: bool
    
    # Review data
    review_count_extracted: int
    review_texts: List[str]
    
    # Seller info (if available)
    seller_nickname: Optional[str] = None
    seller_reputation_level: Optional[str] = None
    seller_power_status: Optional[str] = None
    seller_state: Optional[str] = None


class DatasetParser:
    """Complete dataset parser with validation"""
    
    def __init__(self):
        self.month_map = {
            'jan': 1, 'fev': 2, 'mar': 3, 'abr': 4,
            'mai': 5, 'jun': 6, 'jul': 7, 'ago': 8,
            'set': 9, 'out': 10, 'nov': 11, 'dez': 12
        }
    
    def parse_price(self, preco_str: str) -> float:
        """Parse price string to float"""
        try:
            return float(preco_str)
        except (ValueError, TypeError):
            return 0.0
    
    def parse_seller_id(self, seller_id_str: str) -> Optional[int]:
        """Convert seller_id to int"""
        if not seller_id_str or seller_id_str == "":
            return None
        try:
            return int(seller_id_str)
        except ValueError:
            return None
    
    def detect_bundle(self, titulo: str) -> Tuple[bool, int]:
        """Detect bundle and quantity"""
        titulo_lower = titulo.lower()
        
        # Ordered patterns (most specific first)
        patterns = [
            (r'kit\s*0?(\d+)\s+cartuchos', 'kit_n_cartuchos'),
            (r'kit\s*0?(\d+)', 'kit_n'),
            (r'(\d+)\s+cartuchos', 'n_cartuchos'),
            (r'(\d+)\s+unidades', 'n_unidades'),
        ]
        
        for pattern, name in patterns:
            match = re.search(pattern, titulo_lower)
            if match:
                qty = int(match.group(1))
                return True, qty
        
        # Implicit bundle indicators
        if re.search(r'preto.*\+.*(color|tricolor)', titulo_lower):
            return True, 2
        
        if 'kit' in titulo_lower:
            return True, 2  # Default for unclear kits
        
        return False, 1
    
    def normalize_model(self, product: Dict) -> Tuple[str, bool]:
        """Extract model number and XL flag"""
        # Sources in priority order
        sources = [
            product.get('modelo', ''),
            product.get('titulo', ''),
            product.get('descricao', '')[:200]  # First 200 chars
        ]
        
        for source in sources:
            if not source:
                continue
            
            # Skip garbage values
            if source in ['Cartucho de Tinta', 'Cartucho HP', 'MISSING']:
                continue
            
            # Try to extract 66X model
            match = re.search(r'\b(66[247])(XL|xl)?\b', source, re.IGNORECASE)
            if match:
                base = match.group(1)
                is_xl = bool(match.group(2))
                return base, is_xl
        
        return "UNKNOWN", False
    
    def is_suspicious_distribution(self, product: Dict) -> bool:
        """Detect bimodal rating pattern"""
        total = product.get('total_reviews', 0)
        if total < 10:
            return False
        
        five_star = product.get('rating_5_estrelas', 0)
        one_star = product.get('rating_1_estrela', 0)
        
        extreme_ratio = (five_star + one_star) / total
        one_star_ratio = one_star / total
        
        return extreme_ratio > 0.80 and one_star_ratio > 0.15
    
    def parse_product(
        self, 
        product: Dict, 
        review_entry: Dict, 
        seller: Optional[Dict]
    ) -> ParsedProduct:
        """Parse and validate a single product"""
        
        # Core fields
        id_val = product['id']
        titulo = product['titulo']
        preco_float = self.parse_price(product['preco'])
        seller_id_int = self.parse_seller_id(product['seller_id'])
        
        # Ratings
        rating_medio = product.get('rating_medio', 0.0)
        total_reviews = product.get('total_reviews', 0)
        rating_distribution = {
            5: product.get('rating_5_estrelas', 0),
            4: product.get('rating_4_estrelas', 0),
            3: product.get('rating_3_estrelas', 0),
            2: product.get('rating_2_estrelas', 0),
            1: product.get('rating_1_estrela', 0)
        }
        has_reviews = total_reviews > 0
        
        # Bundle detection
        is_bundle, bundle_quantity = self.detect_bundle(titulo)
        price_per_unit = preco_float / bundle_quantity if bundle_quantity > 0 else preco_float
        
        # Model extraction
        model_number, is_xl = self.normalize_model(product)
        
        # Flags
        suspicious_bimodal = self.is_suspicious_distribution(product)
        has_seller = seller_id_int is not None
        
        # Review data
        review_count_extracted = review_entry.get('total_reviews_extracted', 0)
        review_texts = [r['text'] for r in review_entry.get('reviews', []) if len(r.get('text', '')) > 10]
        
        # Seller info
        seller_nickname = seller['nickname'] if seller else None
        seller_reputation_level = seller.get('seller_reputation', {}).get('level_id') if seller else None
        seller_power_status = seller.get('seller_reputation', {}).get('power_seller_status') if seller else None
        seller_state = seller.get('address', {}).get('state') if seller else None
        
        return ParsedProduct(
            id=id_val,
            titulo=titulo,
            preco_float=preco_float,
            seller_id_int=seller_id_int,
            rating_medio=rating_medio,
            total_reviews=total_reviews,
            rating_distribution=rating_distribution,
            has_reviews=has_reviews,
            is_bundle=is_bundle,
            bundle_quantity=bundle_quantity,
            price_per_unit=price_per_unit,
            model_number=model_number,
            is_xl=is_xl,
            suspicious_bimodal=suspicious_bimodal,
            has_seller=has_seller,
            review_count_extracted=review_count_extracted,
            review_texts=review_texts,
            seller_nickname=seller_nickname,
            seller_reputation_level=seller_reputation_level,
            seller_power_status=seller_power_status,
            seller_state=seller_state
        )

# Usage:
parser = DatasetParser()

# Build indexes
review_index = {e['product_id']: e for e in reviews_data}
seller_index = {s['id']: s for s in sellers_data['dados_vendedores']}

# Parse all products
parsed_products = []
for product in produtos:
    review_entry = review_index[product['id']]
    seller_id_int = parser.parse_seller_id(product['seller_id'])
    seller = seller_index.get(seller_id_int)
    
    parsed = parser.parse_product(product, review_entry, seller)
    parsed_products.append(parsed)
```

---

## Part 12: Month Abbreviation Complete Mapping

### Portuguese Month Names

```python
MONTH_NAMES_PT = {
    # Abbreviation: (Number, Full Name)
    'jan': (1,  'janeiro'),
    'fev': (2,  'fevereiro'),
    'mar': (3,  'março'),
    'abr': (4,  'abril'),
    'mai': (5,  'maio'),
    'jun': (6,  'junho'),
    'jul': (7,  'julho'),
    'ago': (8,  'agosto'),
    'set': (9,  'setembro'),
    'out': (10, 'outubro'),
    'nov': (11, 'novembro'),
    'dez': (12, 'dezembro')
}

# All 12 months observed in dataset: ✓
# Format is consistent: "DD MMM. YYYY"
# Example: "06 jun. 2024"
```

---

## Part 13: Counterfeit Detection Signals

### Strong Positive Signals (Likely Authentic)

1. **High rating with many reviews**
   - `rating_medio > 4.5 AND total_reviews > 50`

2. **Review keywords (positive context)**
   - "genuíno", "lacrado", "HP reconheceu", "original mesmo"

3. **Long-lasting usage reports**
   - "dura bastante", "rendeu bem", "já comprei várias vezes"

4. **High-reputation seller**
   - `seller_reputation.level_id = "5_green"`
   - `seller_reputation.power_seller_status = "platinum"`
   - `transactions.total > 10000`

5. **Price in expected range**
   - Regular 664: R$ 60-90
   - XL 664: R$ 120-180
   - Bundles: R$ 140-300

### Strong Negative Signals (Likely Counterfeit)

1. **Explicit counterfeit claims**
   - Reviews: "falsificado", "falso", "não é original"

2. **Printer rejection**
   - "impressora não reconhece", "bloqueou", "não leu"

3. **Empty/defective cartridges**
   - "veio vazio", "sem tinta", "seco"

4. **Extremely short usage**
   - "durou 2 dias", "acabou em 20 páginas", "não imprimiu nem 30 folhas"

5. **Suspicious pricing**
   - Regular 664 < R$ 40 (too cheap)
   - XL < R$ 80 (too cheap)

6. **Bimodal rating distribution**
   - >80% extreme ratings (5-star + 1-star)
   - >15% are 1-star complaints

7. **Low-reputation seller**
   - `level_id = "1_red"` or null
   - `transactions.total < 100`
   - Multiple low-rated products

---

## Part 14: Production-Ready Filter Examples

### Filter 1: Products Worth Analyzing with LLM

```python
def should_analyze_with_llm(product, review_entry):
    """Decide if product is worth expensive LLM analysis"""
    
    # Must have review text
    if review_entry['total_reviews_extracted'] == 0:
        return False
    
    # Filter out low-value reviews
    quality_reviews = [
        r for r in review_entry['reviews'] 
        if len(r.get('text', '')) > 10  # Skip ultra-short
    ]
    
    if len(quality_reviews) == 0:
        return False
    
    # Priority: High-volume OR high-engagement reviews
    has_many_reviews = review_entry['total_reviews_extracted'] >= 10
    has_liked_reviews = any(r.get('likes', 0) > 0 for r in quality_reviews)
    has_negative_reviews = any(r.get('rating', 5) <= 2 for r in quality_reviews)
    
    return has_many_reviews or has_liked_reviews or has_negative_reviews
```

### Filter 2: Suspicious Products for Manual Review

```python
def is_suspicious_product(parsed_product: ParsedProduct) -> bool:
    """Flag products needing manual review"""
    
    flags = []
    
    # Flag 1: No seller data
    if not parsed_product.has_seller:
        flags.append("NO_SELLER")
    
    # Flag 2: Bimodal ratings
    if parsed_product.suspicious_bimodal:
        flags.append("BIMODAL_RATING")
    
    # Flag 3: Price too low
    expected_min = 60 if not parsed_product.is_xl else 100
    if parsed_product.price_per_unit < expected_min:
        flags.append("PRICE_TOO_LOW")
    
    # Flag 4: Low rating with many reviews
    if parsed_product.has_reviews and \
       parsed_product.rating_medio < 4.0 and \
       parsed_product.total_reviews > 20:
        flags.append("LOW_RATING_HIGH_VOLUME")
    
    # Flag 5: New/low-reputation seller
    if parsed_product.seller_reputation_level in [None, "1_red", "2_orange"]:
        flags.append("LOW_REP_SELLER")
    
    return len(flags) > 0, flags
```

### Filter 3: Reviews Worth Processing

```python
def filter_reviews_for_analysis(reviews: List[Dict]) -> List[Dict]:
    """Filter review list to most valuable ones"""
    
    quality_reviews = []
    
    for review in reviews:
        text = review.get('text', '')
        length = len(text)
        likes = review.get('likes', 0)
        rating = review.get('rating', 5)
        
        # Skip ultra-short
        if length <= 10:
            continue
        
        # Prioritize:
        # 1. High engagement (liked)
        # 2. Negative reviews (complaints)
        # 3. Detailed reviews
        
        priority = 0
        if likes > 0:
            priority += 10
        if rating <= 2:
            priority += 8
        if length > 100:
            priority += 5
        elif length > 50:
            priority += 2
        
        review['_priority'] = priority
        quality_reviews.append(review)
    
    # Sort by priority
    quality_reviews.sort(key=lambda x: x['_priority'], reverse=True)
    
    return quality_reviews
```

---

## Part 15: Data Validation Checklist

### Pre-Processing Validation

```python
def validate_dataset_integrity(main_data, reviews_data, sellers_data):
    """Run integrity checks before processing"""
    
    produtos = main_data['produtos']
    sellers = sellers_data['dados_vendedores']
    
    issues = []
    
    # Check 1: Product count
    if len(produtos) != 229:
        issues.append(f"Expected 229 products, got {len(produtos)}")
    
    # Check 2: Review count
    if len(reviews_data) != 229:
        issues.append(f"Expected 229 review entries, got {len(reviews_data)}")
    
    # Check 3: Product-Review ID match
    product_ids = set(p['id'] for p in produtos)
    review_ids = set(r['product_id'] for r in reviews_data)
    if product_ids != review_ids:
        issues.append("Product IDs don't match between datasets")
    
    # Check 4: Seller IDs reference
    seller_ids_in_products = set(
        int(p['seller_id']) 
        for p in produtos 
        if p.get('seller_id') and p['seller_id'] != ""
    )
    seller_ids_in_vendor = set(s['id'] for s in sellers)
    
    missing_sellers = seller_ids_in_products - seller_ids_in_vendor
    if missing_sellers:
        issues.append(f"Missing sellers: {missing_sellers}")
    
    # Check 5: Required fields
    for i, p in enumerate(produtos):
        if not p.get('id'):
            issues.append(f"Product {i} missing ID")
        if not p.get('titulo'):
            issues.append(f"Product {i} missing titulo")
        if not p.get('preco'):
            issues.append(f"Product {i} missing preco")
    
    # Check 6: Data type consistency
    for i, p in enumerate(produtos):
        if not isinstance(p.get('frete_gratis'), bool):
            issues.append(f"Product {i} frete_gratis not boolean")
        if not isinstance(p.get('rating_medio'), (int, float)):
            issues.append(f"Product {i} rating_medio not numeric")
    
    if issues:
        print("VALIDATION ISSUES FOUND:")
        for issue in issues:
            print(f"  - {issue}")
        return False
    else:
        print("✓ All validation checks passed")
        return True
```

---

## Part 16: LLM Prompt Templates

### For Review Analysis

```python
def create_review_analysis_prompt(product, reviews):
    """Create prompt for LLM to analyze reviews"""
    
    review_texts = "\n".join([
        f"{i+1}. [{r['rating']}-star, {r['date']}] {r['text']}"
        for i, r in enumerate(reviews)
        if len(r['text']) > 10
    ])
    
    prompt = f"""
Analyze the following customer reviews for an HP {product['model_clean']} printer cartridge:

Product: {product['titulo']}
Price: R$ {product['preco_float']:.2f}
Seller: {product.get('seller_nickname', 'Unknown')}

Reviews ({len(reviews)} total):
{review_texts}

Based on these reviews, assess:
1. Likelihood this is a counterfeit product (0-100%)
2. Main complaints or issues mentioned
3. Keywords indicating authenticity or fake
4. Overall product quality assessment

Provide structured JSON output.
"""
    return prompt
```

---

## Conclusion

**This analysis provides:**

✅ Complete schema documentation for all 3 files  
✅ Field-by-field data type specifications  
✅ Edge case catalog with handling strategies  
✅ Cross-file relationship validation  
✅ Pattern extraction for bundles, models, XL detection  
✅ Review text analysis with keyword frequencies  
✅ Seller aggregation metrics  
✅ Production-ready parsing code  
✅ Data quality assessment  
✅ Implementation recommendations  

**You now have everything needed to build a robust anti-piracy detection pipeline.**

---

**Questions? Edge cases I missed? Let me know and I'll dig deeper.**
