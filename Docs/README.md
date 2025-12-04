# *Capa*

*Título do Projeto*: Monitoramento de Preço Global de Placas de Vídeo de Alto Desempenho para Inteligência Artificial

*Nome do Estudante*: Mateus Akira de Oliveira Muranaka

*Curso*: Engenharia de Software

# Resumo

Este documento descreve o desenvolvimento de um sistema de monitoramento de preços de placas de vídeo de alto desempenho utilizadas para Inteligência Artificial (IA). O sistema utiliza a técnica de web scraping por meio de APIs para coletar preços de placas de vídeo em plataformas internacionais e exibe as informações de forma acessível para o usuário. A ferramenta permitirá aos usuários saber qual país oferece o preço mais barato para as placas de vídeo no momento da consulta, com a conversão do preço em tempo real para a moeda brasileira, o Real (R$). Além disso, o projeto será desenvolvido utilizando Python para backend e React JS para frontend.

# 1. Introdução
## 1.1. Contexto

Com a crescente adoção de tecnologias de Inteligência Artificial (IA) e aprendizado de máquina, houve um aumento exponencial na demanda por placas de vídeo de alto desempenho (GPUs), especialmente modelos voltados para cargas de trabalho pesadas como treinamento de modelos de IA e deep learning. Essas placas, como as da linha NVIDIA RTX, Quadro ou AMD Instinct, possuem preços elevados e grande variação conforme o país, cotação da moeda, demanda local e outros fatores.

Em paralelo, consumidores que dependem dessas GPUs para seus projetos, como pesquisadores, desenvolvedores independentes, startups, entusiastas de IA e mineradores de dados, enfrentam dificuldades em acompanhar o comportamento de preços em sites internacionais e tomar decisões de compra baseadas em dados atualizados. A flutuação constante nos valores e o impacto do câmbio tornam inviável realizar comparações manuais frequentes.

Dessa forma, surge a necessidade de um sistema de monitoramento de preços internacionais, que permita ao usuário visualizar de forma rápida e clara em qual plataforma o produto está mais barato naquele momento, com os preços já convertidos em Reais (BRL).


## 1.2. Justificativa

Este projeto é relevante para o campo da engenharia de software, pois combina várias disciplinas práticas: web scraping, consultas via APIs oficiais, automação de coleta de dados, integração com APIs de câmbio, apresentação de dados via interface web interativa, e persistência de dados.
Do ponto de vista de aplicação real, o sistema atende a um público bem definido: profissionais e entusiastas da área de IA e computação de alto desempenho, que precisam adquirir componentes de maneira estratégica, buscando custo-benefício em um mercado globalizado.
Ao contrário de uma aplicação de uso único, o sistema se propõe a ser uma ferramenta recorrente, especialmente útil para:

- Pesquisadores que precisam renovar ou ampliar seus laboratórios com novos hardwares.
- Desenvolvedores independentes ou freelancers que desejam montar estações de trabalho para treinar modelos.
- Startups que querem otimizar seus recursos na hora de escalar suas infraestruturas.
- Consumidores em geral que acompanham as flutuações para realizar a compra no melhor momento.

*Exemplo prático de utilização do sistema:*
Imagine um desenvolvedor no Brasil que está acompanhando o preço da GPU NVIDIA RTX 5090. Ele acessa o sistema e, com apenas alguns cliques, descobre que naquele dia o melhor preço convertido em reais está em um site internacional, mesmo com taxas de frete e câmbio. Isso permite a tomada de decisão informada e estratégica, algo que seria trabalhoso de fazer manualmente.

## 1.3. Objetivos

*Objetivo Principal*: Desenvolver um sistema para monitoramento de preços de placas de vídeo de alto desempenho, fornecendo informações sobre o preço mais baixo em diferentes países e realizando a conversão para a moeda brasileira (R$).

*Objetivos Secundários*:

- Utilizar técnicas de web scraping para coletar informações de sites internacionais.

- Implementar a integração com APIs para conversão de moeda.

- Desenvolver uma interface de visualização de dados que permita a análise intuitiva das variações de preço utilizando React JS.

- Garantir que o sistema seja eficiente e escalável, lidando com grandes volumes de dados.

# 2. Descrição do Projeto
## 2.1. Tema do Projeto

O tema do projeto é o monitoramento de preços de placas de vídeo de alto desempenho (GPUs), com o objetivo de ajudar usuários a identificar as melhores ofertas em diferentes países. A aplicação utiliza técnicas de web scraping por meio de APIs próprias para isso, a fim de extrair informações de preços de sites de e-commerce de diversos países e usa APIs de câmbio para converter os valores para reais.

