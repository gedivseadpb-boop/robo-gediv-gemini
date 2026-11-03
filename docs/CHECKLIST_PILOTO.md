# Checklist verificável — Robô GEDIV

Atualização: 31/10/2026. A coluna de estado descreve o escopo desta branch, não uma homologação institucional. Responsável pela conferência humana e aceitação: GEDIV/área autorizada. Responsável pela implementação: desenvolvimento do projeto.

Este quadro resume o andamento dos itens críticos; o checklist integral anterior está preservado em `REFERENCIA_CHECKLIST_2026-10-29.md` e a especificação em `REFERENCIA_ESPECIFICACAO_V3.md`. Os itens ausentes do quadro resumido não foram descartados.

| ID | Requisito e fonte | Prioridade | Estado | Evidência / método de validação | Dependência ou impedimento |
|---|---|---|---|---|---|
| C01 | Privacidade do repositório — instruções da gerência | Crítica | Aprovado na consulta de 31/10 | Metadados do repositório consultados antes do trabalho | Verificar novamente antes de qualquer operação com dados individuais |
| C02 | Manter separados código de teste e versão principal — checklist | Alta | Em desenvolvimento | Branch `codex/piloto-gediv-20261031` | Revisão antes de qualquer integração à `main` |
| C03 | Documento parcial deve voltar à fila — checklist | Crítica | Em teste | Teste isolado de reprocessamento com hash idêntico | Conferência em execução real |
| C04 | Preservar leitura anterior diante de falha ou substituição — checklist/V3 | Crítica | Em teste | Testes de falha, preservação e snapshot de versão anterior | Revisão do modelo completo e armazenamento durável dos PDFs |
| C05 | Validar domínio e redirecionamentos — checklist | Alta | Em teste | Testes de domínio parecido, credenciais, porta e redirecionamento externo | Teste com portal oficial e redirecionamentos reais |
| C06 | Separar candidato de decisão conferida — V3 | Crítica | Em teste | Conversor e testes do painel; amostra anterior de 13 candidatos mostrada como pendente | Conferência humana de cada decisão |
| C07 | Painel gerencial gerado junto da coleta — V3/UI | Alta | Entrega manual real comprovada; homologação pendente | [Painel privado](https://gediv-conferencia-privada-20261031.ylenaluna.chatgpt.site) recebeu 18 registros em três lotes; consulta real confirmou 328 registros; reenvio não duplicou | Interface visual, filtros e arquivos exportados ainda exigem homologação; coleta diária desativada |
| C08 | Registrar revisão responsável, motivo e fonte — V3 | Alta | Em teste | Utilitário local `src/revisar.py` e testes isolados | Interface de revisão, identidade autenticada, trilha persistente e homologação |
| C09 | Ler uma edição oficial completa — piloto do checklist | Crítica | Bloqueado no acesso | [Primeira execução](https://github.com/gedivseadpb-boop/robo-gediv-pb/actions/runs/41233068223) e [segunda execução](https://github.com/gedivseadpb-boop/robo-gediv-pb/actions/runs/41233491203): testes passaram; conexões às fontes selecionadas expiraram | Testar com PDF oficial obtido em ambiente autorizado, sem presumir indisponibilidade geral do portal |
| C10 | Confirmar OCR em português e colunas — checklist | Crítica | Em desenvolvimento | OCR marca página para conferência; evita atribuir ao bloco texto da página inteira | Comparar com PDF oficial e amostra anotada; instalar idioma português; revisão humana |
| C11 | Vínculo institucional e decisões individuais — V3 | Crítica | Parcial | 18 candidatos extraídos de três recortes oficiais com identificação expressa da GEDIV; 58 testes Python anteriores incluem correções de continuação e duplicidade | Conferência integral de PDFs, variantes, colunas e revisão humana |
| C12 | Retificações e REFEITOS por ato original — V3 | Crítica | Não iniciado | Exigir vínculo revisado e versão comprovada, inclusive caso 473/2026 | Modelo e interface de vinculação ainda não concluídos |
| C13 | Histórico desde 01/01/2026 — checklist | Crítica | Iniciado, cobertura parcial | Três lotes de janeiro, março e junho entregues; histórico anterior de setembro/outubro preservado | Inventariar e ler todas as edições e suplementos; reprocessar lacunas; não declarar cobertura integral |
| C14 | Atualização diária e manual realmente funcionando | Crítica | Entrega manual comprovada; diária pendente | Recibos reais de três lotes; reenvio idempotente; consulta independente confirmou persistência | Obtenção de texto indexado ainda assistida; START autônomo e agendamento somente após homologação |
| C15 | Acesso individualizado e exportação autorizados no servidor | Crítica | Em desenvolvimento | Política atual restrita à proprietária; plugin privado recebeu lotes e consultou estado no serviço real | Testar identidade negada, equipe e exportações; navegador desta execução bloqueado pela rede |
| C16 | Aceitação e uso institucional — V3 | Crítica | Não iniciado | GEDIV compara resultados, PDFs, indicadores e permissões | Evidências dos itens anteriores e homologação da área responsável |
| C17 | Reaproveitar dados históricos sem validar automaticamente o vínculo GEDIV | Alta | Preservação observada na entrega real; revisão pendente | Estado anterior de 310 registros preservado ao receber 18 novos; continuam zero conferidos; novos lotes não contêm eventos | Conferir os PDFs e reconciliar publicações e os 23 modificadores anteriores antes de contar indicadores |
| C18 | Ler cabeçalhos repetidos da GEDIV na mesma coluna sem misturar outras unidades | Crítica | Em teste | PDF sintético com múltiplos blocos; recorte textual indexado de 11/03/2026 retornou cinco blocos e sete processos | Comparar extração diretamente do PDF oficial completo e verificar continuações |
| C19 | Comparar amostra histórica com texto de fonte oficial | Alta | Parcial | Resenha 541/2026: 13 coincidências; nas resenhas 457, 458, 478 e 504/2026: outras 70 coincidências parciais, sem GEDIV expressa nos recortes utilizados | Conferir os PDFs e o vínculo institucional; permanecem pendentes e não integram indicadores |

## Regra de aceite

Um teste sintético que passa demonstra apenas o comportamento exercitado. Não representa precisão de OCR, cobertura completa, publicação real identificada, segurança de um serviço hospedado ou conclusão do robô. Edições, decisões e eventos pendentes não são zero confirmado.

O [registro de conexão manual](CONEXAO_MANUAL.md) conserva os recibos e os limites observados em 31/10/2026. A contagem atual de 328 é de registros no serviço, não de decisões homologadas nem de cobertura integral.
