import os
import pandas as pd
import json
from openai import OpenAI
from dotenv import load_dotenv
from tqdm import tqdm

# --- CONFIGURAÇÃO E CARREGAMENTO DA API KEY ---

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise ValueError("A variável de ambiente OPENAI_API_KEY não foi encontrada. "
                     "Verifique se o arquivo .env está correto e no mesmo diretório.")

client = OpenAI(api_key=api_key)
print("Cliente da OpenAI inicializado com sucesso.")

# --- FUNÇÃO PARA CHAMAR A IA E EXTRAIR OS DADOS (PROMPT ATUALIZADO) ---

def extrair_dados_produto(titulo: str, descricao: str, modelo_ia: str = "gpt-5-nano"):
    """
    Usa a API da OpenAI para extrair informações estruturadas do título e descrição de um produto.
    """
    prompt = f"""
    Analise o título e a descrição de um anúncio de cartucho de tinta HP.
    Extraia as seguintes informações e retorne APENAS um objeto JSON válido.

    Título: "{titulo}"
    Descrição: "{descricao}"

    Siga estas regras estritamente:
    1. "quantidade_por_anuncio": (Número inteiro) A quantidade total de cartuchos no anúncio. Se a palavra "kit" for mencionada mas a quantidade exata não, assuma que são 2.
    2. "cores_detalhadas": (Objeto JSON) Um objeto detalhando a contagem de cada tipo de cartucho. Use as chaves "preto" e "colorido". Se a cor não for especificada ou for única, preencha o campo correspondente com 1 e o outro com 0.
    3. "tipo_cartucho": (String) O modelo principal do cartucho. Ex: "664", "667xl", "664xl". Se houver mais de um, liste-os em uma string separados por vírgula.
    4. "usado_seminovo": (String) Responda com uma das seguintes opções: "Usado", "Seminovo", "Recondicionado", "Recarregado". Se nenhuma dessas condições for mencionada, responda "N/A".

    Exemplo de um kit com 3 cartuchos pretos e 1 colorido:
    {{
      "quantidade_por_anuncio": 4,
      "cores_detalhadas": {{
        "preto": 3,
        "colorido": 1
      }},
      "tipo_cartucho": "664xl",
      "usado_seminovo": "N/A"
    }}

    Exemplo de um único cartucho colorido:
    {{
      "quantidade_por_anuncio": 1,
      "cores_detalhadas": {{
        "preto": 0,
        "colorido": 1
      }},
      "tipo_cartucho": "667",
      "usado_seminovo": "N/A"
    }}
    """
    try:
        response = client.chat.completions.create(
            model=modelo_ia,
            messages=[
                {"role": "system", "content": "Você é um assistente especialista em extração de dados de produtos e responde estritamente em formato JSON seguindo regras complexas."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            reasoning_effort="minimal"
        )
        json_response = response.choices[0].message.content
        return json.loads(json_response)
    except Exception as e:
        print(f"\nErro ao processar o produto '{titulo}'. Erro na API: {e}")
        # Atualiza o dicionário de erro para refletir a nova estrutura
        return {
            "quantidade_por_anuncio": None,
            "cores_detalhadas": {"preto": None, "colorido": None},
            "tipo_cartucho": "ERRO_API",
            "usado_seminovo": "ERRO_API"
        }

# --- PROCESSAMENTO PRINCIPAL DO DATASET ---

def processar_dataset():
    """
    Função principal que carrega o dataset, o processa com a IA, e salva os resultados
    em um arquivo CSV enriquecido e em um arquivo JSON.
    """
    caminho_entrada = os.path.join("dataset_tratado", "dataset_enriquecido_20250930_120011.csv")
    caminho_saida_csv = os.path.join("dataset_tratado", "dataset_final_enriquecido.csv")
    caminho_saida_json = os.path.join("dataset_tratado", "dados_extraidos_ia.json")

    try:
        df = pd.read_csv(caminho_entrada)
        print(f"Arquivo '{caminho_entrada}' carregado com sucesso. {len(df)} linhas para processar.")
    except FileNotFoundError:
        print(f"ERRO: O arquivo '{caminho_entrada}' não foi encontrado.")
        return

    resultados_para_csv = []
    resultados_para_json = []

    for _, row in tqdm(df.iterrows(), total=df.shape[0], desc="Analisando produtos com IA"):
        titulo = str(row.get("titulo", ""))
        descricao = str(row.get("descricao", ""))
        id_produto = row.get("id_produto")
        
        dados_extraidos = extrair_dados_produto(titulo, descricao)
        
        resultados_para_csv.append(dados_extraidos)
        
        json_entry = {"id_produto": id_produto, **dados_extraidos}
        resultados_para_json.append(json_entry)

    print("\nGerando arquivo CSV final...")
    df_resultados = pd.DataFrame(resultados_para_csv)
    df_final = pd.concat([df.reset_index(drop=True), df_resultados], axis=1)
    df_final.to_csv(caminho_saida_csv, index=False, encoding='utf-8-sig')
    print(f"Arquivo CSV enriquecido salvo em: '{caminho_saida_csv}'")

    print("Gerando arquivo JSON final...")
    with open(caminho_saida_json, 'w', encoding='utf-8') as f:
        json.dump(resultados_para_json, f, indent=4, ensure_ascii=False)
    print(f"Arquivo JSON salvo em: '{caminho_saida_json}'")

    print("\nProcessamento concluído com sucesso!")
    print("\nAmostra dos dados do CSV enriquecido:")
    # Atualiza as colunas a serem exibidas na amostra
    print(df_final[['id_produto', 'titulo', 'quantidade_por_anuncio', 'cores_detalhadas', 'tipo_cartucho', 'usado_seminovo']].head())


if __name__ == "__main__":
    processar_dataset()