## 2.2. Problemas a Resolver

- Variação de preços: Identificar a diferença de preços de placas de vídeo em diferentes sites de e-commerce e países.
  
- Conversão de moedas: Realizar a conversão de preços em diferentes moedas para reais, de forma automatizada.
  
- Interface de usuário: Criar uma interface fácil de usar e eficiente, permitindo ao usuário inserir filtros e visualizar os resultados de forma clara.
  
- Gestão de Cache: Implementar sistema de armazenamento temporário de preços para reduzir chamadas às APIs externas e melhorar performance.
  
- Recuperação de Senha: Fornecer fluxo seguro de redefinição de senha via e-mail com tokens temporários.

## 2.3. Limitações

- O sistema será limitado ao monitoramento de placas de vídeo de alto desempenho para treinamento de IA, não abrangendo outros tipos de componentes de hardware.

  - O sistema foca o monitoramento em um conjunto específico e pré-definido de placas de vídeo:

    - NVIDIA A6000 48 GB
    - AMD Radeon PRO W7900 48 GB
    - NVIDIA RTX 5090 32 GB
    - NVIDIA RTX 6000 Ada 48 GB
    - NVIDIA GeForce RTX 4090 24 GB
    - AMD Radeon RX 7900 XTX 24 GB
    - NVIDIA RTX 4080 Super 16 GB
    - AMD Radeon RX 7600 XT 16GB
    - Intel Arc A770 16 GB
    - AMD Radeon RX 7900 XT 20 GB

  - Esta decisão de design é intencional, pois estes modelos representam o hardware mais procurado pelo público-alvo (entusiastas de IA, pesquisadores e pequenas empresas) que procura um equilíbrio entre desempenho extremo e acessibilidade no mercado de consumo. Placas de uso puramente corporativo ou de data center (como a NVIDIA A100) foram excluídas do escopo por não serem tipicamente vendidas em mercados ao consumidor final, dificultando a aquisição e a comparação de preços.

- Não incluirá integração com todas as lojas do mercado, mas sim com um conjunto específico de sites que oferecem placas de vídeo.

- Alguns sites podem acabar bloqueando a utilização do bot para web scraping, assim dificultando a coleta de informações.

# 3. Especificação Técnica

## 3.1. Requisitos de Software

### Requisitos Funcionais (RF):

- RF1: O sistema deve apresentar ao usuário uma interface (dashboard) com os modelos de placas de vídeo pré-cadastradas permitindo ao usuário selecionar uma delas para iniciar a busca comparativa de preços, lista de placas:

  - NVIDIA A6000 48 GB
  - AMD Radeon PRO W7900 48 GB
  - NVIDIA RTX 5090 32 GB
  - NVIDIA RTX 6000 Ada 48 GB
  - NVIDIA GeForce RTX 4090 24 GB
  - AMD Radeon RX 7900 XTX 24 GB
  - NVIDIA RTX 4080 Super 16 GB
  - AMD Radeon RX 7600 XT 16GB
  - Intel Arc A770 16 GB
  - AMD Radeon RX 7900 XT 20 GB

- RF2: O sistema deve realizar coleta de preços através de um modelo híbrido:

  - Atualizações automáticas agendadas (03:00 e 15:00 horário de Brasília)
  - Atualizações sob demanda quando não há dados em cache
  - Armazenamento de histórico de preços no banco de dados para consultas rápidas.
  - O sistema deve realizar coleta de preços através de um modelo híbrido:
  - Atualizações automáticas agendadas (03:00 e 15:00 horário de Brasília)
  - Atualizações sob demanda quando não há dados em cache
  - Armazenamento de histórico de preços no banco de dados para consultas rápidas. 

- RF3: O sistema deve converter os preços coletados para Reais (BRL) utilizando APIs de câmbio.

- RF4: O sistema deve utilizar uma abordagem híbrida de coleta de dados: Web Scraping para plataformas que não fornecem acesso direto (ex: Amazon via Scrapfly) e Integração via API Oficial para plataformas que disponibilizam esse recurso (ex: eBay).

- RF5: O sistema deve exibir os resultados da busca de forma ordenada por menor preço, informando o nome do produto, site de origem, valor convertido e link para o produto.
  
- RF6: O sistema deve permitir que o usuário envie sugestões de novos modelos de placas de vídeo e de fontes de pesquisa de preços para futura inclusão.

