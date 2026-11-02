# Simulador de Pesos

Ferramenta de apoio à avaliação de qualidade de uma Revisão Sistemática da Literatura (RSL). Ela mostra como diferentes pesos nas questões do questionário alteram a pontuação das publicações e quais delas ficam acima da nota de corte, sem refazer a avaliação.

Foi desenvolvida para o Trabalho de Conclusão de Curso *Prototipação de Interfaces com Suporte de Inteligência Artificial em Processos Ágeis: Uma Revisão Sistemática da Literatura*, de Gilberto Aparecido Dias Junior, no curso de Engenharia de Software da Universidade de Rio Verde (UniRV). O uso da ferramenta é descrito na seção "Simulador de pesos" do trabalho.

## Arquivos

| Arquivo | Finalidade |
|---|---|
| `app_pesos.py` | Aplicação interativa em Streamlit, com um controle deslizante por questão (0,0 a 5,0, em passos de 0,5) e ajuste da nota de corte |
| `simulador_pesos.py` | Versão por linha de comando. Os pesos são definidos em `PESOS_SIMULACAO`, e o resultado é salvo em uma planilha `.xlsx` |

## Como a pontuação é calculada

Cada resposta vale SIM = 1,0, PARCIAL = 0,5 e NÃO = 0,0. A pontuação ponderada, na escala de 0 a 10, é:

```text
pontuação = (soma de resposta × peso) / (soma dos pesos) × 10
```

A aplicação em Streamlit também oferece um modo que soma os valores ponderados sem dividir pela soma dos pesos.

Na versão final do trabalho, Q2, Q3, Q5, Q9 e Q10 receberam peso 2,50, as demais questões receberam peso 1,00, e a nota de corte foi 6,0. Os valores de `PESOS_SIMULACAO` no código são apenas um exemplo de simulação, e não esses pesos finais.

## Instalação

Requer Python 3.

```bash
pip install -r requirements.txt
```

## Dados de entrada

Os dados da avaliação não acompanham este repositório. Os dois programas procuram o arquivo mais recente que siga este caminho, a partir da pasta do projeto:

```text
ResultadoQualidade/<execução>/consolidado_completo.csv
```

O CSV deve estar em UTF-8 e ter as colunas `q1` a `q10`, com os valores SIM, PARCIAL ou NÃO, além das colunas de identificação das publicações, como `arquivo`, `base` e `titulo`.

## Execução

Aplicação interativa:

```bash
streamlit run app_pesos.py
```

Linha de comando:

```bash
python simulador_pesos.py
```
