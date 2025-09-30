import json
import pandas as pd
import re
import os
from datetime import datetime

def limpar_valor_numerico(texto, tipo=float):
    """Extrai o primeiro valor numérico de uma string."""
    if texto is None:
        return None
    
    texto_str = str(texto)
    match = re.search(r'(\d+[\.,]?\d*)', texto_str)
    if match:
        try:
            valor_limpo = match.group(1).replace(',', '.')
            return tipo(valor_limpo)
        except (ValueError, TypeError):
            return None
    return None

def limpar_texto_para_csv(texto): # <-- ### NOVA FUNÇÃO ###
    """Remove quebras de linha e excesso de espaços para evitar problemas no CSV."""
    if not isinstance(texto, str):
        return texto
    # Substitui quebras de linha por um espaço e remove espaços duplos
    texto_limpo = texto.replace('\n', ' ').replace('\r', ' ')
    texto_limpo = re.sub(r'\s+', ' ', texto_limpo).strip()
    return texto_limpo

def processar_produto(produto_bruto):
    """Transforma um dicionário de produto bruto em um dicionário limpo e essencial."""
    dados_essenciais = {}
    
    json_ld = produto_bruto.get('dados_brutos', {}).get('json_ld', {}) or {}
    melidata = produto_bruto.get('dados_brutos', {}).get('melidata', {}) or {}
    
    # --- Identificação Essencial ---
    dados_essenciais['id_produto'] = produto_bruto.get('id')
    dados_essenciais['titulo'] = produto_bruto.get('titulo', '').replace('| MercadoLivre', '').strip()
    dados_essenciais['link'] = produto_bruto.get('link')

    # --- Dados Comerciais e de Anúncio ---
    dados_essenciais['preco_atual'] = limpar_valor_numerico(melidata.get('price'))
    dados_essenciais['preco_original'] = limpar_valor_numerico(melidata.get('original_price'))
    
    unidades = 1
    try:
        unidades_options = melidata.get('pickers', {}).get('UNITS_PER_PACK', [])
        for option in unidades_options:
            if option.get('selected'):
                unidades = int(option.get('value', 1))
                break
    except (TypeError, ValueError):
        unidades = 1
    dados_essenciais['unidades_por_anuncio'] = unidades
    
    if dados_essenciais['preco_atual'] and unidades > 0:
        dados_essenciais['preco_por_unidade'] = round(dados_essenciais['preco_atual'] / unidades, 2)
    else:
        dados_essenciais['preco_por_unidade'] = None

    dados_essenciais['condicao'] = produto_bruto.get('condicao')
    dados_essenciais['tipo_anuncio'] = melidata.get('listing_type_id')
    dados_essenciais['tipo_logistica'] = melidata.get('logistic_type')
    dados_essenciais['frete_gratis'] = melidata.get('free_shipping', False)

    # --- Dados do Vendedor ---
    dados_essenciais['vendedor_id'] = melidata.get('seller_id')
    dados_essenciais['vendedor_nome'] = melidata.get('seller_name')
    dados_essenciais['vendedor_reputacao'] = melidata.get('reputation_level')
    dados_essenciais['vendedor_lider'] = melidata.get('power_seller_status')
    dados_essenciais['id_loja_oficial'] = melidata.get('official_store_id')

    # --- Dados de Reputação Social ---
    dados_essenciais['rating_medio'] = produto_bruto.get('rating_medio')
    dados_essenciais['total_reviews'] = produto_bruto.get('total_reviews')
    dados_essenciais['distribuicao_reviews'] = produto_bruto.get('distribuicao_estrelas')

    # --- Atributos Técnicos Consolidados ---
    atributos = {}
    atributos['marca'] = produto_bruto.get('marca')
    atributos['linha'] = produto_bruto.get('linha')
    atributos['modelo'] = produto_bruto.get('modelo')
    atributos['modelo_alfanumerico'] = produto_bruto.get('modelo_alfanumerico')
    atributos['tipo_cartucho'] = produto_bruto.get('tipo_cartucho')
    atributos['cor_tinta'] = produto_bruto.get('cor_tinta')
    atributos['volume_ml'] = limpar_valor_numerico(produto_bruto.get('volume'))
    
    rendimento = limpar_valor_numerico(produto_bruto.get('rendimento_paginas'), tipo=int)
    descricao_texto = produto_bruto.get('descricao', '')
    if not rendimento and descricao_texto:
        match = re.search(r'rendimento (?:de|aproximado de|de até) (\d+)', descricao_texto, re.IGNORECASE)
        if match:
            rendimento = int(match.group(1))
    atributos['rendimento_paginas'] = rendimento

    dados_essenciais['atributos'] = atributos
    
    # --- Descrição ---
    # <-- MUDANÇA ###: Aplicando a função de limpeza na descrição
    dados_essenciais['descricao'] = limpar_texto_para_csv(descricao_texto)

    # --- Origem do Dado ---
    dados_essenciais['query_origem'] = produto_bruto.get('query_origem', 'desconhecida')

    return dados_essenciais

