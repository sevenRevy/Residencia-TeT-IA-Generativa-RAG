# AULA 01

Pasta com os primeiros testes de comunicação com modelos de linguagem.

## Conteúdo

- `hello_llm.py`: teste inicial com o SDK da OpenAI.
- `hello_llm_OR.py`: teste usando OpenRouter com interface compatível com OpenAI.
- `hello_llm.ipynb`: versão em notebook da atividade.

Esta aula não gera relatórios em `corpus/reports/`; ela documenta a configuração inicial usada pelas etapas posteriores do projeto.

## Relatório

### 03/08/2026 - AULA 1

Nesta primeira etapa do projeto, realizei a configuração do ambiente Python e a integração inicial com modelos de linguagem (LLMs). Configurei um ambiente virtual (`venv`) para isolar as dependências utilizadas, instalei as bibliotecas necessárias (`openai` e `python-dotenv`) e implementei o carregamento seguro das credenciais através de variáveis de ambiente utilizando um arquivo `.env`, evitando expor a chave da API diretamente no código.

Para realizar a comunicação com o modelo de linguagem, utilizei o SDK da OpenAI em conjunto com a API da **OpenRouter**, que disponibiliza uma interface compatível com a API da OpenAI e permite o acesso a diferentes modelos de IA através do mesmo padrão de integração. A aplicação foi configurada para enviar mensagens para um modelo de linguagem, receber as respostas geradas e exibi-las no terminal, estabelecendo o fluxo básico entre a aplicação Python e um LLM.

Durante os testes, também realizei ajustes relacionados ao gerenciamento de tokens da requisição, limitando o tamanho das respostas para adequar o consumo de recursos e evitar erros relacionados aos limites disponíveis da API. Com essa configuração inicial, estabeleci a base necessária para evoluir o projeto para aplicações envolvendo IA Generativa, RAG (Retrieval-Augmented Generation) e processamento de documentos.
