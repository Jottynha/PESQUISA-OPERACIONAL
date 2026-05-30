<div align="center">

<img src="https://cdn.simpleicons.org/python/3776AB" alt="Python" width="72" />

# Pesquisa Operacional

<p>
	Reprodução de formulações de Otimização Combinatória com validação por meio do Gurobi.
</p>

<p>
	<b>João Pedro Rodrigues Silva</b><br />
	Disciplina: <b>Pesquisa Operacional</b> — Campus V do CEFET-MG
</p>

<table>
	<tr>
		<td><b>Artigo</b></td>
		<td><i>A new mixed integer linear programming model for the multi level uncapacitated facility location problem</i></td>
	</tr>
	<tr>
		<td><b>Autores</b></td>
		<td>Kratica, Dugošija e Savić</td>
	</tr>
	<tr>
		<td><b>Ano</b></td>
		<td>2014</td>
	</tr>
	<tr>
		<td><b>Solver</b></td>
		<td>Gurobi via <code>gurobipy</code></td>
	</tr>
</table>

</div>

## Visão geral

Este projeto tem como finalidade reproduzir, em ambiente computacional, a formulação MILP apresentada no artigo selecionado para o **Multi-Level Uncapacitated Facility Location Problem (MLUFLP)**.

Em termos operacionais, o problema consiste em determinar:

- quais instalações devem ser abertas em cada nível da hierarquia;
- por quais instalações cada cliente será atendido;
- qual configuração minimiza o custo total, considerando **custos fixos** de abertura e **custos de transporte** entre níveis.

A implementação foi desenvolvida em Python, utilizando a API do Gurobi, e validada com a instância de exemplo disponibilizada no próprio artigo.

## Problema abordado

O MLUFLP generaliza o problema clássico de localização de facilidades. Nesse contexto, a solução não se limita à escolha de uma única instalação para atender cada cliente; ela deve construir um **caminho de atendimento** que percorre níveis consecutivos da rede.

No artigo utilizado neste projeto:

- existem níveis hierárquicos de instalações;
- os clientes estão no último nível do grafo de atendimento;
- cada cliente deve ser conectado por um caminho viável até as instalações abertas;
- a abertura de uma instalação implica custo fixo;
- a utilização de uma ligação entre dois nós implica custo de transporte.

Desse modo, o objetivo consiste em encontrar a combinação de aberturas e conexões que produza o menor custo total.

## Formulação implementada

A formulação adotada no artigo emprega duas famílias principais de variáveis.

### Variáveis de decisão

<table>
	<tr>
		<th>Variável</th>
		<th>Significado</th>
	</tr>
	<tr>
		<td><code>y[i]</code></td>
		<td>Assume valor 1 se a instalação no sítio <code>i</code> for aberta; caso contrário, assume valor 0.</td>
	</tr>
	<tr>
		<td><code>z[i,j]</code></td>
		<td>Representa o fluxo ou a utilização da ligação do nó <code>j</code> para o nó <code>i</code>, entre níveis consecutivos.</td>
	</tr>
</table>

### Função objetivo

O modelo minimiza a soma de dois componentes:

1. **Custos fixos** associados à abertura de instalações;
2. **Custos de transporte** associados às ligações utilizadas no caminho de cada cliente.

Em forma resumida:

$$
\min \sum_{i \in F} f_i y_i + \sum c_{ij} z_{ij}
$$

### Restrições

O modelo implementado no código segue a estrutura descrita a seguir:

- **Atribuição de clientes:** cada cliente deve ser atendido por exatamente um caminho viável.
- **Conservação de fluxo:** o fluxo que entra em um nó de um nível deve ser igual ao fluxo que sai para o nível subsequente.
- **Ligação com instalações abertas:** somente é permitido utilizar uma ligação quando a instalação de origem estiver aberta.
- **Domínio das variáveis:** `y[i]` é binária e `z[i,j]` é contínua não negativa.

Essas restrições asseguram que a solução obtida seja factível e represente, para cada cliente, um caminho completo de atendimento.

## Resultados do exemplo do artigo

O projeto inclui a instância de validação do artigo em `data/article_example.json`.

Para essa instância, obteve-se:

- **valor ótimo encontrado:** `329`
- **instalações abertas:** `Fac2`, `Fac3` e `Fac5`
- **sequência de atendimento:**
	- `Client1`: `Fac2 -> Fac3 -> Client1`
	- `Client2`: `Fac2 -> Fac3 -> Client2`
	- `Client3`: `Fac2 -> Fac5 -> Client3`
	- `Client4`: `Fac2 -> Fac3 -> Client4`
	- `Client5`: `Fac2 -> Fac3 -> Client5`

O resultado coincide com o exemplo reportado no artigo, indicando que a formulação foi reproduzida de maneira consistente.

## Como executar

```bash
python3 -m pip install -r requirements.txt
python3 src/mluflp_gurobi.py --check-optimal
```

Se o Gurobi estiver configurado corretamente, o script deverá retornar o valor objetivo `329` e confirmar a validação do exemplo.

## Estrutura do projeto

<table>
	<tr>
		<th>Arquivo</th>
		<th>Função</th>
	</tr>
	<tr>
		<td><code>src/mluflp_gurobi.py</code></td>
		<td>Responsável por carregar a instância, formular o modelo e resolver com Gurobi.</td>
	</tr>
	<tr>
		<td><code>data/article_example.json</code></td>
		<td>Instância numérica utilizada para validar a formulação implementada.</td>
	</tr>
	<tr>
		<td><code>requirements.txt</code></td>
		<td>Dependência Python necessária para utilização da API do Gurobi.</td>
	</tr>
</table>

## Observação

Este projeto foi estruturado para apoiar a apresentação e a arguição individual. Caso deseje, posso, em seguida, adaptar o texto para um formato ainda mais acadêmico, com introdução, metodologia, implementação e conclusão em estilo de relatório.

