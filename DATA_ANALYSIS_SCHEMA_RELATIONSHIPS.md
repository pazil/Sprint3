# Cross-Reference Analysis of JSON Files

## Executive Summary
This document provides a comprehensive analysis of three JSON files containing MercadoLivre marketplace data for HP 664 cartridges. The files contain product listings, reviews, and seller information with clear relational keys for data integration.

---

## File Overview

### 1. **664_dataset_javascript_sem_reviews_20250930_012112.json**
- **Purpose**: Main product dataset with detailed product information
- **Size**: 105,216 lines
- **Structure**: Root object with metadata + array of products
- **Total Products**: 229

### 2. **664_reviews.json**
- **Purpose**: Product reviews and ratings data
- **Size**: 8,874 lines
- **Structure**: Array of review objects
- **Contains**: 39 products with actual reviews extracted

### 3. **664_vendedores.json**
- **Purpose**: Seller/vendor information
- **Size**: 2,396 lines
- **Structure**: Root object with "dados_vendedores" array
- **Contains**: Seller profiles, reputation, and transaction history

---

## Schema Analysis

### File 1: Main Product Dataset (664_dataset_javascript_sem_reviews_*.json)

#### Root Level Structure:
```json
{
  "query": "cartucho hp 664",
  "timestamp": "20250930_012112",
  "total_produtos": 229,
  "produtos": [...]
}
```

#### Product Object Schema:
```javascript
{
  // PRIMARY KEY - Links to reviews.json
  "id": "MLB3159055901",
  
  // FOREIGN KEY - Links to vendedores.json
  "seller_id": "677845209",
  
  // Product Information
  "titulo": "Kit Cartuchos Originais Hp 664...",
  "link": "https://produto.mercadolivre.com.br/...",
  "preco": "209.99",
  "preco_original": "",
  "desconto": "",
  
  // Seller Summary (redundant with vendedores.json)
  "vendedor": "YELLOWCELL ACESSORIOS",
  "reputation_level": "5_green",
  "power_seller_status": "gold",
  
  // Review Summary Statistics
  "rating_medio": 4.7,
  "total_reviews": 43,
  "rating_5_estrelas": 37,
  "rating_4_estrelas": 1,
  "rating_3_estrelas": 1,
  "rating_2_estrelas": 1,
  "rating_1_estrela": 1,
  "reviews_com_texto": 0,
  "reviews_com_imagens": 0,
  
  // Product Details
  "imagem_url": "https://...",
  "frete_gratis": true,
  "categoria": "",
  "marca": "HP",
  "condicao": "Novo",
  "disponibilidade": "https://schema.org/InStock",
  
  // Empty array - detailed reviews are in reviews.json
  "reviews_detalhadas": [],
  
  // Raw data from scraping
  "dados_brutos": {
    "json_ld": {...},  // Schema.org structured data
    "melidata": {...}  // MercadoLivre internal data
  }
}
```

---

### File 2: Reviews Data (664_reviews.json)

#### Structure:
```javascript
[
  {
    // PRIMARY KEY - Links back to produtos[].id
    "product_id": "MLB3159055901",
    
    "extraction_timestamp": "2025-09-30T10:15:10.033871",
    "url": "https://www.mercadolivre.com.br/noindex/catalog/reviews/...",
    
    // General review statistics
    "general_data": {
      "average_rating": 4.7,
      "total_reviews": 43
    },
    
    // AI-generated summary (mostly null in this dataset)
    "ai_summary": {
      "summary": null,
      "likes": 0,
      "available": false
    },
    
    // Product characteristics ratings (empty in this dataset)
    "characteristics_ratings": {},
    
    // Detailed individual reviews
    "reviews": [
      {
        "review_number": 1,
        "rating": 5,
        "date": "06 jun. 2024",
        "text": "Ótimo produto.",
        "likes": 0,
        "images": [],
        "image_count": 0,
        "has_images": false
      },
      {
        "review_number": 2,
        "rating": 5,
        "date": "18 jan. 2024",
        "text": "Bom+++++++++++++++.",
        "likes": 0,
        "images": [],
        "image_count": 0,
        "has_images": false
      }
      // ... more reviews
    ],
    
    "total_reviews_extracted": 3
  }
]
```

**Notes:**
- Most products (190 out of 229) have empty reviews arrays
- 39 products have actual review data extracted
- Each review includes: rating (1-5), date, text, likes, and image indicators

---

### File 3: Seller Data (664_vendedores.json)

