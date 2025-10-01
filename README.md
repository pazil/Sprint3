# 🛡️ Sistema de Detecção de Fraude - Cartuchos HP

## 📋 Visão Geral

Este projeto é um sistema de análise de fraude desenvolvido para detectar produtos falsificados de cartuchos de tinta HP no Mercado Livre. O sistema utiliza técnicas de Machine Learning, processamento de dados e análise de preços para identificar anúncios suspeitos.

## 🎯 Objetivo

Desenvolver uma solução que ajude a HP a combater a pirataria de cartuchos de tinta, identificando automaticamente anúncios que podem conter produtos falsificados através da análise de:
- Preços suspeitosamente baixos
- Padrões de vendedores
- Características dos produtos
- Comportamento de mercado

## 🏗️ Arquitetura do Sistema

### 📁 Estrutura do Projeto

```
Front_End_Sprint3/
├── 📊 analise_fraude_hp.ipynb          # Notebook principal de análise
├── 🔧 processamento de datasets/       # Scripts de processamento
│   ├── extrator_openai.py             # Extração de dados com IA
│   └── processar_dataset_bruto.py     # Processamento de datasets
├── 📂 dataset_bruto/                   # Dados brutos coletados
│   ├── *.json                         # Dados de produtos, reviews e vendedores
│   └── llm_analyzed_products_pretty.json
├── 📂 dataset_tratado/                 # Dados processados e enriquecidos
│   ├── dataset_enriquecido_*.csv      # Dataset principal
│   ├── dados_extraidos_ia.json        # Dados extraídos pela IA
│   └── dataset_final_enriquecido.csv  # Dataset final
├── 📂 fornecidos_pela_hp/             # Dados de referência da HP
│   ├── Briefing Anti pirataria FIAP.pdf
│   └── Tabela de Preços Sugeridos.csv
└── 📂 mlruns/                         # Experimentos do MLflow
```

## 🚀 Funcionalidades

### 1. **Coleta e Processamento de Dados**
- Extração automática de dados do Mercado Livre
- Processamento e limpeza de datasets
- Enriquecimento com dados de vendedores e reviews

### 2. **Análise com Inteligência Artificial**
- Extração estruturada de informações usando OpenAI GPT
- Identificação de características dos produtos
- Classificação de tipos de cartuchos e condições

### 3. **Detecção de Fraude**
- Análise de preços suspeitos
- Identificação de padrões de vendedores
- Comparação com preços oficiais HP
- Machine Learning para classificação de risco

### 4. **Monitoramento e Logging**
- MLflow para tracking de experimentos
- Logs detalhados de processamento
- Métricas de performance dos modelos

## 🛠️ Tecnologias Utilizadas

- **Python 3.11+**
- **Pandas** - Manipulação de dados
- **NumPy** - Computação numérica
- **Scikit-learn** - Machine Learning
- **PyCaret** - AutoML
- **MLflow** - Experiment tracking
- **OpenAI API** - Extração de dados com IA
- **Jupyter Notebook** - Análise interativa

## 📦 Instalação

### Pré-requisitos
- Python 3.11 ou superior
- Conta OpenAI com API key

### Passos para instalação

1. **Clone o repositório**
```bash
git clone <url-do-repositorio>
cd Front_End_Sprint3
```

2. **Crie um ambiente virtual**
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

3. **Instale as dependências**
```bash
pip install -r requirements.txt
```

4. **Configure as variáveis de ambiente**
```bash
# Crie um arquivo .env na raiz do projeto
echo "OPENAI_API_KEY=sua_api_key_aqui" > .env
```

## 🎮 Como Usar

### 1. **Processamento de Dados Brutos**
```bash
python "processamento de datasets/processar_dataset_bruto.py"
```

### 2. **Extração de Dados com IA**
```bash
python "processamento de datasets/extrator_openai.py"
```

### 3. **Análise Completa**
Abra o notebook `analise_fraude_hp.ipynb` e execute todas as células para:
- Carregar e processar dados
- Treinar modelos de ML
- Gerar relatórios de fraude
- Visualizar resultados

## 📊 Dados de Entrada

### Dataset Principal
- **Produtos**: Informações de anúncios do Mercado Livre
- **Reviews**: Avaliações e feedback dos usuários
- **Vendedores**: Dados dos vendedores e suas reputações

### Dados de Referência HP
- **Tabela de Preços**: Preços oficiais sugeridos pela HP
- **Briefing**: Documentação sobre padrões de pirataria

## 📈 Métricas e Resultados

O sistema gera:
- **Scores de Risco**: Pontuação de 0-100 para cada produto
- **Classificações**: Produto legítimo, suspeito ou fraudulento
- **Relatórios**: Análises detalhadas por vendedor e categoria
- **Dashboards**: Visualizações interativas dos resultados

## 🔧 Configuração Avançada

### Personalização de Modelos
- Ajuste de thresholds de detecção
- Configuração de features específicas
- Treinamento com novos dados

### Integração com APIs
- Configuração de rate limits
- Personalização de prompts da IA
- Integração com outras fontes de dados

## 📝 Logs e Monitoramento

- **logs.log**: Logs detalhados do sistema
- **mlruns/**: Experimentos e métricas do MLflow
- **Console**: Output em tempo real do processamento

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto foi desenvolvido para fins acadêmicos no contexto do Sprint 3 da FIAP.

## 📞 Contato

Para dúvidas ou sugestões, entre em contato através dos canais oficiais do projeto.

---

**Desenvolvido com ❤️ para combater a pirataria de cartuchos HP**