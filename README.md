# Documentação do Projeto Final de ADS/SPI/CD

## Resumo do Projeto

Na cena musical local, existe uma carência de ferramentas digitais que centralizem informações sobre shows e eventos culturais, em especial os de artistas pequenos e/ou independentes. Atualmente, esses eventos dependem fortemente de redes sociais ou da divulgação boca a boca, o que dificulta seu alcance.  

Este projeto propõe uma plataforma web que permita a divulgação, organização e descoberta desses eventos de forma acessível e integrada. Com isso, busca-se ampliar o alcance de artistas e organizadores e facilitar o acesso do público interessado, criando um ecossistema mais conectado e eficiente.

## Definição do Problema

Muitos artistas independentes enfrentam dificuldades significativas para divulgar seu trabalho e alcançar o público interessado. Segundo o estudo *Musician’s Census 2024*, 54% dos músicos responderam que o maior obstáculo em sua carreira é “fazer com que sua música seja ouvida”.  

Shows ao vivo são a segunda maior fonte de renda para esses artistas (citada por 32% dos respondentes), o que evidencia a dependência de oportunidades presenciais para obtenção de receita. A falta de canais eficientes de divulgação limita o alcance de artistas independentes e dificulta a sustentabilidade financeira de sua atividade.

Atualmente, muitos artistas dependem de redes sociais, indicações boca a boca ou plataformas de streaming, que nem sempre fornecem visibilidade suficiente, especialmente para quem atua na cena local e de pequeno porte.  

Enquanto outras plataformas, como Facebook Events e Sympla, costumam utilizar algoritmos, engajamento e impulsionamento pago para gerar visibilidade, este projeto busca oferecer uma forma mais justa de divulgação, permitindo que mesmo eventos pequenos tenham um espaço garantido na plataforma, sem depender de popularidade prévia ou investimento em anúncios.

### Comparação com plataformas existentes

| Plataforma       | Público alvo    | Custo para organizadores                          | Foco em eventos locais | Promoção/Pagamento para visibilidade                                  |
|------------------|----------------|---------------------------------------------------|------------------------|------------------------------------------------------------------------|
| Facebook Events  | Geral          | Gratuito                                          | Baixo                  | Sim, via Facebook Ads e engajamento orgânico                           |
| Sympla           | Geral          | Recursos pagos, taxa sobre venda de ingressos     | Médio                  | Sim, planos de promoção e integração com anúncios externos             |
| Projeto Proposto | Local/cultural | Gratuito                                          | Alto                   | Não, visibilidade igual para todos os eventos, inclusive os pequenos   |

## Objetivos

**Objetivo Geral**  
Desenvolver uma plataforma web que centralize a divulgação e descoberta de shows e eventos culturais locais, aumentando o alcance de artistas e a acessibilidade para o público interessado.

**Objetivos Específicos**
- Criar um sistema de cadastro e gerenciamento de eventos.  
- Permitir a pesquisa e filtragem de eventos por data, localização e características (preço, área, gratuidade).  
- Proporcionar uma interface simples e intuitiva para usuários finais.  
- Garantir persistência dos dados de forma segura em banco de dados relacional.  
- Validar a solução com potenciais usuários da cena cultural.  
- Construir uma “biblioteca” de casas de show e espaços de evento locais para uso recorrente nos cadastros.

## Stack Tecnológico

- **Backend:** FastAPI (Python) com Pydantic v2 para validação, SQLAlchemy como ORM síncrono e `pg8000` como driver PostgreSQL.  
- **Banco de Dados:** PostgreSQL.  
- **Frontend Web:** Páginas HTML estáticas utilizando Tailwind CSS via CDN, Alpine.js para interatividade e JavaScript nativo com `fetch` para integração com a API REST.  
- **Autenticação:** Tokens de sessão HTTP Bearer, armazenamento de sessões em tabela dedicada e uso de `localStorage` no frontend para manter o estado do usuário.  
- **Ferramentas de desenvolvimento:** Uvicorn com reload, Watchfiles e Python-dotenv para carregamento de variáveis de ambiente.  
- **Versionamento de código:** Git/GitHub.  

