import json
import re

def str_to_float(val):
    """Converte string formatada em Real (R$ 1.000,00) para float (1000.0)."""
    try: 
        return float(str(val).replace('R$', '').replace('.', '').replace(',', '.').strip())
    except: 
        return 0.0

def formatar_valor_contabil(valor):
    """Converte valores em parênteses (15000) para formato negativo - 15000."""
    v_str = str(valor).strip()
    if v_str.startswith('(') and v_str.endswith(')'):
        numero_limpo = v_str[1:-1].strip()
        return f"- {numero_limpo}"
    return v_str

def safe_float(valor):
    """Conversão ultra-segura para float, lidando com diversos formatos numéricos."""
    try:
        if isinstance(valor, (int, float)): return float(valor)
        v = str(valor).upper().replace('R$', '').strip()
        if '.' in v and ',' in v: v = v.replace('.', '').replace(',', '.')
        elif ',' in v: v = v.replace(',', '.')
        v = re.sub(r'[^\d.-]', '', v)
        return float(v) if v else 0.0
    except:
        return 0.0

def extrair_json_seguro(texto):
    """Localiza e extrai o primeiro bloco JSON de uma string de texto da IA."""
    # Tenta extrair de bloco markdown ```json ... ``` primeiro
    try:
        match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', texto, re.DOTALL)
        if match:
            return json.loads(match.group(1))
    except:
        pass
    # Fallback: busca raw entre o primeiro { e o último }
    try:
        inicio = texto.find('{')
        fim = texto.rfind('}') + 1
        if inicio != -1 and fim > inicio:
            return json.loads(texto[inicio:fim])
    except:
        pass
    return {}

def limpa_pdf(texto):
    """Remove emojis e caracteres problemáticos para compatibilidade com FPDF (Latin-1)."""
    try:
        texto_str = str(texto)
        # Substitui caracteres comuns incompatíveis com latin-1
        replacements = {
            '“': '"', '”': '"', '‘': "'", '’': "'", '–': '-', '—': '-',
            '…': '...', '•': '-', '\u200b': '', '\xa0': ' '
        }
        for k, v in replacements.items():
            texto_str = texto_str.replace(k, v)
        # Primeiro tenta direto (funciona com ISO-8859-1/Latin-1)
        return texto_str.encode('latin-1', 'ignore').decode('latin-1').strip()
    except:
        # Fallback: remover tudo que não for ASCII básico
        return ''.join(c for c in str(texto) if ord(c) < 128).strip()

def formatar_moeda_br(valor):
    """Formata float para R$ 1.234,56."""
    try:
        return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return str(valor)

def limpa_markdown(texto):
    """Remove marcações Markdown (como negrito, subtítulos e tabelas) devolvendo texto limpo."""
    try:
        texto_str = str(texto)
        # Remove bold/italic (**, __)
        texto_str = re.sub(r'\*\*(.*?)\*\*', r'\1', texto_str)
        texto_str = re.sub(r'__(.*?)__', r'\1', texto_str)
        # Remove headers (## Header -> Header)
        texto_str = re.sub(r'^#+\s*', '', texto_str, flags=re.MULTILINE)
        # Remove table separator lines like |---|---|
        texto_str = re.sub(r'^\|?[\s\-:]+\|[\s\-:|]+$', '', texto_str, flags=re.MULTILINE)
        # Replace pipes with spaces to keep separation but remove table borders
        texto_str = texto_str.replace('|', '  ')
        # Remove multiple empty lines
        texto_str = re.sub(r'\n{3,}', '\n\n', texto_str)
        return texto_str.strip()
    except:
        return str(texto)
