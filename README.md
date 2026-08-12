# 📚 Residência Trilhas em Tecnologias - IA e RAG - Introdução à IA 

## Aluno: João Pedro Félix Reis

## Organização do Repositório

| Pasta | Título | Conteúdo | README |
| --- | --- | --- | --- |
| `AULA_01/` | Setup inicial  | Primeiros testes com LLMs, OpenRouter/OpenAI e variáveis de ambiente. | [Ler README](AULA_01/README.md) |
| `AULA_02/` | Extração estruturada de informações | Extração de documentos PDFs. | [Ler README](AULA_02/README.md) |
| `AULA_03/` | Embeddings, distâncias e busca semântica manual | Scripts e resultados de embeddings, distâncias e busca semântica manual. | [Ler README](AULA_03/README.md) |
| `AULA_04/` | Busca semântica com LangChain e RAG | PDFs, conversão com Docling e arquivos Markdown da atividade de chunking/RAG. | [Ler README](AULA_04/README.md) |

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