## Descrição da Solução

A solução é disponibilizada como uma aplicação web composta por um backend em FastAPI e um frontend estático consumindo a API. O backend gerencia:
- Cadastro, autenticação e sessão de usuários;  
- Cadastro e consulta de eventos, estabelecimentos, gêneros e artistas;  
- Persistência dos dados em PostgreSQL por meio do SQLAlchemy.  

Os usuários podem registrar novos eventos e estabelecimentos por meio de formulários dedicados no frontend (páginas em HTML/Tailwind/Alpine.js), além de utilizar a documentação interativa da API (Swagger) para testes técnicos.  

O sistema mantém os dados persistentes entre sessões, garantindo que os eventos cadastrados fiquem disponíveis mesmo após reinícios da aplicação.

### Exemplos de telas e fluxos
Fluxo de funcionamento
<img width="988" height="462" alt="diagram-export-11-12-2025-20_23_11" src="https://github.com/user-attachments/assets/a27064f9-876a-4d69-bf5e-cced2f88c4af" />


Tela inicial, home
<img width="1914" height="919" alt="image" src="https://github.com/user-attachments/assets/dd9bb955-bfe7-467d-99d5-7ab903529e55" />


### Funcionalidades implementadas (versão atual)

- Cadastro, autenticação e gestão de usuários com tokens de sessão persistidos em banco de dados.  
- CRUD completo de **eventos**, **estabelecimentos**, **gêneros** e **artistas**, com associações N:N entre eventos, gêneros e artistas.  
- Páginas públicas para **listagem**, **busca** e **detalhamento** de eventos, incluindo filtros por palavra‑chave, bairro/cidade, intervalo de datas, faixa de preço e opção de “somente gratuitos”.  
- Formulários guiados para criação de eventos e estabelecimentos, com reaproveitamento de locais já cadastrados pelo organizador.  
- Painel do organizador (“Meu painel”) com visão rápida dos eventos e estabelecimentos do próprio usuário autenticado.  
- Páginas específicas para gestão avançada de eventos e estabelecimentos do usuário.
- Mecanismo simples de migração de colunas de localização e proprietário no banco de dados, via funções internas do backend, mantendo compatibilidade com bases já existentes.  

## Arquitetura

A arquitetura atual é composta por:
- Um serviço backend FastAPI (monolítico) responsável pela API REST, autenticação, regras de negócio e acesso ao banco de dados;  
- Um banco de dados PostgreSQL acessado via SQLAlchemy;  
- Um frontend web estático (HTML + Tailwind + Alpine.js) que consome a API por meio de `fetch` e gerencia estado de autenticação via JavaScript.  

Artefatos já trabalhados ou em desenvolvimento:
- Benchmarking com plataformas existentes;  
- Definição do problema e canvas inicial;  
- Casos de uso e backlog inicial (cadastro de eventos, listagem, pesquisa);  
- Protótipo inicial da API com Swagger;  
- Primeira versão de frontend responsivo com páginas públicas e painéis de conta/admin.  

 

## Conclusões

O projeto visa solucionar a lacuna de divulgação de eventos culturais locais por meio de uma plataforma dedicada, acessível e gratuita. A expectativa é que o sistema facilite a descoberta de eventos, aumente o alcance de artistas e organizadores e contribua para fortalecer a cena cultural independente.

**Limitações (escopo atual):**
- O foco geográfico está na região da Grande Porto Alegre e arredores.  

**Perspectivas Futuras:**
- Integração com APIs externas (por exemplo, Spotify, Google Maps) para enriquecer as informações dos eventos.  
- Criação de aplicativo mobile como cliente adicional da API.  
- Expansão para eventos de outras cidades e regiões.  
- Ferramentas avançadas para curadoria, moderação e destaques editoriais.  

## Referências Bibliográficas

- Right Chord Music Group, *Musicians Census*: https://www.rightchordmusic.com/musicians-census  
- Documentação oficial FastAPI: https://fastapi.tiangolo.com/  
- Documentação oficial PostgreSQL: https://www.postgresql.org/  