def main():
    """Função principal para carregar, UNIR, processar e salvar datasets."""
    pasta_datasets_brutos = 'dataset_bruto'
    pasta_datasets_tratados = 'dataset_tratado'

    if not os.path.exists(pasta_datasets_tratados):
        os.makedirs(pasta_datasets_tratados)
        print(f"Pasta '{pasta_datasets_tratados}' criada.")

    if not os.path.isdir(pasta_datasets_brutos):
        print(f"❌ ERRO: A pasta '{pasta_datasets_brutos}' não foi encontrada.")
        return

    arquivos_encontrados = [
        f for f in os.listdir(pasta_datasets_brutos) 
        if f.endswith('.json') and 'dataset_javascript' in f
    ]

    if not arquivos_encontrados:
        print(f"⚠️ Nenhum arquivo de dataset bruto (contendo 'dataset_javascript') encontrado na pasta '{pasta_datasets_brutos}'.")
        return

    print(f"🔍 Encontrados {len(arquivos_encontrados)} arquivos de dataset bruto para processar.")
    
    todos_os_produtos = []
    for nome_arquivo in arquivos_encontrados:
        caminho_arquivo = os.path.join(pasta_datasets_brutos, nome_arquivo)
        try:
            with open(caminho_arquivo, 'r', encoding='utf-8') as f:
                dados = json.load(f)
            
            produtos_do_arquivo = dados.get('produtos', [])
            query_origem = dados.get('query', 'desconhecida')
            
            for produto in produtos_do_arquivo:
                produto['query_origem'] = query_origem
            
            todos_os_produtos.extend(produtos_do_arquivo)
            print(f"  -> Arquivo '{nome_arquivo}' carregado: {len(produtos_do_arquivo)} produtos (query: '{query_origem}')")

        except (json.JSONDecodeError, Exception) as e:
            print(f"❌ ERRO ao carregar ou processar o arquivo '{nome_arquivo}': {e}")
            continue
    
    if not todos_os_produtos:
        print("⚠️ Nenhum produto foi encontrado nos arquivos JSON válidos.")
        return

    print(f"\n✅ Total de {len(todos_os_produtos)} produtos brutos unidos.")
    print(f"🔄 Processando e limpando todos os {len(todos_os_produtos)} produtos...")
    dataset_limpo = [processar_produto(p) for p in todos_os_produtos]
    print("✅ Processamento concluído.")

    timestamp_geral = datetime.now().strftime("%Y%m%d_%H%M%S")
    nome_base_arquivo = f'dataset_consolidado_{timestamp_geral}'

    # Salvar em JSON limpo (o JSON pode manter as quebras de linha originais)
    caminho_json_limpo = os.path.join(pasta_datasets_tratados, f'{nome_base_arquivo}.json')
    with open(caminho_json_limpo, 'w', encoding='utf-8') as f:
        # Para o JSON, vamos usar os dados sem a limpeza de texto para manter a formatação original
        dataset_json = [processar_produto(p) for p in todos_os_produtos]
        for item in dataset_json:
            item['descricao'] = item.get('descricao', '').replace('\n', ' ').replace('\r', ' ') # Limpeza simples para JSON
        json.dump(dataset_json, f, ensure_ascii=False, indent=2)
    print(f"💾 Dataset consolidado salvo em JSON: '{caminho_json_limpo}'")

    # Salvar em CSV (usando o dataset_limpo com a descrição sanitizada)
    try:
        df = pd.json_normalize(dataset_limpo, sep='_')
        caminho_csv_limpo = os.path.join(pasta_datasets_tratados, f'{nome_base_arquivo}.csv')
        df.to_csv(caminho_csv_limpo, index=False, encoding='utf-8-sig')
        print(f"💾 Dataset consolidado salvo em CSV: '{caminho_csv_limpo}'")
    except Exception as e:
        print(f"⚠️ Não foi possível salvar em CSV. Erro: {e}")

if __name__ == '__main__':
    main()