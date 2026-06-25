\# Object Calisthenics: Cheat Sheet



Este documento descreve as 9 regras do \*\*Object Calisthenics\*\*, focadas em melhorar o design de código, a manutenibilidade e a legibilidade através de restrições rígidas de refatoração.



\---



\### 1. Um nível de indentação por método

Reduza a complexidade extraindo lógica aninhada para novos métodos.

\- \*\*Objetivo:\*\* Métodos curtos, focados e com baixa complexidade ciclomática.



\### 2. Não use a palavra-chave `else`

Utilize \*Early Returns\* (retorno antecipado) ou Polimorfismo.

\- \*\*Objetivo:\*\* Reduzir ramificações mentais e evitar o "código em flecha".



\### 3. Envolva todos os tipos primitivos e Strings

Transforme tipos básicos em \*\*Value Objects\*\* (ex: `Email`, `Preco`, `CPF`).

\- \*\*Objetivo:\*\* Combater a "Obsessão por Primitivos" e centralizar validações.



\### 4. Coleções de primeira classe

Qualquer classe que contenha uma coleção não deve possuir outros atributos.

\- \*\*Objetivo:\*\* Encapsular comportamentos de filtros e manipulações da lista.



\### 5. Um ponto por linha

Não encadeie chamadas que exponham a estrutura interna de outros objetos (Lei de Demeter).

\- \*\*Regra:\*\* `objeto.facaAlgo()`, nunca `objeto.getOutro().getMaisUm().facaAlgo()`.



\### 6. Não abrevie

Nomes de classes, métodos e variáveis devem ser claros e autoexplicativos.

\- \*\*Dica:\*\* Se o nome é longo demais para não ser abreviado, a classe provavelmente tem responsabilidades demais.



\### 7. Mantenha as entidades pequenas

Limites sugeridos:

\- Classes: Máximo de \*\*50 linhas\*\*.

\- Pacotes: Máximo de \*\*10 arquivos\*\*.

\- \*\*Objetivo:\*\* Forçar a alta coesão.



\### 8. No máximo duas variáveis de instância por classe

Reduza o estado das classes decompondo-as em objetos menores.

\- \*\*Objetivo:\*\* Minimizar o acoplamento e facilitar o reaproveitamento.



\### 9. Sem Getters, Setters ou Propriedades Públicas

Aplique o princípio \*\*"Tell, Don't Ask"\*\* (Diga, não pergunte).

\- \*\*Objetivo:\*\* Manter o comportamento junto com os dados e evitar o "Anemic Domain Model".



\---



> \*\*Nota: Estas regras são exercícios. Em produção, use o bom senso, mas tente segui-las ao máximo para desenvolver um "instinto" de código limpo.\*\*

