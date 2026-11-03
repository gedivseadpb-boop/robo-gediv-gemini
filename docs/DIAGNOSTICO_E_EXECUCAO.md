# Diagnóstico e execução — piloto do Robô GEDIV

Atualização: 31/10/2026. Este registro acompanha a branch de desenvolvimento, com base no checklist operacional, especificação V3, código do repositório e versões anteriores disponíveis.

**Atualização posterior, 20h34:** a conexão manual ao serviço privado foi comprovada com três lotes e 18 registros reais; o estado passou de 310 para 328 registros. O reenvio não duplicou dados. O [registro de conexão manual](CONEXAO_MANUAL.md) atualiza as descrições históricas de site estático nas seções abaixo: a API publicada agora persiste lotes e recompõe o painel. A coleta autônoma, leitura integral, OCR e homologação continuam pendentes.

## Objetivo e arquitetura

Buscar publicações oficiais da GEDIV, preservar a evidência e produzir um painel gerencial com acesso protegido. O fluxo alvo é: inventário de edições e suplementos → PDF oficial → texto/OCR → candidatos → revisão e vínculo de alterações → base privada versionada → painel e exportação autorizados.

A arquitetura do piloto reaproveita o coletor Python e o painel gerencial já existentes. A branch gera um HTML privado independente a partir do estado do coletor. Uma [cópia estática de conferência](https://gediv-conferencia-privada-20261031.ylenaluna.chatgpt.site) foi publicada com acesso restrito à conta proprietária; essa hospedagem não atualiza a coleta nem implementa revisão multiusuário. Banco/API, identidade para equipe e rotina de atualização permanecem como parte futura da solução.

## Antes e alterações desta branch

| Área | Antes observado | Depois implementado nesta branch | Evidência e limite |
|---|---|---|---|
| Fila | Estado `PROCESSADO COM PENDÊNCIAS` era tratado como completo por prefixo | Somente `PROCESSADO` sem pendências é completo; parcial volta à fila | Teste isolado; falta coleta real |
| Falha de nova tentativa | Recuperação incompleta, com risco de perda ou estado impreciso | Conserva registros anteriores e deixa a edição pendente | Teste isolado de falha simulada |
| PDF substituído | Dados da mesma URL podiam ser sobrescritos | Guarda snapshot anterior e exige revisão de versão alterada | Teste local; não guarda ainda uma cópia imutável do PDF |
| Fonte | Checagem por prefixo e redirecionamentos automáticos | Valida HTTPS, hostname, credenciais, porta e cada redirecionamento | Testes isolados; falta teste real no portal |
| Blocos na mesma coluna | O primeiro cabeçalho da GEDIV podia encerrar a leitura antes de outras resenhas da mesma unidade | Percorre cabeçalhos repetidos e interrompe em limites de outras unidades | Testes com PDF sintético e conferência limitada de recorte textual indexado; falta comparar com o PDF completo |
| OCR sem linhas identificadas | A releitura da página inteira podia atribuir um processo de outra área ao bloco GEDIV | Não atribui texto amplo a um bloco e mantém página OCR como pendente | Teste sintético; é necessário implementar releitura restrita por região e conferir a qualidade em português |
| Indicadores | HTML anterior podia incluir candidatos nos cartões | Apenas registros marcados como conferidos são contabilizados; candidatos têm lista própria | Teste do conversor e amostra anterior, ainda sem aprovação da GEDIV |
| Painel | Interface gerencial e coletor separados | Geração de `painel_gerencial_privado.html` pelo coletor | Testar com saída real e decisões revisadas |
| Revisão | Sem procedimento rastreado no coletor | Utilitário de revisão de JSON local, com responsável, justificativa, fonte, página e hash | Não é uma plataforma de revisão multiusuário nem controle de acesso |
| Automação | Últimas execuções conhecidas do fluxo principal foram puladas | Workflow de piloto separado e restrito à branch privada | A execução precisa ser observada; não equivale à rotina diária |

## Teste real proposto

O workflow de piloto tenta obter uma edição da fonte oficial, processá-la em arquivos temporários e gerar um artefato do repositório privado por até 3 dias. Não grava o estado em banco ou na `main`, nem carrega automaticamente candidatos em indicadores. A leitura de todas as páginas e a qualidade dos resultados devem ser avaliadas no resultado efetivo; timeout ou falha de acesso deve permanecer como falha, nunca como ausência de publicação.

Na [primeira execução](https://github.com/gedivseadpb-boop/robo-gediv-pb/actions/runs/41233068223), as dependências e os testes da branch passaram no GitHub; a conexão ao PDF de 10/10/2026 expirou, portanto não houve leitura nem artefato de painel. Na [segunda execução](https://github.com/gedivseadpb-boop/robo-gediv-pb/actions/runs/41233491203), 17 testes passaram no GitHub, mas as conexões aos dois PDFs selecionados e ao catálogo público da CGE expiraram. Isso descreve o acesso a partir dos runners naquele momento e não demonstra indisponibilidade para outros usuários. A equivalência e a cobertura do catálogo da CGE não foram comprovadas.

Uma consulta posterior ao conteúdo textual indexado da [edição oficial de 11/03/2026](https://auniao.pb.gov.br/servicos/doe/2026/marco/diario-oficial-11-03-2026-portal.pdf) permitiu conferir um recorte com cinco blocos da GEDIV e sete processos. A nova separação reconheceu esses cinco blocos no texto disponibilizado pelo índice. Isso não envolveu baixar ou processar o PDF original e não comprova a cobertura da edição ou o OCR. Os 22 testes locais incluem casos sintéticos de blocos repetidos, de resenha anterior ao cabeçalho e de não atribuição de texto de outra área.

Um segundo recorte textual indexado, desta vez da [edição oficial de 10/10/2026](https://auniao.pb.gov.br/servicos/doe/2026/outubro/diario-oficial-10-10-2026-portal.pdf), permitiu comparar a resenha 541/2026 da página indicada como 3 com o arquivo histórico. Os 13 processos apareceram em ambos; processo, nome, matrícula, eixo, modalidade e resultado coincidiram nos 13. O texto da resenha indica o grupo GAJ-1700, não preenchido nos registros antigos. Em cópia local separada, foi acrescentada uma nota de conferência preliminar aos 13 registros, sem alterar grupo, status ou indicadores. O painel exibe a nota e a inclui na exportação de pendências. A comparação usou texto indexado, não o PDF original; não comprova cobertura integral, OCR ou validação final. O conjunto de testes locais passou a ter 23 testes.

Outros recortes indexados permitiram confrontar os mesmos campos nas resenhas 457/2026 (21 candidatos), 458/2026 (9 de 20), 478/2026 (20) e 504/2026 (20): 70 coincidências adicionais. Os trechos não identificam expressamente a GEDIV. A resenha 456/2026 aparece mais de uma vez no mesmo recorte e foi recusada por ambiguidade. As notas foram acrescentadas somente em nova cópia privada, preservando todos os estados de revisão. `src/comparar_indice.py` registra URL, página indicada e hash do recorte, e interrompe a comparação em limites conservadores, inclusive `PUBLIQUE-SE`. A ordem de colunas do texto indexado ainda pode ser enganosa; a comparação não confirma integridade do PDF nem cobertura completa. São 25 testes locais, incluindo preservação do estado e recusa de ambiguidade.

## Referência de Kaio

Foi baixada e conferida a árvore pública de `kaiooeduardoo/cursoesafi` na revisão `09d7ec5a7d1a1961dfd46b155117575345ba21a7`, incluindo critérios, instruções, modelo de seis abas, interface e testes. O projeto visualiza planilhas importadas localmente; não coleta nem lê PDFs automaticamente. São relevantes a identificação de candidatos seguida de conferência direcionada, o controle de páginas e lacunas, os dados e alterações separados, a fonte por registro e os cuidados com exportação. Na cópia local, passaram as verificações de pacote, segurança e gráficos. Seu código próprio não apresenta licença geral de reutilização; este piloto adota conceitos e implementação própria, sem alterar o repositório de referência.

## Catálogo anterior

A versão histórica examinada tem 333 itens: 310 publicações e 23 ocorrências marcadas como alteração. Entre os 330 itens marcados como validados na origem, 204 têm a menção à GEDIV registrada como `nao_expresso`. Isso não demonstra que sejam de outra gerência; exige conferir o contexto institucional. O importador `src/importar_historico.py` preserva os estados anteriores e mantém publicações e eventos em revisão, sem somá-los automaticamente aos indicadores. Em cópia privada local, 310 registros e 23 eventos foram adaptados; nenhum foi promovido automaticamente. O catálogo antigo e o banco existente não foram alterados.

A prévia exibiu 309 registros pendentes, um rejeitado e 23 eventos sem vínculo; busca na lista e navegação foram exercitadas. O menu de exportação gerou confirmação de preparação, mas o navegador de teste não disponibilizou o arquivo baixado para inspeção. Em teste independente, o gerador XLSX foi aberto por outra biblioteca e um valor com aparência de fórmula permaneceu texto. A exportação com dados reais ainda exige homologação na máquina de uso da GEDIV.

Em 31/10, foi publicada separadamente a cópia privada de conferência. A configuração consultada lista apenas a conta proprietária, sem grupos ou convidados externos. Na prévia, as sete visões, menu, alternância da tabela, cobertura, lista e pesquisa de pendências foram acionados; os botões de exportação foram acionados, mas o arquivo baixado e o diálogo de impressão não puderam ser confirmados no navegador remoto. Um link de edição oficial abriu em nova aba, mas a rede desse navegador bloqueou o acesso ao endereço. Não se conclui, por isso, indisponibilidade do Diário para outros usuários.

## Limites e riscos

- O acesso direto ao portal oficial foi bloqueado no ambiente de desenvolvimento. Isso não prova indisponibilidade para outros ambientes.
- A separação de colunas e continuações, OCR em português, sete serviços e grupos ainda exigem comparação com documentos reais; um cabeçalho ausente em uma continuação pode ocultar registros.
- Quando o OCR não identifica processos dentro do bloco, o piloto deixa pendência em vez de associar à resenha linhas obtidas da página inteira. A recuperação por região delimitada ainda precisa ser implementada.
- O versionamento implementado preserva metadados e registros anteriores, mas não substitui arquivo documental imutável nem revisão de vínculos original/modificador.
- O histórico de revisão em JSON não é trilha imutável nem uma solução de identidade/autorização no servidor.
- Não há nesta branch evidência de carga histórica completa, automação diária em operação ou API autenticada. A URL privada publicada é uma cópia estática do estado parcial, não um painel conectado ao coletor.
- Os custos e franquias dos serviços e as condições da licença de PyMuPDF precisam ser conferidos antes da operação continuada.
- A amostra de 13 processos da resenha 541/2026 é anterior e permanece pendente; não foi reconciliada com outros conjuntos de dados.
