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

Além disso, o volume de dados e a necessidade de realizar cálculos espaciais tornam o uso de planilhas inadequado para determinadas operações. O cruzamento entre a localização das Ovitrampas e das EDLs pode exigir grande quantidade de cálculos de distância, resultando em lentidão e travamentos.

Dessa forma, o projeto busca estruturar uma solução capaz de integrar os dados coletados em campo, permitir análises espaciais e temporais e fornecer informações que apoiem decisões mais rápidas e direcionadas pelas equipes responsáveis pelo controle do vetor.

### 1.2 Pergunta de negócio
O problema de negócio identificado é a dificuldade de transformar os dados coletados pelas Ovitrampas e pelas EDLs em informações integradas e úteis para a tomada de decisão operacional.

Atualmente, profissionais da GEVACZ dependem de processos manuais para combinar diferentes fontes de dados. Como consequência, a análise pode levar semanas, dificultando a identificação de regiões que necessitam de atenção e o direcionamento das equipes de campo.

O projeto pretende, portanto, reduzir o esforço manual e o tempo necessário para analisar os dados, permitindo que os responsáveis pelo monitoramento tenham uma visão espacial e temporal mais integrada da situação.

### 1.3 Público e uso pretendido
A resposta será destinada principalmente aos analistas epidemiológicos, especialistas em geoprocessamento, supervisores distritais de saúde e Agentes de Saúde Ambiental (ASACEs) envolvidos no monitoramento e controle do Aedes aegypti. Esses profissionais foram identificados no Desk Research como os principais usuários afetados pelo processo atual.

As informações deverão ser utilizadas para apoiar a tomada de decisão, permitindo:
- identificar regiões com maior concentração ou aumento na quantidade de ovos;
- acompanhar a evolução dos dados ao longo do tempo;
- analisar espacialmente a distribuição das Ovitrampas e EDLs;
- avaliar possíveis relações entre a atuação das EDLs e a quantidade de ovos observada;
- auxiliar no direcionamento das equipes que atuam em campo.

O objetivo é substituir parte do processo atual, baseado no cruzamento manual de planilhas, por uma análise integrada capaz de gerar informações mais rápidas para os responsáveis pela operação. O Desk Research identifica justamente a ausência de uma ferramenta que realize automaticamente o cruzamento entre os dados das Ovitrampas e das EDLs.

### 1.4 Critérios de sucesso
O principal critério de sucesso será verificar se a solução consegue reduzir o tempo necessário para transformar os dados coletados em informações úteis para a tomada de decisão e para o direcionamento das equipes de campo.

Também será considerado indicativo de sucesso que a solução permita integrar os dados das Ovitrampas e das EDLs e realizar análises espaciais e temporais de maneira mais eficiente do que o processo atual baseado em planilhas. O resultado deverá contribuir para reduzir o esforço manual dos analistas e fornecer informações que possam ser utilizadas para direcionar as ações de controle do vetor.

## 2. Data Understanding

### 2.1 Quais agregados/variáveis do IBGE foram explorados
Exploramos a PNAD Contínua, principalmente a Tabela 6469, que apresenta informações sobre o rendimento médio mensal das pessoas ocupadas. A intenção era utilizar esses dados como uma variável socioeconômica no projeto.
### 2.2 Granularidade disponível (geográfica, temporal)
A principal limitação encontrada foi a granularidade geográfica. Os dados da PNAD são disponibilizados em níveis mais agregados, como Brasil, Grandes Regiões e Estados, não permitindo representar diretamente o município do Recife ou seus bairros.

Apesar de a PNAD possuir informações ao longo do tempo, a escala geográfica disponível não atende ao objetivo do nosso estudo.
### 2.3 Problemas de qualidade identificados
2.3 Problemas de qualidade identificados

O problema identificado não está na qualidade dos dados, mas na inadequação da escala geográfica. Como nosso estudo é focado na cidade do Recife, utilizar dados referentes a Pernambuco não representaria as diferenças socioeconômicas existentes dentro do município.

