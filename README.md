# *Capa*

*Título do Projeto*: Monitoramento de Preço Global de Placas de Vídeo de Alto Desempenho para Inteligência Artificial
*Nome do Estudante*: Mateus Akira de Oliveira Muranaka
*Curso*: Engenharia de Software

# Resumo

Este documento descreve o desenvolvimento de um sistema de monitoramento de preços de placas de vídeo de alto desempenho utilizadas para Inteligência Artificial (IA). O sistema utiliza a técnica de web scraping para coletar preços de placas de vídeo em diferentes países e exibe as informações de forma acessível para o usuário. A ferramenta permitirá aos usuários saber qual país oferece o preço mais barato para as placas de vídeo no momento da consulta, com a conversão do preço em tempo real para a moeda brasileira, o Real (R$). Além disso, o projeto será desenvolvido utilizando Python para backend e React JS para frontend.

# 1. Introdução
## 1.1. Contexto

Com o avanço da Inteligência Artificial e o aumento do uso de aprendizado de máquina, as placas de vídeo de alto desempenho tornaram-se peças essenciais para o desenvolvimento de IA. Esses componentes, especialmente as GPUs, são caros e a variação de preço pode ser significativa entre diferentes países e mercados. Portanto, existe uma demanda por uma ferramenta que ajude os consumidores a encontrar as melhores ofertas de placas de vídeo, considerando a flutuação de preços e as taxas de câmbio.

## 1.2. Justificativa

Este projeto é relevante para o campo da engenharia de software, pois envolve o uso de técnicas de web scraping para coletar informações de vários sites de e-commerce e comparar preços de maneira eficiente. Além disso, o uso de APIs para obter dados de câmbio e a implementação de um sistema de frontend interativo com React são tecnologias importantes para a formação de um engenheiro de software. O projeto oferece um exemplo prático de como integrar várias ferramentas e tecnologias para criar uma aplicação funcional e escalável.

## 1.3. Objetivos

*Objetivo Principal*: Desenvolver um sistema para monitoramento de preços de placas de vídeo de alto desempenho, fornecendo informações sobre o preço mais baixo em diferentes países e realizando a conversão para a moeda brasileira (R$).

*Objetivos Secundários*:

- Utilizar técnicas de web scraping para coletar informações de sites internacionais.

- Implementar a integração com APIs para conversão de moeda.

- Criar uma interface amigável para o usuário, utilizando React JS.

- Garantir que o sistema seja eficiente e escalável, lidando com grandes volumes de dados.

# 2. Descrição do Projeto
## 2.1. Tema do Projeto

O tema do projeto é a monitoramento de preços de placas de vídeo de alto desempenho (GPUs), com o objetivo de ajudar usuários a identificar as melhores ofertas em diferentes países. A aplicação utiliza técnicas de web scraping para extrair informações de preços de sites de e-commerce de diversos países e usa APIs de câmbio para converter os valores para reais.

## 2.2. Problemas a Resolver

- Variação de preços: Identificar a diferença de preços de placas de vídeo em diferentes sites de e-commerce e países.

- Conversão de moedas: Realizar a conversão de preços em diferentes moedas para reais, de forma automatizada.

- Interface de usuário: Criar uma interface fácil de usar e eficiente, permitindo ao usuário inserir filtros e visualizar os resultados de forma clara.

## 2.3. Limitações

- O sistema será limitado ao monitoramento de placas de vídeo de alto desempenho para IA, não abrangendo outros tipos de componentes de hardware.

- Não incluirá integração com todas as lojas do mercado, mas sim com um conjunto específico de sites que oferecem placas de vídeo.

- Alguns sites podem acabar bloqueando a utilização do bot para web scraping, assim dificultando a coleta de informações.

# 3. Especificação Técnica
## 3.1. Requisitos de Software

### Requisitos Funcionais (RF):

- RF1: O sistema deve permitir ao usuário buscar placas de vídeo por marca, modelo e especificações.