#### Structure:
```javascript
{
  "dados_vendedores": [
    {
      // PRIMARY KEY - Links back to produtos[].seller_id
      "id": 677845209,
      
      // Seller Profile
      "nickname": "YELLOWCELL ACESSORIOS",
      "country_id": "BR",
      "address": {
        "city": "São Paulo",
        "state": "BR-SP"
      },
      
      // Seller Classification
      "user_type": "normal",  // or "brand"
      "site_id": "MLB",
      
      // Profile URL
      "permalink": "http://perfil.mercadolivre.com.br/YELLOWCELL+ACESSORIOS",
      
      // Reputation Data
      "seller_reputation": {
        "level_id": "5_green",
        "power_seller_status": "gold",  // or "platinum"
        "transactions": {
          "period": "historic",
          "total": 11918
        }
      },
      
      // Status
      "status": {
        "site_status": "active"
      }
    }
  ]
}
```

**Seller Reputation Levels:**
- `level_id`: "5_green" (best), "4_green", etc.
- `power_seller_status`: "platinum" > "gold" > lower tiers

---

## Relationship Mapping

### Entity Relationship Diagram (ERD)

```
┌─────────────────────────────────┐
│      MAIN PRODUCT DATASET       │
│  (664_dataset_javascript_...)   │
├─────────────────────────────────┤
│ PK: id (string)                 │
│ FK: seller_id (string)          │
│ - titulo                        │
│ - preco                         │
│ - rating_medio                  │
│ - total_reviews                 │
│ - marca                         │
│ - imagem_url                    │
│ - frete_gratis                  │
│ - dados_brutos                  │
└──────┬──────────────────────────┘
       │                      │
       │ 1:1                  │ N:1
       │                      │
       ▼                      ▼
┌──────────────────┐   ┌──────────────────┐
│   REVIEWS        │   │   SELLERS        │
│ (664_reviews)    │   │ (664_vendedores) │
├──────────────────┤   ├──────────────────┤
│ PK: product_id   │   │ PK: id           │
│ - general_data   │   │ - nickname       │
│ - reviews[]      │   │ - address        │
│ - ai_summary     │   │ - user_type      │
└──────────────────┘   │ - reputation     │
                       │ - status         │
                       └──────────────────┘
```

### Relationship Keys

| Source File | Key Field | Target File | Target Field | Relationship Type |
|-------------|-----------|-------------|--------------|-------------------|
| Main Dataset | `id` | Reviews | `product_id` | 1:1 |
| Main Dataset | `seller_id` | Vendors | `id` | N:1 |

---

## Key Value Pair Correlations

### 1. **Product ID Linking** (Main ↔ Reviews)

**Main Dataset:**
```javascript
"id": "MLB3159055901"  // Product identifier
```

**Reviews File:**
```javascript
"product_id": "MLB3159055901"  // Same identifier
```

**Relationship:** One-to-one mapping. Each product can have one reviews object (though many have empty review arrays).

---

### 2. **Seller ID Linking** (Main ↔ Vendors)

**Main Dataset:**
```javascript
"seller_id": "677845209"  // Stored as string
```

**Vendors File:**
```javascript
"id": 677845209  // Stored as integer
```

**⚠️ IMPORTANT:** Data type mismatch - string vs integer. Must convert when linking:
- Convert vendor ID to string: `String(vendor.id)`
- Or convert seller_id to int: `parseInt(product.seller_id)`

**Relationship:** Many-to-one. Multiple products can share the same seller.

---

### 3. **Redundant Data Fields**

Some fields appear in multiple files - these should be validated for consistency:

| Field | Main Dataset | Reviews | Vendors | Notes |
|-------|--------------|---------|---------|-------|
| `average_rating` | `rating_medio` | `general_data.average_rating` | - | Should match |
| `total_reviews` | `total_reviews` | `general_data.total_reviews` | - | Should match |
| `reputation_level` | `reputation_level` | - | `seller_reputation.level_id` | Should match |
| `power_seller_status` | `power_seller_status` | - | `seller_reputation.power_seller_status` | Should match |
| `seller_name` | `vendedor` | - | `nickname` | Should match |

---

## Data Quality Observations

### Reviews File:
- **Total products in reviews file:** 229 (same as main dataset)
- **Products with extracted reviews:** 39 (17%)
- **Products with empty reviews:** 190 (83%)
- **Reason:** Some products may not have reviews available or extraction failed

### Seller Data:
- All sellers in the dataset appear to be active (`site_status: "active"`)
- Sellers range from "gold" to "platinum" power seller status
- Geographic concentration: Mostly São Paulo, some Rio de Janeiro and other cities

### Data Consistency:
✅ All product IDs in main dataset appear to have corresponding entries in reviews file  
✅ Review statistics in main dataset match the `general_data` in reviews file  
⚠️ Seller ID data type inconsistency (string vs integer)  
✅ Timestamps indicate data was collected on September 30, 2025

---