Por isso, decidimos buscar outras fontes de dados específicas para o Recife, principalmente aquelas disponibilizadas pelo Estado e pela Prefeitura, que apresentem uma granularidade mais adequada ao nosso estudo.

## 3. Data Preparation

### 3.1 Tratamentos necessários
Após a escolha das bases, será necessário realizar a padronização e integração dos dados. Para o Censo 2022, os dados de rendimento e demais variáveis socioeconômicas deverão ser tratados para garantir que os valores estejam em formatos numéricos e que não existam inconsistências ou duplicidades.

Também será necessário realizar o tratamento dos dados espaciais, verificando os sistemas de coordenadas e garantindo que as geometrias estejam corretas para o cruzamento com a grade H3.

Em seguida, os dados socioeconômicos serão relacionados espacialmente às células H3 utilizadas no projeto. Também serão tratados valores ausentes e possíveis inconsistências, além de serem criadas as variáveis necessárias para a etapa de modelagem.

## 4. Modeling

### 4.1 Formato final
O conjunto final deverá ser estruturado de forma que cada registro represente uma célula H3 em um determinado período de análise.

As variáveis poderão incluir informações como:

quantidade de OVTs;
presença ou quantidade de EDLs;
distância até EDLs;
rendimento da área;
população;
variáveis ambientais, como chuva;
período de análise;
outras variáveis de controle definidas durante o projeto.
Dessa forma, a base final terá uma estrutura semelhante a:

| H3     | Período  | OVTs | EDLs | Rendimento | População | Chuva |
| ------ | -------- | ---: | ---: | ---------: | --------: | ----: |
| H3_001 | Jan/2025 |   12 |    2 |      2.500 |     1.200 |   180 |
| H3_002 | Jan/2025 |    7 |    0 |      4.100 |       950 |   180 |
| H3_001 | Fev/2025 |   15 |    2 |      2.500 |     1.200 |   220 |

Essa estrutura permitirá posteriormente aplicar o modelo estatístico escolhido pelo grupo, considerando tanto a dimensão espacial quanto temporal dos dados.

## 5. Evaluation

### 5.1 Critérios que o grupo usará para considerar os dados "prontos"
Os dados serão considerados prontos quando atenderem aos seguintes critérios:

Cobertura espacial: todos os registros deverão estar corretamente associados às células H3 do território analisado.
Cobertura temporal: os períodos necessários para a análise deverão estar disponíveis e padronizados.
Consistência: não deverão existir duplicidades ou valores incompatíveis entre as diferentes bases.
Dados ausentes: valores ausentes deverão estar identificados e tratados de acordo com sua importância para cada variável.
Integração: as diferentes fontes deverão estar corretamente relacionadas por meio das informações espaciais e temporais.
Validação: os resultados dos cruzamentos espaciais deverão ser verificados para evitar associações incorretas entre bairros, setores censitários e células H3.

Assim, o conjunto será considerado pronto quando apresentar dados consistentes, integrados e suficientemente completos para a aplicação do modelo.

## 6. Deployment

### 6.1 Como o pipeline deverá rodar de forma recorrente; como o código será versionado
O pipeline deverá ser organizado em etapas, permitindo que os dados sejam processados novamente sempre que uma nova atualização das bases estiver disponível.

A estrutura prevista será:

Dados brutos
     ↓
Limpeza e padronização
     ↓
Tratamento espacial
     ↓
Integração das bases
     ↓
Agregação para H3
     ↓
Base final
     ↓
Modelagem
     ↓
Resultados

O código será versionado utilizando Git, mantendo as diferentes versões dos scripts e registrando as alterações realizadas durante o desenvolvimento. Os dados brutos não deverão ser modificados diretamente, permitindo que o pipeline seja reproduzido a partir das fontes originais.

Sempre que uma nova versão dos dados for disponibilizada, o pipeline poderá ser executado novamente para gerar uma nova versão da base final e dos resultados.