- RF7: O sistema deve permitir que novos usuários se cadastrem fornecendo um e-mail e senha e que usuários existentes façam login com suas credenciais.

- RF8: O sistema deve proteger o acesso às funcionalidades principais (como busca de preços) apenas para usuários autenticados.

- RF9: O sistema deve permitir a recuperação de senha via e-mail, gerando um token temporário com validade.

- O sistema deve armazenar e exibir o histórico de variação de preços de cada produto.
  - Para produtos nacionais ou vendidos em Reais (ex: Amazon BR), o histórico deve apresentar o valor nominal coletado (BRL).
  - Para produtos internacionais (ex: eBay), o sistema deve exibir o valor na moeda original (USD) e/ou o valor convertido, permitindo ao usuário analisar se a variação de preço ocorreu devido ao vendedor ou devido à oscilação cambial.

### Requisitos Não-Funcionais (RNF):

- RNF1: O sistema deve ser eficiente no processamento de dados para garantir a experiência do usuário sem delays.

- RNF2: O sistema deve ser escalável para suportar o aumento de fontes de dados e número de usuários.

- RNF3: A interface deve ser intuitiva e responsiva, adaptando-se a diferentes dispositivos.

- RNF4: O sistema deve gerenciar credenciais sensíveis (chaves de API, senhas de banco de dados) exclusivamente através de variáveis de ambiente, garantindo que nenhum segredo seja exposto no código-fonte.

### Representação dos Requisitos:

Diagrama de Casos de Uso (UML) para representar as interações do usuário com o sistema:

![Diagrama UML do Projeto](Diagrama%20UML%20-%20TCC.jpg)

## 3.2. Considerações de Design

*Visão Inicial da Arquitetura*: O sistema será composto por um backend desenvolvido em Python, utilizando web scraping via API para coletar dados e APIs para conversão de moedas, e um frontend em React JS para a apresentação das informações ao usuário.

*Estratégias de Otimização:*

1. Sistema de Cache em Banco de Dados:
- Armazena histórico completo de preços coletados
- Reduz latência em consultas subsequentes
- Permite análise temporal de variação de preços

2. Agendador de Tarefas (APScheduler):
- Atualiza preços automaticamente 2x ao dia (03:00 e 15:00)
- Reduz tempo de resposta para o usuário final
- Mantém dados sempre atualizados em horários estratégicos

3. Gestão de Tokens da API eBay:
- Sistema automático de refresh de access tokens
- Armazena tokens em arquivo local (ebay_token.json)
- Renovação proativa 5 minutos antes da expiração

*Padrões de Arquitetura*: O sistema seguirá o padrão MVC (Model-View-Controller) para separar claramente as responsabilidades entre a lógica de negócios, a interface do usuário e o controle dos dados.

*Modelos C4*: A arquitetura será detalhada em 4 níveis:

- *Nível de Contexto*: Mostra como o sistema interage com os usuários e fontes externas de dados.