## Code Implementation Guidelines

### Recommended Data Structures

#### JavaScript/TypeScript:

```javascript
// Type Definitions
interface Product {
  id: string;
  seller_id: string;
  titulo: string;
  preco: string;
  rating_medio: number;
  total_reviews: number;
  // ... other fields
}

interface Review {
  product_id: string;
  general_data: {
    average_rating: number;
    total_reviews: number;
  };
  reviews: Array<{
    review_number: number;
    rating: number;
    date: string;
    text: string;
    likes: number;
  }>;
}

interface Seller {
  id: number;
  nickname: string;
  seller_reputation: {
    level_id: string;
    power_seller_status: string;
    transactions: {
      total: number;
    };
  };
  // ... other fields
}

// Indexing for Fast Lookup
const reviewsMap = new Map(
  reviews.map(r => [r.product_id, r])
);

const sellersMap = new Map(
  sellers.dados_vendedores.map(s => [String(s.id), s])
);

// Joining Data
function enrichProduct(product) {
  return {
    ...product,
    detailed_reviews: reviewsMap.get(product.id)?.reviews || [],
    seller_info: sellersMap.get(product.seller_id)
  };
}

const enrichedProducts = mainDataset.produtos.map(enrichProduct);
```

---

## Linking Strategy for Full Relations

### Step 1: Load and Index

```javascript
// Load all three files
const mainData = JSON.parse(fs.readFileSync('664_dataset_*.json', 'utf8'));
const reviewsData = JSON.parse(fs.readFileSync('664_reviews.json', 'utf8'));
const sellersData = JSON.parse(fs.readFileSync('664_vendedores.json', 'utf8'));

// Create indexes
const reviewsByProductId = indexBy(reviewsData, 'product_id');
const sellersByIdStr = indexBy(
  sellersData.dados_vendedores, 
  seller => String(seller.id)
);
```

### Step 2: Validate Relationships

```javascript
// Check all products have corresponding reviews entry
const missingReviews = mainData.produtos.filter(
  p => !reviewsByProductId.has(p.id)
);

// Check all sellers exist
const missingSellers = mainData.produtos.filter(
  p => !sellersByIdStr.has(p.seller_id)
);

// Check for orphaned reviews (reviews without products)
const orphanedReviews = reviewsData.filter(
  r => !mainData.produtos.find(p => p.id === r.product_id)
);
```

### Step 3: Create Unified Dataset

```javascript
const unifiedDataset = mainData.produtos.map(product => {
  const reviews = reviewsByProductId.get(product.id);
  const seller = sellersByIdStr.get(product.seller_id);
  
  return {
    // Product info
    product_id: product.id,
    title: product.titulo,
    price: parseFloat(product.preco),
    brand: product.marca,
    free_shipping: product.frete_gratis,
    image_url: product.imagem_url,
    link: product.link,
    
    // Reviews aggregated
    rating_average: product.rating_medio,
    rating_count: product.total_reviews,
    rating_distribution: {
      5: product.rating_5_estrelas,
      4: product.rating_4_estrelas,
      3: product.rating_3_estrelas,
      2: product.rating_2_estrelas,
      1: product.rating_1_estrela
    },
    
    // Detailed reviews
    reviews: reviews?.reviews || [],
    reviews_extracted: reviews?.total_reviews_extracted || 0,
    
    // Seller info
    seller: {
      id: seller?.id,
      name: seller?.nickname,
      city: seller?.address?.city,
      state: seller?.address?.state,
      reputation: seller?.seller_reputation?.level_id,
      power_seller: seller?.seller_reputation?.power_seller_status,
      total_transactions: seller?.seller_reputation?.transactions?.total
    }
  };
});
```

---

## Summary of Relationships

1. **Product ← Review**: Use `product.id === review.product_id` (1:1)
2. **Product ← Seller**: Use `String(seller.id) === product.seller_id` (N:1)
3. **Review Statistics**: Validate `product.rating_medio === review.general_data.average_rating`
4. **Seller Reputation**: Validate `product.power_seller_status === seller.seller_reputation.power_seller_status`

---

## Next Steps for Implementation

1. ✅ Schema mapping completed
2. ✅ Relationship keys identified
3. 🔄 **Build indexing functions** for fast lookups
4. 🔄 **Create unified data structure** with all relations
5. 🔄 **Implement validation checks** for data integrity
6. 🔄 **Handle missing/null data** gracefully
7. 🔄 **Add data enrichment** (calculated fields, derived metrics)

---

**Generated:** September 30, 2025  
**Data Source:** MercadoLivre HP 664 Cartridge Dataset  
**Total Products:** 229  
**Total Sellers:** Variable count  
**Collection Date:** September 30, 2025