- RF2: O sistema deve realizar scraping de preços em tempo real de sites selecionados de e-commerce.

- RF3: O sistema deve converter os preços coletados para reais utilizando APIs de câmbio.

- RF4: O sistema deve exibir os resultados de forma organizada e fácil de entender.

### Requisitos Não-Funcionais (RNF):

- RNF1: O sistema deve ser eficiente no processamento de dados para garantir a experiência do usuário sem delays.

- RNF2: O sistema deve ser escalável para suportar o aumento de fontes de dados e número de usuários.

- RNF3: A interface deve ser intuitiva e responsiva, adaptando-se a diferentes dispositivos.

### Representação dos Requisitos:

Será criado um Diagrama de Casos de Uso (UML) para representar as interações do usuário com o sistema.

![Diagrama UML](https://github.com/user-attachments/assets/8d2da584-64a5-45c6-ad84-60ffbe69b75f)

## 3.2. Considerações de Design

*Visão Inicial da Arquitetura*: O sistema será composto por um backend desenvolvido em Python, utilizando web scraping para coletar dados e APIs para conversão de moedas, e um frontend em React JS para a apresentação das informações ao usuário.

*Padrões de Arquitetura*: O sistema seguirá o padrão MVC (Model-View-Controller) para separar claramente as responsabilidades entre a lógica de negócios, a interface do usuário e o controle dos dados.

*Modelos C4*: A arquitetura será detalhada em 4 níveis:

- *Nível de Contexto*: Mostra como o sistema interage com os usuários e fontes externas de dados.

![C4 Modelo - Contexto](https://github.com/user-attachments/assets/c785259d-2a88-4b49-84b1-8c31577ff302)

- *Nível de Contêineres*: Divide o sistema em componentes como backend, frontend, APIs e banco de dados.

![C4 Modelo - Conteiners](https://github.com/user-attachments/assets/31f19408-2a34-4593-a5cc-9fae43f9da8c)

- *Nível de Componentes*: Detalha os componentes principais do sistema, como o scraper, o conversor de moedas e a interface de usuário.

![C4 Modelo - Componentes](https://github.com/user-attachments/assets/ab14be2b-0b2e-4f93-995a-cbd274f06d3a)

- *Nível de Código*: Expõe detalhes de implementação e estrutura do código-fonte.

## 3.3. Stack Tecnológica

*Linguagens de Programação*: Python para backend e web scraping e React JS para frontend.

*Frameworks e Bibliotecas*: Flask (para backend), Requests e BeautifulSoup (para web scraping), Axios (para integração com APIs), React Router (para navegação no frontend).

*Ferramentas de Desenvolvimento*: GitHub (para versionamento de código), Docker (para contêinerização), Github Actions (para CI/CD), PostgreSQL (para armazenar dados de preços).

## 3.4. Considerações de Segurança

O sistema usará práticas de segurança recomendadas para garantir a proteção de dados, incluindo o uso de HTTPS para comunicação segura entre o frontend e o backend.

A coleta de dados será realizada de forma ética, respeitando as políticas dos sites de e-commerce.

## 4. Próximos Passos

Após a conclusão do documento, o cronograma será dividido em duas partes:

*Validação do Professor*: O documento será analisado pelo professor Diogo Winck para prosseguir pela Aprovação dos Professores

*Aprovação dos Professores*: O documento será aprovado por 3 professores para prosseguir para o desenvolvimento

*Portfólio I*: Planejamento da arquitetura e início da implementação do backend.

*Portfólio II*: Implementação do frontend, integração de todos os componentes e testes finais.

## 5. Referências

Requests: https://docs.python-requests.org/en/latest/

BeautifulSoup: https://www.crummy.com/software/BeautifulSoup/

React JS: https://reactjs.org/

Flask: https://flask.palletsprojects.com/

APIs de câmbio: https://www.exchangerate-api.com/