![C4 Modelo - Contexto](https://github.com/user-attachments/assets/c785259d-2a88-4b49-84b1-8c31577ff302)

- *Nível de Contêineres*: Divide o sistema em componentes como backend, frontend, APIs e banco de dados.

![C4 Modelo - Conteiners](https://github.com/user-attachments/assets/31f19408-2a34-4593-a5cc-9fae43f9da8c)

- *Nível de Componentes*: Detalha os componentes principais do sistema, como o scraper, o conversor de moedas e a interface de usuário.

![C4 Modelo - Componentes](https://github.com/user-attachments/assets/ab14be2b-0b2e-4f93-995a-cbd274f06d3a)

## 3.3. Stack Tecnológica

*Linguagens de Programação*: Python para backend e web scraping e React JS para frontend.

*Frameworks e Bibliotecas*: 

- FastAPI (para a construção da API)
- SQLAlchemy (para a interação com o banco de dados)
- Pydantic (para validação de dados)
- Passlib com Bcrypt (para hashing de senhas)
- Python-JOSE (para manipulação de JWT)
- psycopg2-binary (driver de conexão com o PostgreSQL)
- Scrapfly (como serviço de API para contornar bloqueios de scraping)
- BeautifulSoup4 (para a análise e extração de dados do HTML)
- APScheduler (agendamento de tarefas periódicas)
- SendGrid (envio de e-mails de recuperação de senha)
- Loguru (logging avançado para depuração)
- Frankfurter API (conversão USD → BRL em tempo real)

*Frontend:* React Router (para navegação), Axios (para integração com a API) e MUI (Material-UI) (para a biblioteca de componentes visuais).

*Desenvolvimento e DevOps:* GitHub (para versionamento de código), Docker (para contêinerização), Github Actions (para CI/CD), PostgreSQL (para armazenar dados de preços).

*CI/CD e Qualidade:* GitHub Actions (para integração e entrega contínua), SonarCloud (para análise estática de qualidade e segurança do código).

*Banco de Dados:* PostgreSQL (para armazenar dados de usuários e preços coletados).

*Testes:* Pytest (para testes de backend) e Jest com React Testing Library (para testes de frontend).

*Ambiente de Produção:* Azure Database for PostgreSQL (armazenamento do banco de dados), Azure Web App Service (backend) e Azure Static Web Apps (frontend).

## 3.4. Considerações de Segurança

O sistema implementa práticas de segurança recomendadas em múltiplas camadas para garantir a proteção de dados e a integridade da aplicação.

*Comunicação Segura:* Toda a comunicação entre o frontend e o backend é projetada para ocorrer sobre HTTPS, garantindo a criptografia dos dados em trânsito.

*Autenticação Robusta:* Foi implementado um fluxo de autenticação de ponta a ponta, que inclui:
- Cadastro e Login de Usuários: Permite o gerenciamento de acesso individualizado à plataforma.
- Hashing de Senhas: Utiliza o algoritmo bcrypt para garantir que as senhas nunca sejam armazenadas em texto plano no banco de dados, protegendo as credenciais contra vazamentos.
- Gerenciamento de Sessão com JWT: Emprega JSON Web Tokens para gerenciar as sessões dos usuários de forma segura e stateless após o login.

*Gerenciamento de Segredos:* As credenciais sensíveis (como chaves de API e senhas de banco de dados) são gerenciadas através de variáveis de ambiente e arquivos .env, que são excluídos do versionamento de código pelo .gitignore, evitando a exposição de segredos no repositório.

*Análise de Segurança Contínua:* A integração com o SonarCloud no pipeline de CI/CD realiza análises a cada Pull Request para identificar potenciais vulnerabilidades ("Security Hotspots") e falhas de segurança no código.

*Coleta de Dados Ética:* A coleta de dados por web scraping é realizada de forma a respeitar as políticas dos sites de e-commerce e evitar sobrecarga em seus servidores. 

## 4. Referências

*Backend (Python)*
- SQLAlchemy (Para a interação com o banco de dados): https://docs.sqlalchemy.org/en/20/
- Pydantic (Para validação de dados e configurações): https://docs.pydantic.dev/
- Passlib (Para hashing de senhas com Bcrypt): https://passlib.readthedocs.io/en/stable/
- Python-JOSE (Para manipulação de tokens JWT): https://python-jose.readthedocs.io/en/latest/
- APScheduler (Para agendamento de tarefas): https://apscheduler.readthedocs.io/en/3.x/userguide.html
- ScrapflyAPI (Raspagem de dados da Amazon): https://scrapfly.io/docs
- eBay API (Dados de produtos do Ebay): https://developer.ebay.com/develop/get-started

*Frontend (React)*
- MUI (Material-UI) (Para a biblioteca de componentes visuais): https://mui.com/material-ui/getting-started/
- React Router (Para o sistema de rotas e navegação): https://reactrouter.com/home
- Axios (Para as chamadas à API): https://axios-http.com/docs/intro

*Banco de Dados*
- PostgreSQL (O banco de dados que você implementou): https://www.postgresql.org/docs/17/index.html
- pgAdmin (A ferramenta de gerenciamento do banco de dados): https://www.pgadmin.org/docs/pgadmin4/development/index.html

*Testes*
- Pytest (Para os testes do backend): https://docs.pytest.org/
- React Testing Library (Para os testes do frontend): https://testing-library.com/docs/react-testing-library/intro/
- Jest (Para os testes de frontend): https://jestjs.io/docs/getting-started

*DevOps e CI/CD*
- Docker (Para a contêinerização): https://www.docker.com/
- Docker Compose (Para a orquestração dos contêineres): https://docs.docker.com/compose/
- GitHub Actions (Para a automação de CI/CD): https://github.com/features/actions
- SonarCloud (Para a análise de qualidade de código): https://www.sonarsource.com/learn/

*Produção*
- Azure Database Service (Banco de Dados) - https://docs.azure.cn/en-us/postgresql/flexible-server/service-overview
- Azure Web App Service (Backend) - https://learn.microsoft.com/pt-br/azure/app-service/
- Azure Static Web Apps (Frontend) - https://learn.microsoft.com/pt-br/azure/static-web-apps/
