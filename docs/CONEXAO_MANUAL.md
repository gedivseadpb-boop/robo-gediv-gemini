# START manual — extração e conexão privada GEDIV

Verificação: 31/10/2026, 20h34 de João Pessoa. Este registro distingue entrega real, extração parcial e testes isolados.

## Resultado comprovado

O serviço do [painel privado](https://gediv-conferencia-privada-20261031.ylenaluna.chatgpt.site) confirmou três lotes reais, com 18 registros. O estado consultado antes tinha 310 registros e zero lotes; depois passou a 328 registros, 327 pendentes e um rejeitado. Nenhum registro foi promovido a conferido. Os 23 eventos anteriores não foram alterados por esses lotes, que não contêm eventos.

| Publicação oficial | Resenha | Registros recebidos | Recorte utilizado |
|---|---|---:|---|
| [17/01/2026](https://auniao.pb.gov.br/servicos/doe/2026/janeiro/diario-oficial-17-01-2026-portal.pdf) | 032/2026 | 1 | Página física 8, linhas indexadas 972–979 |
| [11/03/2026](https://auniao.pb.gov.br/servicos/doe/2026/marco/diario-oficial-11-03-2026-portal.pdf) | 117/2026 | 2 | Página física 8, linhas indexadas 944–952 |
| [10/06/2026](https://auniao.pb.gov.br/servicos/doe/2026/junho/diario-oficial-10-06-2026-portal.pdf) | 276/2026 | 15 | Página física 8, linhas indexadas 871–929 |

São 17 candidatos de Progressão Horizontal, grupo GAJ, e um de desaverbação de tempo de serviço. Os trechos foram recuperados novamente de URLs oficiais e confrontados com os campos extraídos nesta verificação. Isso não comprova leitura integral, precisão global nem cobertura de janeiro a outubro.

## Recibos do serviço real

| Lote | Identificador SHA-256 do recibo | Recebimento UTC |
|---|---|---|
| Janeiro, 1 registro | `8e7530081647e701624f4ea586448708bb80137e11dc942cf4ab0cecf11f7728` | 2026-10-31T23:34:10.784Z |
| Março, 2 registros | `a1fd41508aeca13feb5a4b17f9bf78c75ce3a388ac4f5d301f01903f7b085d53` | 2026-10-31T23:34:15.612Z |
| Junho, 15 registros | `53bcac04092f725bb4b28c02e252eb061b7bb3bf91dad8a1d84b5c9951db9a8e` | 2026-10-31T23:34:21.379Z |

O reenvio exato de junho devolveu `ja_recebido`, com o mesmo identificador e horário. A consulta subsequente manteve três lotes e 328 registros, com zero sobreposições com o histórico anterior. Esse é um teste real de persistência e reenvio; os testes de concorrência e recuperação de armazenamento continuam sendo isolados.

## Fluxo de inicialização

1. Consultar `gediv_status` pelo plugin do painel e verificar a conta/destino. A política atual permite somente a proprietária. Conferir novamente a privacidade do repositório antes de usar dados individuais.
2. Localizar a edição em URL oficial observada. Registrar data da publicação, total de páginas, páginas efetivamente lidas e método. Texto indexado, PDF nativo e OCR têm evidências distintas.
3. Preparar o pacote privado para `src/extrair_texto.py`: `url`, `data`, `metodo`, `referencia`, `paginas_totais` e `paginas`, cada uma com `pagina` e `texto`. `pagina_visual_conferida` só deve ser verdadeira quando houver conferência visual efetiva. Não atribuir SHA de PDF a texto indexado.
4. Executar o extrator com `--entrada`, `--saida` para um diretório novo e `--natureza real`. Usar a janela inclusiva autorizada. Preservar o pacote e o lote fora do código-fonte versionado.
5. Conferir contagem, identidade, resultado, vínculo institucional, limitações e SHA do texto. A identificação automática mantém candidatos pendentes e cobertura parcial.
6. Enviar o conteúdo integral de `lote.json` em `gediv_receber_lote`. Conservar o recibo. A resposta deve ser `recebido` ou `ja_recebido`; qualquer erro deixa a entrega não confirmada.
7. Consultar `gediv_status` em nova chamada e reconciliar os lotes e a quantidade de registros. A contagem do lote pode diferir do incremento se já houver sobreposição documental.
8. Abrir o painel com a conta autorizada e usar **Atualizar dados**. Os candidatos devem aparecer na fila de conferência, fora dos indicadores. Esta etapa visual ainda exige verificação: o navegador disponível nesta execução recebeu bloqueio de rede.
9. Encaminhar a conferência dos PDFs e os vínculos de alterações à revisão humana. A ponte de importação não permite ao emissor homologar decisões. Não ativar agendamento antes da homologação.

## Erros e reprocessamento

- Falha de acesso ao Diário: registrar edição pendente; não registrar ausência de publicações nem cobertura completa.
- Texto ilegível, misturado entre colunas ou com continuação não resolvida: preservar a lacuna e não atribuir linhas a uma resenha sem evidência.
- Falha de envio ou recibo perdido: reenviar o mesmo lote. O identificador estável impede duplicação do mesmo conteúdo.
- Correção do texto: gerar novo lote com nova evidência; conferir conflitos. A deduplicação exata não substitui a reconciliação humana de versões e eventos.
- Fonte, data, páginas ou situação inválidas: corrigir a origem do erro; não retirar as validações do receptor.

## Evidências e limites dos testes

- Três extrações reais reproduzidas localmente com igualdade dos registros, eventos e metadados de origem.
- Três entregas ao serviço publicado e uma reentrega idempotente, todas com recibos reais.
- Consulta autenticada após a entrega confirmou os totais e o agendamento desativado.
- As 58 verificações Python anteriores e os 14 testes da ponte com armazenamento simulado não representam testes de precisão documental ou de identidade externa.
- A política de acesso foi lida no serviço de hospedagem; a conta proprietária é a única autorizada. Não houve ensaio com outra identidade.
- O navegador desta execução retornou **Forbidden. Calls to this URL are not allowed.** A API privada respondeu. Não foi possível homologar visualmente a interface nem os arquivos de exportação.
- A obtenção direta dos PDFs continua sem sucesso comprovado neste ambiente. O funcionamento assistido por texto indexado não é um robô autônomo diário.
- A cobertura integral de 01/01/2026 a 31/10/2026, os suplementos, OCR e validação humana continuam pendentes.
