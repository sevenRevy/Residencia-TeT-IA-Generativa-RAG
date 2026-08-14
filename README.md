# 📚 Residência Trilhas em Tecnologias - IA e RAG - Introdução à IA 

## Aluno: João Pedro Félix Reis

## Organização do Repositório

| Pasta | Título | Conteúdo | README |
| --- | --- | --- | --- |
| `AULA_01/` | Setup inicial  | Primeiros testes com LLMs, OpenRouter/OpenAI e variáveis de ambiente. | [Ler README](AULA_01/README.md) |
| `AULA_02/` | Extração estruturada de informações | Scripts de conversão e extração de metadados. | [Ler README](AULA_02/README.md) |
| `AULA_03/` | Embeddings, distâncias e busca semântica manual | Scripts de embeddings, distâncias, busca semântica manual e gráficos. | [Ler README](AULA_03/README.md) |
| `AULA_04/` | Busca semântica com LangChain e RAG | Script de conversão com Docling e experimentos de chunking/RAG. | [Ler README](AULA_04/README.md) |
| `AULA_05/` | Documents com LangChain | Exemplos de `Document` com metadados a partir dos dados reais da Aula 04. | [Ler README](AULA_05/README.md) |

## Organização do Corpus

Os dados ficam centralizados em `corpus/`, separados pelo estágio do pipeline. As pastas `AULA_*` guardam a progressão das aulas, scripts e explicações; o corpus guarda os artefatos de entrada e saída.

```text
corpus/
├── raw/
│   ├── aula02/      # PDFs usados na Aula 02
│   └── aula04/      # PDFs usados na Aula 04
├── processed/
│   ├── aula02/      # Markdown gerado a partir dos PDFs da Aula 02
│   └── aula04/      # Markdown gerado a partir dos PDFs da Aula 04
├── metadata/
│   └── aula02/      # JSONs de metadados extraídos na Aula 02
├── embeddings/
│   └── aula03/      # JSONs de embeddings, distâncias e busca semântica manual
└── reports/
    └── aula04/      # Relatórios completos e filtrados dos experimentos de RAG
```

## Onde Procurar

| Artefato | Caminho |
| --- | --- |
| PDFs originais da Aula 02 | `corpus/raw/aula02/` |
| PDFs originais da Aula 04 | `corpus/raw/aula04/` |
| Markdown processado da Aula 02 | `corpus/processed/aula02/` |
| Markdown processado da Aula 04 | `corpus/processed/aula04/` |
| Metadados extraídos da Aula 02 | `corpus/metadata/aula02/` |
| Embeddings e resultados da Aula 03 | `corpus/embeddings/aula03/` |
| Relatórios de busca/chunking da Aula 04 | `corpus/reports/aula04/` |

## 🚀 Passo a Passo para Configuração e Execução

### 1. Criar o Ambiente Virtual (venv)
Abra o seu terminal na pasta raiz do projeto (`/IA`) e execute o seguinte comando para criar o ambiente virtual:

```bash
# No Linux/macOS
python3 -m venv venv

# No Windows
python -m venv venv
```

### 2. Ativar o Ambiente Virtual
Sempre que for trabalhar no projeto ou rodar os códigos, você precisa ativar o `venv`.

```bash
# No Linux/macOS
source venv/bin/activate

# No Windows
venv\Scripts\activate
```
*(Você saberá que o ambiente está ativado porque o nome `(venv)` aparecerá no início da linha de comando do terminal).*

### 3. Instalar as Dependências
Com o ambiente ativado, instale as bibliotecas necessárias (como `openai` e `python-dotenv`) a partir do arquivo `requirements.txt` que está na raiz do projeto:

```bash
pip install -r requirements.txt
```

### 4. Configurar as Variáveis de Ambiente (Segurança)
Para proteger seus dados e garantir a segurança, as chaves de API nunca devem ser inseridas diretamente no código nem comitadas em repositórios públicos.

Crie um arquivo `.env` na raiz do projeto a partir do modelo `.env.example`:

```env
OPENAI_API_KEY=sua_chave_de_api_aqui
OPENAI_MODEL=gpt-5.4-mini
OPENAI_EMBEDDING_MODEL=nvidia/nemotron-3-embed-1b:free
```
*(Importante: adicione o arquivo `.env` ao seu `.gitignore` para não enviá-lo para o GitHub).*

### 5. Rodar o Código
Agora que o ambiente está isolado e as bibliotecas estão instaladas, você pode executar o script:

```bash
# Entre na pasta da aula
cd AULA_01

# Execute o script Python
python hello_llm_OR.py
```

---
### 🛑 Como sair do Ambiente Virtual?
Quando terminar de programar, você pode desativar o ambiente virtual executando simplesmente:
```bash
deactivate
```
