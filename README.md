
# Documentação do Projeto Final de ADS/SPI/CD

## Resumo do Projeto

Na cena musical local, existe uma carência de ferramentas digitais que centralizem informações sobre shows e eventos culturais, em especial os de artistas pequenos e/ou independentes. Atualmente, esses eventos dependem fortemente de redes sociais ou da divulgação boca a boca, o que dificulta seu alcance. A solução proposta é o desenvolvimento de uma plataforma web que permita a divulgação, organização e descoberta desses eventos de forma acessível e integrada. Com isso, espera-se ampliar o alcance dos artistas e organizadores e facilitar o acesso do público interessado, criando um ecossistema mais conectado e eficiente.


## Definição do Problema

Muitos artistas independentes enfrentam dificuldades significativas para divulgar seu trabalho e alcançar o público interessado. Segundo o estudo *Musician’s Census 2024*, 54% dos músicos responderam que o maior obstáculo em sua carreira é "fazer com que sua música seja ouvida". Além disso, shows ao vivo são a segunda maior fonte de renda para os artistas, sendo citados por 32% dos respondentes, o que evidencia a dependência de oportunidades presenciais para obtenção de receita.  

Esses dados indicam que a falta de canais eficientes de divulgação limita o alcance de artistas independentes e dificulta a sustentabilidade financeira de sua atividade. Atualmente, muitos artistas dependem de redes sociais, indicações boca a boca ou plataformas de streaming, que nem sempre fornecem visibilidade suficiente, especialmente para quem atua na cena local e de pequeno porte.  

Enquanto outras plataformas, como Facebook Events e Sympla, costumam utilizar algoritmos, engajamento de usuários e impulsionamento pago para gerar visibilidade em eventos, este projeto busca fornecer uma maneira mais justa de divulgação, permitindo que até mesmo eventos pequenos e sem muita divulgação possuam um espaço garantido na plataforma. Dessa forma, todos os eventos têm visibilidade igualitária, sem depender de recursos financeiros ou popularidade prévia.  

### Comparação com plataformas existentes

| Plataforma       | Público alvo    | Custo para organizadores | Foco em eventos locais | Promoção/Pagamento para visibilidade |
|------------------|----------------|-------------------------|-----------------------|-------------------------------------|
| Facebook Events  | Geral          | Gratuito                | Baixo                 | Sim, via Facebook Ads e engajamento |
| Sympla           | Geral          | Recursos pagos, taxa em vendas de ingresso| Médio                 | Sim, planos de promoção e integração com anúncios externos |
| Projeto Proposto | Local/cultural | Gratuito                | Alto                  | Não, visibilidade igual para todos os eventos, inclusive pequenos e sem divulgação |




## Objetivos

**Objetivo Geral**  
Desenvolver uma plataforma web que centralize a divulgação e descoberta de shows e eventos culturais locais, aumentando o alcance de artistas e a acessibilidade para o público interessado.

**Objetivos Específicos**
- Criar um sistema de cadastro e gerenciamento de eventos.  
- Permitir a pesquisa e filtragem de eventos por data, localização e categoria.  
- Proporcionar uma interface simples e intuitiva para usuários finais.  
- Garantir persistência dos dados de forma segura em banco de dados.  
- Validar a solução com potenciais usuários da cena cultural.  
- Construir uma "biblioteca" de casas de evento/shows locais e para inclusão no site

## Stack Tecnológico

- **Backend:** FastAPI (Python)  
- **Banco de Dados:** PostgreSQL  


- **Versionamento de Código:** GitHub  


*(stack tecnologico será expandido ao decorrer do desenvolvimento do projeto)*

## Descrição da Solução

A solução será disponibilizada como uma aplicação web. O backend desenvolvido em FastAPI gerencia o cadastro de eventos, autenticação de usuários e persistência em PostgreSQL. Os usuários podem registrar novos eventos por meio de uma interface simples (Swagger para testes de API e, futuramente, frontend dedicado).  

O sistema mantém os dados persistentes entre sessões, garantindo que os eventos cadastrados fiquem disponíveis mesmo após reinícios da aplicação. 

### Exemplos de telas e fluxos
*(espaço reservado para protótipos, mockups ou screenshots do sistema futuramente)*  

## Arquitetura

A arquitetura segue um modelo baseado em microsserviços simples, com backend independente, banco de dados e integração futura com frontend.  

Artefatos já trabalhados ou em desenvolvimento:
- Benchmarking com plataformas existentes  
- Definição do problema e canvas inicial  
- Casos de uso e backlog inicial (cadastro de eventos, listagem, pesquisa)  
- Protótipo inicial de API com Swagger  

  

## Validação

### Estratégia
A validação será realizada em duas etapas:
1. **Testes técnicos** – validação funcional da API (cadastro, edição, listagem de eventos).  
2. **Pesquisa com usuários potenciais** – aplicação de questionário e entrevistas com artistas e frequentadores locais para avaliar usabilidade e relevância da solução.  

### Consolidação dos Dados Coletados
Os dados coletados serão organizados em gráficos e tabelas comparativas, analisando métricas de facilidade de uso, interesse na plataforma e potencial de adoção.  

## Conclusões

O projeto visa solucionar a lacuna de divulgação de eventos culturais locais através de uma plataforma dedicada, acessível e gratuita. Ao final, espera-se que o sistema facilite a descoberta de eventos e aumente o alcance de artistas e organizadores.  

**Limitações:**  
- Funcionalidades como compra de ingressos ou integração com redes sociais estão fora do escopo inicial.  
- Os eventos do site terão foco em grande Porto Alegre e região próxima

**Perspectivas Futuras:**  
- Integração com APIs externas (Spotify, Google Maps).  
- Criação de aplicativo mobile.  
- Expansão para eventos de outras cidades e regiões

## Referências Bibliográficas

- Right Chord Music group, Musician Census: https://www.rightchordmusic.com/musicians-census
- Documentação oficial FastAPI: https://fastapi.tiangolo.com/  
- Documentação oficial PostgreSQL: https://www.postgresql.org/  
