# 📚 Residência Trilhas em Tecnologias - IA e RAG - Introdução à IA 

## Aluno: João Pedro Félix Reis

### 03/08/2026 - AULA 1
Nesta primeira etapa do projeto, realizei a configuração do ambiente Python e a integração inicial com modelos de linguagem (LLMs). Configurei um ambiente virtual (`venv`) para isolar as dependências utilizadas, instalei as bibliotecas necessárias (`openai` e `python-dotenv`) e implementei o carregamento seguro das credenciais através de variáveis de ambiente utilizando um arquivo `.env`, evitando expor a chave da API diretamente no código.

Para realizar a comunicação com o modelo de linguagem, utilizei o SDK da OpenAI em conjunto com a API da **OpenRouter**, que disponibiliza uma interface compatível com a API da OpenAI e permite o acesso a diferentes modelos de IA através do mesmo padrão de integração. A aplicação foi configurada para enviar mensagens para um modelo de linguagem, receber as respostas geradas e exibi-las no terminal, estabelecendo o fluxo básico entre a aplicação Python e um LLM.

Durante os testes, também realizei ajustes relacionados ao gerenciamento de tokens da requisição, limitando o tamanho das respostas para adequar o consumo de recursos e evitar erros relacionados aos limites disponíveis da API. Com essa configuração inicial, estabeleci a base necessária para evoluir o projeto para aplicações envolvendo IA Generativa, RAG (Retrieval-Augmented Generation) e processamento de documentos.

### 05/08/2026 - AULA 2
Nessa aula, trabalhei com extração estruturada de informações a partir de arquivos `.md`. O script `Aula02_arquivos_output/test_json_extractor.py` lê o conteúdo de um documento de entrada, envia o texto para um modelo via OpenRouter/OpenAI e solicita a geração de um JSON seguindo um schema fixo com os campos `titulo`, `autores` e `ano`.

O resultado é salvo na própria pasta `Aula02_arquivos_output`, gerando um arquivo `.json` para cada documento processado. A proposta da atividade foi transformar texto livre em dados estruturados, facilitando o uso posterior em pipelines de RAG, análise de conteúdo e organização automática de documentos.

### 07/08/2026 - AULA 3
Nessa aula, explorei embeddings e comparação semântica entre termos. O script `Aula03_embedding_output/test_embeddings.py` gera embeddings para palavras como `gato`, `felino`, `carro` e `banana`, salvando cada vetor em arquivos `.json` dentro de `Aula03_embedding_output`.

Também adicionei o script `Aula03_embedding_output/busca_semantica_manual.py`, que gera o teste com `frase_ancora` e `frases_comparacao` e produz um relatório de busca semântica manual sobre os arquivos `.md` da aula 2, comparando trechos por linha, parágrafo e capítulo.

Depois, o script `Aula03_embedding_output/fun_distancia.py` calcula distâncias euclidiana e cosseno entre todos os pares de termos e grava o resultado consolidado em `Aula03_distancias.json`. Para visualizar a distribuição dos vetores, o script `Aula03_graficos/visualizar_embeddings.py` aplica PCA em 2D e 3D e exporta os gráficos em `Aula03_graficos/embeddings_pca_2d.png` e `Aula03_graficos/embeddings_pca_3d.html`.

### 10/08/2026 - AULA 4
Nessa aula, avancei na implementação da busca semântica utilizando LangChain e embeddings gerados através da API da OpenAI. O projeto passou a trabalhar diretamente com os documentos em formato .md, realizando a leitura e divisão dos textos em diferentes estratégias de chunking, permitindo comparar formas distintas de segmentação dos documentos.

Também implementei a geração de embeddings em lotes e o cálculo de similaridade por cosseno entre os vetores. A partir desses recursos, foi criada uma função de busca semântica capaz de receber uma consulta e recuperar os trechos mais semelhantes dentro do corpus de documentos.

Por fim, desenvolvi a geração de relatórios para múltiplas consultas, salvando os resultados da busca em arquivos .json. Durante a implementação, também foram adicionados tratamentos para erros relacionados à chave da API e à dimensão dos embeddings. Além da implementação da busca semântica, ampliei o corpus utilizado nos testes com novos documentos, permitindo avaliar o funcionamento da recuperação semântica em uma base maior e mais diversificada.

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

Certifique-se de que o arquivo `.env` exista dentro da pasta `AULA_01` (ou na raiz, dependendo de onde for executar) com a seguinte estrutura:

```env
OPENAI_API_KEY=sua_chave_de_api_aqui
OPENAI_MODEL=gpt-5.4-mini
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
