---
title: "Planejamento CRISP-DM — Projeto Integrador - Grupo 2"
date: "24-08-2026"
options:
    theme: paper
---

# Planejamento CRISP-DM — Projeto Integrador

## 1. Business Understanding

### 1.1 Contexto do problema
O projeto tem como foco o monitoramento e controle de arboviroses, como dengue, zika e chikungunya, realizado pela GEVACZ e pela EMPREL no Recife. Nesse contexto, a vigilância entomológica utiliza Ovitrampas (OVTs) para monitorar a presença e a quantidade de ovos do Aedes aegypti e Estações Disseminadoras de Larvicida (EDLs) como estratégia de controle do vetor. O cenário estudado envolve aproximadamente 2.700 Ovitrampas distribuídas por 73 bairros e cerca de 700 EDLs utilizadas inicialmente no bairro de Casa Amarela.

Atualmente, os dados provenientes das atividades de campo são armazenados e manipulados principalmente por meio de arquivos CSV e planilhas Excel. Os dados das Ovitrampas e das EDLs permanecem separados, fazendo com que analistas e gestores precisem realizar cruzamentos e tratamentos manualmente. Esse processo aumenta a carga de trabalho, dificulta a análise espacial e temporal e pode introduzir erros durante a manipulação dos dados.

Além da limitação técnica do Excel para suportar operações de distância espacial, há uma lacuna na análise do contexto urbano. O controle vetorial ocorre no vácuo de variáveis socioambientais, ignorando como fatores de infraestrutura urbana afetam a eficácia das EDLs. Adicionalmente, pesquisas preliminares (Desk Research) apontam que dados entomológicos costumam apresentar o fenômeno estatístico da superdispersão (excesso de zeros e picos extremos), o que pode exigir abordagens analíticas mais robustas do que médias simples.

### 1.2 Pergunta de negócio
O problema de negócio identificado é a dificuldade de transformar os dados coletados pelas Ovitrampas e EDLs em informações integradas, georreferenciadas e cruzadas com indicadores socioambientais para a tomada de decisão. 

As perguntas que guiam este projeto são: 
1. Como automatizar e otimizar o cruzamento espacial entre OVT e EDL para reduzir o tempo de resposta das equipes de campo?
2. Como a variação temporal (ano a ano) nas condições de infraestrutura sanitária e vulnerabilidade social impacta a eficácia das ações de controle do vetor na cidade do Recife?

### 1.3 Público e uso pretendido
A resposta será destinada principalmente aos analistas epidemiológicos, especialistas em geoprocessamento, supervisores distritais de saúde e Agentes de Saúde Ambiental (ASACEs). 

As informações deverão ser utilizadas para apoiar a tomada de decisão, permitindo:
- identificar regiões com maior concentração ou aumento na quantidade de ovos;
- investigar possíveis correlações entre áreas de falha do larvicida e deficiências crônicas de infraestrutura sanitária;
- analisar espacialmente a distribuição das Ovitrampas e EDLs;
- auxiliar no direcionamento mais estratégico (Saúde Pública de Precisão) das equipes que atuam em campo.

### 1.4 Critérios de sucesso
O principal critério de sucesso será verificar se a solução consegue reduzir o tempo necessário para transformar os dados coletados em informações úteis para a tomada de decisão. Também será considerado sucesso a implementação de um pipeline de dados automatizado que integre com êxito os dados agregados de infraestrutura urbana como covariáveis de contexto, gerando um dataset pronto para testes estatísticos e visualizações dinâmicas.

---

## 2. Data Understanding

### 2.1 Quais agregados/variáveis do IBGE foram explorados
Para entender o impacto do contexto urbano na proliferação do vetor, foram selecionadas tabelas estratégicas da PNAD Contínua Anual (Características Gerais dos Domicílios e dos Moradores) via API do SIDRA/IBGE. A tabela trimestral de emprego (6469) foi descartada para evitar ruído estatístico, priorizando variáveis estruturais:
- **Eixo Saneamento e Água:** Tabelas 6731 (Fonte principal de água), 9468 (Rede geral de distribuição) e 7192 (Tipo de esgotamento sanitário). *Justificativa: Falhas no abastecimento forçam o armazenamento de água em recipientes (criadouros).*
- **Eixo Resíduos Sólidos:** Tabelas 6736 (Destino do lixo) e 6738 (Disponibilidade de coleta). *Justificativa: Acúmulo de lixo retém água da chuva.*
- **Eixo Adensamento e Estrutura:** Tabelas 6727 (Tipo de domicílio) e 6720 (Densidade de moradores).
- **Eixo Socioeconômico:** Tabelas 6407 (População por sexo e idade) e 7401 (Rendimento médio domiciliar per capita). 

*Nota metodológica: A seleção dessas variáveis baseia-se em premissas biológicas e achados do Desk Research. Um dos objetivos do projeto é testar a hipótese de que esses indicadores macro de saneamento e demografia têm impacto estatisticamente mensurável na eficácia das EDLs.*

### 2.2 Granularidade disponível (geográfica, temporal)
O projeto trabalhará com a integração de duas granularidades distintas:
- **Dados Primários (Micro):** Alta granularidade geográfica (coordenadas transformadas em células H3) e temporal (leituras a cada 15 dias para OVT e EDLs).
- **Dados Secundários (Macro):** Granularidade geográfica a nível de Município (Recife, geocódigo 2611606) e temporal Anual (série histórica da PNAD de 2018 a 2024). Essa abordagem cria um "contexto de vulnerabilidade municipal" correlacionado às flutuações anuais do vetor.

### 2.3 Problemas de qualidade identificados
- **Risco de Superdispersão e Zeros Excedentes:** Baseado na literatura de controle de vetores, suspeita-se que os dados de contagem de ovos apresentem muitos valores zerados misturados a picos extremos. Esse comportamento precisará ser validado durante a análise exploratória.
- **Distorção Espacial (MAUP):** O agrupamento atual de dados baseado nos limites oficiais dos bairros gera distorções analíticas que serão corrigidas com o uso da grade Uber H3.
- **Valores Ausentes na API:** Variáveis com amostragem insuficiente podem retornar valores nulos ou marcadores de confidencialidade pela API do IBGE, exigindo tratamento.

---

## 3. Data Preparation

### 3.1 Tratamentos necessários
- **Filtro de Variáveis de Ouro (API IBGE):** Para evitar multicolinearidade e ruído, o pipeline extrairá da API do SIDRA apenas as variáveis de "Distribuição percentual" e totais de referência, descartando ativamente todos os "Coeficientes de Variação" e "Erros Padrão". Também serão isoladas categorias específicas de risco (ex: % de lixo não coletado, % de uso de poços).
- **Indexação Espacial:** Substituição da métrica de bairros pela malha hexagonal H3 da Uber (resolução 8 ou 9), transformando as coordenadas em índices para otimizar os cruzamentos relacionais.
- **Integração das Bases:** Os dados operacionais de campo serão agregados temporalmente para permitir a junção relacional com a tabela de contexto macro (PNAD Anual).

---

## 4. Modeling

### 4.1 Formato final
O formato final será modelado em uma estrutura relacional (ex: PostgreSQL + PostGIS), separando os dados operacionais microespaciais dos dados contextuais macro. 

A estrutura lógica do dataset final unificado seguirá este padrão analítico:

| H3_Index | Ano/Mês | OVT_Contagem | EDL_Presença | Bairro_Aprox | Rendimento_Anual_Mun | Perc_Lixo_Inadequado_Mun |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 88a810... | 2024-03 | 145 | Sim | Casa Amarela | R$ 2.450 | 12.5% |
| 88a810... | 2024-03 | 0 | Sim | Casa Amarela | R$ 2.450 | 12.5% |
| 88a811... | 2024-03 | 320 | Não | Dois Irmãos | R$ 2.450 | 12.5% |

*Nota: Este formato preparará o dataset para testes estatísticos iniciais. O objetivo é permitir que a equipe valide a presença de superdispersão nos dados reais e cruze as métricas entomológicas com as covariáveis da PNAD, testando se os fatores de vulnerabilidade explicam as variações na eficácia do larvicida.*

---

## 5. Evaluation

### 5.1 Critérios que o grupo usará para considerar os dados "prontos"
Os dados serão considerados prontos quando atenderem aos seguintes critérios:
- **Performance de Cruzamento:** A consulta espacial cruzando OVTs e EDLs deve retornar resultados via índice H3 sem os travamentos experimentados no Excel.
- **Cobertura e Consistência:** A tabela dimensional da PNAD deve estar populada com a série histórica, e a soma total de armadilhas no banco deve bater com os registros originais da GEVACZ.
- **Tratamento de Ausentes:** Valores suprimidos da API ou falhas de leitura de campo devem estar mapeados e tratados (imputação ou descarte justificado).

---

## 6. Deployment

### 6.1 Como o pipeline deverá rodar de forma recorrente e versionamento
O pipeline deverá ser organizado em etapas automatizadas e versionado utilizando **Git/GitHub**, mantendo as diferentes versões dos scripts (extração, limpeza, formatação).

A estrutura de execução prevista será:

1. **Ingestão (Extract):** Scripts conectam-se à API do SIDRA (IBGE) e recebem os CSVs das OVTs/EDLs.
2. **Transformação (Transform):** Limpeza, filtro percentual, e conversão de LAT/LONG para H3.
3. **Carga (Load):** Inserção no banco de dados relacional e geração da base final.

Para a orquestração recorrente, o grupo avaliará o uso de ferramentas de CI/CD (ex: GitHub Actions) ou funções em nuvem (*serverless*), permitindo que os dados sejam reprocessados automaticamente sempre que novos ciclos de leitura quinzenais ou atualizações anuais da PNAD estiverem disponíveis, sem alterar os dados brutos originais.