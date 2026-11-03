> **Referência histórica.** Este documento preserva o checklist de 29/10/2026. A consulta de 31/10 confirmou o repositório privado; consulte CHECKLIST_PILOTO.md e a branch atual para o estado mais recente. Decisões posteriores da usuária prevalecem.

# Checklist de execução — Robô GEDIV e Painel DOE

**Atualização:** 29/10/2026  
**Objetivo:** implantar um robô que identifique publicações da GEDIV no Diário Oficial da Paraíba, organize dados verificáveis e alimente o painel gerencial aprovado.  
**Situação:** desenvolvimento iniciado em cópia local; coleta histórica e atualização automática ainda não validadas.

**Como usar:** marque `[x]` apenas após verificar o resultado e registrar a evidência. `Pendente` não é sinônimo de falha; indica uma etapa ainda não concluída. Não inserir dados fictícios no painel nem apresentá-los como publicações reais.

## Regras já definidas

- Dois eixos: **Progressão Funcional** e **Tempo de Serviço/Contribuição**. Horizontal e Vertical são modalidades de Progressão; grupos ocupacionais não são eixos.
- Primeira carga histórica solicitada: **01/01/2026 até a data de execução**. A especificação V3 menciona 2025; ampliar depois, sem impedir a consulta de um ato anterior quando for necessário conferir uma alteração de 2026.
- Considerar como GEDIV somente atos com vínculo institucional comprovado. Menção isolada a DEREH, SEAD ou ao tema não basta.
- Dados individualizados, buscas e exportações devem ficar disponíveis apenas a usuários autorizados; o código público não deve conter dados individuais nem credenciais.
- Preservar o painel aprovado: filtros recolhíveis à esquerda, gráficos e indicadores no centro e resenhas/processos à direita, com download da visão escolhida.
- A ausência de dados só pode ser apresentada como ausência de publicação quando a cobertura do recorte for suficiente; nos demais casos, informar **cobertura pendente** ou **base não carregada**.
- Antes de alterar o GitHub ou um site existente, apresentar a alteração concreta e solicitar a autorização que Ylena pediu anteriormente.

## Ponto de partida confirmado

- [x] Examinar a especificação funcional V3, o código atual do robô e o painel sem dados no GitHub.
- [x] Confirmar que o repositório `robo-gediv-pb` está público nesta verificação e que o fluxo atual impede a coleta nesse estado.
- [x] Identificar que a cópia pública do painel não contém registros individuais e não está conectada à coleta automática.
- [x] Preparar, em cópia local, uma primeira correção para manter edições com pendências na fila e preservar dados anteriores quando uma tentativa falha.
- [x] Executar 8 testes locais das regras existentes e da correção; a rotina de coleta de rede foi simulada nos testes específicos de reprocessamento.
- [x] Verificar um PDF real local: a leitura ficou pendente, com zero registros extraídos, porque `pytesseract` não estava instalado neste ambiente. Isso **não demonstra falha no GitHub** e não valida o OCR.
- [x] Testar o OCR disponível em uma tabela da resenha real 236/2026: o recorte ampliado identificou os 4 números de processo e os 4 coincidiram com o documento. O idioma disponível era inglês e a página inteira não identificou esses números; nomes e outros campos não foram validados. É um experimento local, não uma coleta do DOE.
- [x] Testar a função de extração existente com o trecho textual previamente localizado na página física 3 do DOE de 10/10/2026: foram identificadas 13 linhas candidatas da resenha 541/2026, todas marcadas como pendentes. Isso não testa a descoberta automática nem a extração integral do PDF.
- [x] Consultar, sem executar nova coleta, o status da ferramenta anterior do Observatório. Ela relata 41 edições no recorte 01/09 a 25/10/2026, nenhuma integralmente processada e 41 pendentes na atualização de 27/10. Seus totais de ocorrências exigem auditoria e não comprovam alimentação do painel de revisão.
- [x] Verificar que o painel de revisão aprovado tem acesso restrito configurado e nenhum agendamento vinculado; a versão examinada é estática. Um site anterior com nome semelhante está público; não foi verificado nesta análise quais dados individuais ele expõe.
- [x] Inventariar **213 arquivos** identificados nas listagens consultadas de janeiro a outubro de 2026. Entre eles estão as edições de **28 e 29/10**, localizadas na segunda página do acervo; os dois PDFs ainda não foram lidos. Inventariar não significa concluir a leitura ou provar cobertura integral.
- [x] Registrar o resultado da tentativa histórica: **154 PDFs disponibilizados para leitura**, **96 buscas textuais parciais**, **59 arquivos não obtidos** e **58 falhas de busca após abertura**. Os totais são da tentativa documentada e não provam inexistência de publicações nas edições pendentes.
- [x] Preparar, para conferência, **118 apontamentos candidatos**, uma amostra de **13 processos** da resenha 541/2026 e **7 referências separadas de fonte não oficial**, sem contá-los como decisões validadas. Uma das sete referências já corresponde a um apontamento do lote principal; não somá-la novamente. O vínculo, a classificação e as fontes devem ser confirmados antes da carga.
- [ ] Abrir e conferir o conteúdo dos DOEs de 28 e 29/10 e das demais edições pendentes; testar OCR, colunas e eventuais suplementos antes de afirmar que o período foi coberto.
- [ ] Conferir no PDF oficial cada uma das referências encontradas em espelho de terceiros. A página indicada no espelho não comprova, por si só, a página física do PDF oficial.
- [ ] Revisar a correção local e autorizar, se desejado, sua inclusão em local específico do GitHub. A cópia preparada ainda não foi enviada.

## 0. Arquitetura hierárquica da captura do DOE

### 0.1. Decisão de arquitetura — candidata principal

**Caminho prioritário para testar sem depender de assinatura paga:** código e execução do robô em ambiente **privado**, com GitHub Actions nas franquias gratuitas; Python e Tesseract em lotes; e, como hipótese de hospedagem, Cloudflare Workers, D1 e Access nas respectivas faixas gratuitas. A interface deve preservar o layout e as regras do painel aprovado. Isso depende de confirmar cadastro, acesso, consumo e integração; não é uma implantação pronta nem garantia de custo zero. O código público já existente pode continuar como referência, mas o fluxo atual só executa a coleta quando o repositório é privado. O envio de dados individuais ao repositório depende de confirmar sua privacidade e da autorização já solicitada pela usuária.

Fluxo de informações:

`Acervo oficial → inventário de edições → leitura do PDF/OCR → candidatos GEDIV → conferência → base privada → API autorizada → painel e exportações`

O processamento pesado dos PDFs deve ficar fora de um Worker gratuito com tempo de CPU limitado. O painel e a API podem ser leves e separados do processo de leitura. Dados candidatos não entram nos indicadores oficiais até a validação.

**Situação:** arquitetura recomendada, ainda não instalada nem comprovada de ponta a ponta. A solução deve funcionar sem API de IA paga; o uso de IA é opcional e sujeito às regras institucionais.

### 0.2. Comparação de soluções

| Alternativa | Como funcionaria | Automação e compartilhamento | Custo e decisão |
|---|---|---|---|
| **A. Manual, como a ideia do Kaio** | Pessoa analisa o documento e importa planilha validada no navegador. | Não coleta nem atualiza automaticamente; arquivo precisa ser importado. | Simples e compatível com software gratuito. Usar como contingência, não como solução final pretendida. Não copiar código sem licença ou permissão. |
| **B. GitHub privado + painel privado já existente** | Actions executa coletor/OCR; uma base e API privadas alimentam o painel após adequação. | Pode oferecer atualização diária e manual e manter o layout já aprovado. | GitHub Free tem franquias. A hospedagem Sites está atualmente incluída no plano Plus/Pro existente, mas esses planos são pagos; portanto é custo adicional potencialmente zero, não uma solução independente de assinatura paga. Pode servir como etapa temporária se a usuária concordar. Integração, uso e acesso da equipe ainda precisam de teste. |
| **C. GitHub privado + Cloudflare Workers/D1/Access** | Actions faz OCR; Worker protegido consulta uma base privada e entrega o painel com o layout aprovado. | Pode oferecer atualização e acesso por pessoa, quando configurados e testados. | Primeira hipótese para solução independente de assinatura paga. Serviços têm faixas gratuitas e limites. O cadastro do Zero Trust pode exigir dados de pagamento; o consumo e as condições reais precisam ser verificados. Não é uma gratuidade garantida. |
| **D. Infraestrutura institucional existente** | Computador ou servidor institucional executa o robô e hospeda base/painel em rede protegida. | Pode automatizar se a máquina e rede permanecerem disponíveis. | Softwares podem ser gratuitos, mas infraestrutura, energia, suporte e autorização institucional não são presumidos gratuitos ou disponíveis. |
| **E. Ferramenta antiga do Observatório** | Reaproveitar o coletor e a base já existentes após auditoria. | Há status de leitura, mas a integração com o painel aprovado e a atualização diária não foram comprovadas. | Pode reduzir trabalho; validar acesso, origem, qualidade e custo antes de reutilizar. O site antigo está público e não deve receber ou expor novos dados individualizados sem verificação e autorização. |

- [x] Comparar os modelos acima e escolher **C como primeira hipótese a validar**, por não depender da assinatura paga do ChatGPT e permitir reproduzir o layout aprovado, sujeito às condições das franquias.
- [ ] Verificar cadastro, base persistente, acesso autorizado, integração de serviço, cota e compartilhamento de C. Avaliar B como etapa temporária ou D como alternativa, conforme disponibilidade e preferência da usuária.
- [ ] Registrar a escolha final apenas depois de testar o fluxo e confirmar que os custos previstos atendem à exigência da usuária.

### 0.3. Franquias e limites — verificar antes da implantação

- GitHub Free para repositórios privados: a documentação consultada informa **US$ 12 de uso de computação incluído por mês** e **500 MB de armazenamento de artefatos**. À tarifa documentada de US$ 0,006 por minuto em runner Linux padrão, isso corresponde a até cerca de 2.000 minutos se não houver outro uso da mesma franquia. Medir o tempo real; não tratar esse número como garantia de gratuidade.
- Configurar e testar controles de orçamento, limites e alertas quando autorizados. Um alerta sozinho pode não impedir cobrança; a documentação do GitHub alerta que o orçamento pode ser excedido no primeiro ciclo em determinadas condições.
- Cloudflare D1 Free: documentação consultada indica **5 milhões de linhas lidas/dia, 100 mil escritas/dia e 5 GB totais**. Ao atingir os limites, consultas ou gravações podem falhar. Conferir as condições atuais antes de adotar.
- Cloudflare Workers Free: **10 ms de CPU por requisição ou gatilho**, segundo a documentação consultada; isso não é adequado para pressupor OCR pesado de PDFs no próprio Worker. Usar um executor separado e medir.
- Cloudflare R2 possui franquia gratuita documentada para armazenamento e operações; ultrapassagens, cadastro e eventual necessidade de meio de pagamento exigem verificação.
- O Supabase Free é alternativa para banco/API, com **500 MB por projeto** nas condições consultadas e possibilidade de pausa após baixa atividade por sete dias. Verificar autorização por linha e regras de acesso antes de qualquer uso.
- ChatGPT Sites: a hospedagem é atualmente incluída no Plus/Pro, com limites de uso e armazenamento; não está disponível nos planos Free ou Go segundo a documentação consultada. Não presumir que as quotas do Cloudflare sejam idênticas às do Sites.
- A coleta não deve depender de serviço pago de OCR ou chamada a modelo de IA. Confirmar licenças das bibliotecas: o código atual usa PyMuPDF, distribuído sob AGPL ou licença comercial; avaliar aderência ou alternativas como pdfplumber, conforme necessidades e revisão técnica.
- [ ] Medir tempo e volume reais dos primeiros documentos, estimar consumo mensal e da carga histórica e registrar o resultado.
- [ ] Confirmar se contas, métodos de pagamento, plano, permissões e armazenamento exigidos estão disponíveis; não ativar cobrança nem criar assinaturas sem autorização.

### 0.4. Camadas de captura — implementação em ordem

#### Nível 1 — Inventário da fonte

- [ ] Consultar o acervo oficial de A União por mês e percorrer todas as páginas de listagem. Identificar edição ordinária, suplemento e versão substitutiva pelo que a fonte efetivamente apresenta.
- [ ] Registrar data de publicação, número quando identificável, tipo, URL original, data/hora da consulta, tamanho e hash SHA-256. Não fabricar endereços.
- [ ] Conferir o domínio por análise da URL e validar também redirecionamentos; o uso atual de comparação por prefixo precisa de revisão.
- [ ] Validar resposta, limite de tamanho e assinatura de PDF; guardar erros, tempo de espera e retomada com intervalo entre tentativas.
- [ ] Tratar cada suplemento como documento próprio, sem confundi-lo com a edição normal do mesmo dia.

#### Nível 2 — Leitura e reconhecimento de regiões

- [ ] Inspecionar primeiro a qualidade do texto nativo por região, inclusive páginas em que parte do texto está legível e parte está corrompida.
- [ ] Usar OCR em português para as regiões necessárias; registrar versão, idioma, método e página. A ausência do modelo em português deve criar pendência visível, sem fingir sucesso.
- [ ] Fazer duas passagens: localizar regiões candidatas e depois ampliar tabelas, linhas ou cabeçalhos relevantes. A região de uma linha deve conservar referência à mesma resenha e ao contexto institucional.
- [ ] Reconstruir ordem de leitura entre colunas, páginas e atos sem fundir dados de outra gerência; quando houver dúvida, preservar o trecho e pedir revisão.
- [ ] Registrar **página física do PDF** e **página impressa**, com posição aproximada do conteúdo. O link do visualizador deve usar a página física.
- [ ] Testar outras edições e formatos além da resenha 236/2026; o desempenho de um recorte não comprova a leitura de todas as edições.

#### Nível 3 — Vínculo GEDIV e extração

- [ ] Identificar o início e fim do bloco institucional por contexto, não apenas por palavra-chave na mesma coluna.
- [ ] Separar identificações comprovadas de indícios sem vínculo; estes últimos não entram nos cartões.
- [ ] Extrair cada decisão e sua evidência literal: data de publicação, resenha, processo, resultado, grupo/serviço e, apenas em ambiente autorizado, dados individuais expressamente publicados.
- [ ] Normalizar busca e classificação com acentos e variantes; preservar sempre a grafia original. Não inferir dados ausentes.
- [ ] Aplicar o dicionário dos dois eixos, modalidades, condições, grupos e sete serviços; denominações novas entram como candidatas.

#### Nível 4 — Duplicidades, divergências e alterações

- [ ] Comparar identidade documental, data, tipo, número/ano, processo, campos e texto; um identificador isolado não autoriza descartar um registro.
- [ ] Usar como caso real de homologação a resenha **473/2026**, presente nos DOEs de 02/10 e 10/10/2026 com informações divergentes. Confrontar as duas fontes e pesquisar possível alteração; não presumir qual versão prevalece ou que uma seja duplicata simples.
- [ ] Detectar retificações, republicações, correções e atos sem efeito, vinculando-os ao ato original somente com evidência suficiente.
- [ ] Manter histórico versionado, candidatos de vínculo e evidências; uma tentativa parcial não deve apagar a versão anterior.
- [ ] Rever a atualização atual do estado: ela substitui registros da mesma URL após um processamento; a correção local preserva dados diante de falhas, mas não implementa versionamento completo.

#### Nível 5 — Armazenamento e validação

- [ ] Separar edição, documento/página, ato, resenha, processo, decisão, evento, vínculo, revisão, catálogo, cobertura e execução.
- [ ] Preservar arquivo ou cópia documental de forma controlada e rastreável conforme disponibilidade, política de retenção e custos; não depender apenas de link que pode mudar.
- [ ] Manter registros identificados, extraídos, pendentes, validados, rejeitados e revisados em estados distintos, com histórico de quem revisou e quando.
- [ ] Impedir que métricas recebam dados ainda pendentes de validação. O JSON agregado do código atual conta a quantidade de registros sem, por si só, comprovar revisão.
- [ ] Preparar restauração de backup, expiração controlada e proteção de dados nos logs e artefatos; não versionar dados pessoais em repositório público.

#### Nível 6 — API, painel e permissões

- [ ] Implementar uma interface de dados autenticada entre base e painel, com permissão por usuário, operação e exportação; testar o lado do servidor, não apenas ocultar elementos visuais.
- [ ] Definir uma rotina segura para o coletor gravar na base sem colocar credenciais no código ou no navegador. Verificar as opções compatíveis com o ambiente privado antes de emitir qualquer credencial.
- [ ] Levar ao painel a última atualização, período realmente coberto, edições não lidas, páginas com OCR pendente, vínculos não resolvidos e dados validados.
- [ ] Garantir que filtros, gráficos, cartões e tabela compartilhem regras de contagem e acesso. Para Refeitos e Sem efeito, usar a data do evento; para decisões originais, usar a data da publicação original.
- [ ] Corrigir os tipos de dados do Excel e gerar exportações completas da visão selecionada, sempre respeitando o acesso do usuário.

#### Nível 7 — Rotina diária, histórica e contingência

- [ ] Ativar a execução manual apenas depois que o fluxo de teste estiver pronto e aprovado; usar a mesma lógica e os mesmos controles da rotina diária.
- [ ] Implantar agendamento diário no fuso de João Pessoa, registrar início, término e resultado e verificar que a execução realmente ocorreu. Agendamentos podem atrasar.
- [ ] Tratar histórico de 2026 em lotes retomáveis, sem deixar falhas antigas bloquearem edições novas e vice-versa; identificar edições ainda ausentes.
- [ ] Quando o portal estiver fora do ar ou a franquia se esgotar, preservar o último estado confirmado, mostrar a falha e retomar depois.
- [ ] Manter alternativa manual de planilha padronizada, com importação local e conferência humana, para contingência; ela não substitui a atualização automática.

### 0.5. Portões de aceitação do piloto

- [ ] A fonte oficial responde no ambiente escolhido e é possível inventariar edição e suplemento reais.
- [ ] Ao menos uma edição real atravessa descoberta, leitura, vínculo GEDIV, registro, validação e visualização privada com evidência verificável.
- [ ] Uma edição com falha ou leitura parcial permanece pendente e volta para tentativa; dados anteriores não são apagados.
- [ ] Testes com documentos reais cobrem pelo menos uma ocorrência de Progressão e uma de Tempo de Serviço, além de um caso de alteração/vínculo.
- [ ] As duas publicações da resenha 473/2026 recebem análise explícita, sem decisão automática de equivalência.
- [ ] A pessoa sem permissão não consegue acessar registros individuais nem exportá-los por URL ou API.
- [ ] O relatório de consumo indica se o piloto e a rotina cabem na franquia; custos e exigências de cadastro são comunicados antes de ativar serviços.
- [ ] A GEDIV confere os resultados e o acesso; só então liberar histórico completo e agendamento como operação.

### 0.6. Fontes para as decisões técnicas

- [Acervo oficial de outubro de 2026, com edição e suplemento](https://auniao.pb.gov.br/servicos/doe/2026/outubro/).
- [DOE de 02/10/2026](https://auniao.pb.gov.br/servicos/doe/2026/outubro/diario-oficial-02-10-2026-portal.pdf) e [DOE de 10/10/2026](https://auniao.pb.gov.br/servicos/doe/2026/outubro/diario-oficial-10-10-2026-portal.pdf).
- [Franquias atuais do GitHub](https://docs.github.com/en/billing/reference/product-usage-included) e [cobrança do Actions](https://docs.github.com/en/billing/concepts/product-billing/github-actions).
- [Limites do Cloudflare D1](https://developers.cloudflare.com/d1/platform/pricing/) e [limites do Workers](https://developers.cloudflare.com/workers/platform/limits/).
- [Cloudflare Access para Workers](https://developers.cloudflare.com/workers/configuration/cloudflare-access/) e [criação de conta Zero Trust](https://developers.cloudflare.com/cloudflare-one/setup/).
- [Política de pausa do Supabase Free](https://supabase.com/docs/guides/platform/free-project-pausing).
- [Uso e limites do ChatGPT Sites](https://help.openai.com/pt-br/articles/20001339-creating-and-using-chatgpt-sites).
- [Licença do PyMuPDF](https://pymupdf.readthedocs.io/en/latest/about.html) e [licença do pdfplumber](https://github.com/jsvine/pdfplumber/blob/stable/LICENSE.txt).

### 0.7. Referência do Kaio — avaliação e decisões para o nosso painel

**Escopo examinado:** tela pública, arquivos do repositório, instruções e critérios de extração, JavaScript, segurança e testes incluídos no projeto. Os dados iniciais mostrados pelo próprio site são identificados como demonstração. A tela abriu no navegador, mas a conexão interrompeu a interação; por isso não foi possível clicar e confirmar todos os controles em um navegador real. Uma simulação local do código exercitou filtro, abas, exportação CSV, impressão, tema, seletor e rejeição de arquivos; essa simulação não substitui o teste completo de interface.

| Área | O que foi observado | Decisão para a GEDIV |
|---|---|---|
| Captação | O site recebe XLSX criado separadamente; não lê o PDF do DOE, não verifica a planilha e não sincroniza a fonte. O fluxo sugerido usa ChatGPT para produzir a planilha. | Construir o coletor e o OCR próprios; manter importação padronizada apenas como contingência conferida. |
| Organização da extração | Os critérios propõem uma passagem para localizar candidatas e outra para extrair e conferir; também distinguem cobertura, documentos e vínculos pendentes. | Adotar a organização em duas passagens, com evidência e revisão humana, sem depender de uma IA paga. |
| Filtros | Há órgão, tipo, município e busca. No código e na simulação, tipo e município filtram instrumentos, mas não restringem os aditivos; com o tipo “Termo de fomento”, a amostra ficou em um instrumento e sete aditivos. | Definir o alcance de cada filtro para cada entidade e tornar os totais coerentes ou rotular explicitamente a exceção. |
| Pesquisa | A busca converte maiúsculas/minúsculas, mas não remove acentos; na amostra, “saude” e “saúde” retornaram resultados diferentes. | Tornar a busca tolerante a acentos, preservando o texto original. |
| Gráficos | Rosca com quantidades e percentuais, legenda textual e barras por órgão; as fatias e legendas são apresentadas, mas não aplicam filtros. | Manter legenda acessível e acrescentar seleção por gráfico, combinação de filtros, indicação da seleção e ação para limpar. |
| Tabela e downloads | Abas de instrumentos e alterações; a tabela exibe até 500 linhas e informa essa limitação. O CSV exporta a aba e o filtro ativos; o PDF usa a impressão do navegador. | Exportar todos os registros autorizados do recorte, indicar filtro e cobertura, testar Excel tipado e PDF, além de paginação consistente. |
| Qualidade dos valores | A função de conversão do projeto transforma valores numéricos inválidos em zero. | Manter “não informado” e erro de leitura distintos de zero; validar dados antes de agregar. |
| Segurança no navegador | Processamento local do Excel; CSP restringe conexões de scripts; escape de texto, validações de tamanho/ZIP e neutralização de fórmulas no CSV. Os testes básicos de segurança e integridade passaram na cópia analisada. | Adaptar esses controles e testá-los para os nossos formatos; acrescentar autenticação e autorização de servidor para dados individualizados. |
| Fonte e acesso | Link aceita HTTPS e mostra o domínio informado pela planilha, mas não comprova fonte oficial. O site é público e não tem autenticação nem armazenamento remoto. | Usar endereço obtido do acervo oficial, validar domínio e redirecionamentos, e proteger base, API, painel e exportações. |
| Reutilização | O projeto informa que, salvo avisos de terceiros, a publicação não concede licença geral para copiar o código. | Reaproveitar ideias e especificações; só copiar código com licença aplicável ou permissão. |

- [x] Comparar os recursos e limites do projeto de referência com as necessidades do robô e do painel GEDIV.
- [ ] Homologar todos os controles do nosso painel em navegador real com usuários e permissões diferentes, inclusive fluxo de download e leitura de tela.
- [ ] Testar o fluxo de importação com arquivo real apropriado e autorizado, em ambiente privado, se a contingência por planilha for adotada.

Referências do projeto analisado: [visão geral](https://github.com/kaiooeduardoo/cursoesafi), [código do painel](https://github.com/kaiooeduardoo/cursoesafi/blob/main/assets/dashboard.js), [critérios de extração](https://github.com/kaiooeduardoo/cursoesafi/blob/main/CRITERIOS_EXTRACAO.md) e [política de segurança](https://github.com/kaiooeduardoo/cursoesafi/blob/main/SECURITY.md).

## 1. Preservação e ambiente

- [ ] Registrar a versão do código atual e do painel aprovado; preparar um ponto de restauração e testar como voltar a ele.
- [ ] Trabalhar em cópia ou ramificação separada e apresentar quais arquivos serão modificados antes de qualquer gravação no GitHub.
- [ ] Definir o destino privado e persistente dos dados individualizados. Possibilidades: ambiente/repositório privado aprovado ou código público separado de processamento e armazenamento privados; escolher a arquitetura conforme recursos disponíveis.
- [ ] Verificar o acesso e a política de armazenamento do destino escolhido antes de enviar dados pessoais.
- [ ] Testar primeiro a conexão com dados técnicos sem identificação individual.

**Etapa concluída quando:** houver um local de teste definido, acesso verificado e procedimento de retorno comprovado, sem modificar o painel aprovado.

## 2. Descoberta e controle de edições

- [ ] Localizar edições oficiais no acervo de A União, incluindo edições normais, suplementos e substituições disponíveis.
- [ ] Registrar data, número/tipo da edição, endereço exato encontrado, horário de consulta, páginas e hash do PDF.
- [ ] Distinguir falha de acesso, edição não localizada, arquivo ilegível e inexistência confirmada; não gerar zero automático para casos incertos.
- [ ] Evitar duplicação por URL, conteúdo e edição; identificar substituição do mesmo endereço por PDF diferente.
- [ ] Organizar a carga de 2026 em lotes retomáveis, com registro do que foi encontrado, processado e pendente.
- [ ] Dar tratamento justo à fila de novas edições e tentativas antigas, para evitar que uma falha recorrente bloqueie todo o histórico.
- [ ] Reprocessar com tentativas limitadas, intervalo e registro do erro; preservar o estado anterior durante falha e revisão.

**Etapa concluída quando:** uma amostra real de edições e suplementos tiver inventário rastreável, sem perda ou duplicação, e as falhas estiverem visíveis.

## 3. Leitura de PDF e OCR

- [ ] Preparar ambiente de teste com dependências do projeto e OCR em português; registrar versões utilizadas.
- [ ] Detectar quando o PDF já tem texto e quando é necessário OCR, sem considerar texto ilegível como leitura válida.
- [ ] Ler blocos e colunas na ordem correta e tratar continuações de resenhas entre colunas e páginas.
- [ ] Distinguir página impressa de página física do arquivo PDF.
- [ ] Separar falha de página, leitura parcial e extração sem pendências; mesmo uma leitura sem erro técnico requer conferência humana.
- [ ] Repetir o teste da resenha 236/2026 e comparar as linhas extraídas com o PDF real.
- [ ] Conferir amostras reais de texto selecionável, imagem/OCR, resenha longa e continuação em página ou coluna.

**Etapa concluída quando:** os documentos escolhidos forem comparados com o original e as dificuldades remanescentes estiverem registradas.

## 4. Identificação da GEDIV e classificação

- [ ] Identificar primeiro o cabeçalho e o alcance do bloco institucional; só depois classificar o assunto e os processos.
- [ ] Separar candidatos sem vínculo GEDIV comprovado para revisão, sem incluí-los nos indicadores.
- [ ] Extrair, quando comprovados: resenha, processo, resultado, modalidade, condição, grupo ou serviço e trecho de evidência.
- [ ] Tratar cada decisão individual conforme seu próprio contexto; não repetir resultado para outras linhas por suposição.
- [ ] Atualizar um dicionário versionado com nomes, códigos, sinônimos, expressão original, evidência e situação de validação.
- [ ] Conferir todos os grupos já levantados em publicações e conversas; documentar a evidência de cada grupo e modalidade e identificar outros ainda não catalogados.
- [ ] Manter PPGG e outras referências sem prova suficiente como candidatos; preservar variantes STF/SFT até esclarecer sua relação, sem criar duplicatas automaticamente.
- [ ] Manter os sete serviços definidos: Anotação; Desaverbação; Licença para Tratar de Interesses Particulares; Desistência dessa Licença; Licença Especial; Conversão de Licença Especial em Tempo de Serviço; e Conversão de Férias.
- [ ] Classificar novas denominações como candidatas até validação, sem criar automaticamente uma oitava categoria.

**Etapa concluída quando:** os grupos e serviços testados tiverem evidência rastreável, e as dúvidas permanecerem em fila separada.

## 5. Retificações, Refeitos e Tornados sem efeito

- [ ] Detectar retificações, correções, republicações e atos tornados sem efeito, preservando o texto e o PDF do evento.
- [ ] Relacionar o evento ao ato original apenas quando houver evidência suficiente; não fazer vínculo apenas por semelhança de nome ou processo.
- [ ] Manter alterações sem vínculo comprovado em fila própria, sem acrescentá-las indevidamente a Refeitos.
- [ ] Preservar o histórico e as versões anteriores, incluindo alterações que atinjam apenas parte de uma resenha.
- [ ] Contar **Refeitos** por ato original com alteração validada, pela data de publicação do evento; vários eventos no mesmo ato não criam vários atos refeitos.
- [ ] Contar **Tornados sem efeito** separadamente; um ato pode aparecer nos dois indicadores quando houver eventos comprovados para ambos.
- [ ] Mostrar também o total de eventos e de eventos pendentes de vínculo, sem somá-los como novos processos ou decisões.
- [ ] Verificar atos originais anteriores a 2026 quando necessários para vincular modificações publicadas no período da primeira carga.

**Etapa concluída quando:** exemplos reais de original e modificador forem conferidos e puderem ser abertos nas duas fontes.

## 6. Base e conexão com o painel

- [ ] Definir entidades e identificadores para edição, página, ato, resenha, processo, decisão, evento, vínculo, versão e pendência.
- [ ] Impedir fusão automática de processos ou pessoas com identificações ambíguas.
- [ ] Definir o contrato de dados entre o coletor e o painel, incluindo cobertura, versão do dicionário e última atualização.
- [ ] Implantar autenticação e autorização no lado do servidor para consultas individualizadas e exportações.
- [ ] Separar registros confirmados, candidatos e pendentes, sem contar pendências como decisões validadas.
- [ ] Garantir persistência e recuperação da base; arquivo temporário de execução não é solução permanente.
- [ ] Criar testes da conexão e do recebimento de novas publicações, sem substituir o painel atual durante a validação.

**Etapa concluída quando:** uma publicação real conferida percorrer coleta, armazenamento e painel privado com a mesma evidência e a mesma contagem.

## 7. Painel gerencial

- [ ] Preservar o layout aprovado e os dois eixos, com navegação para Horizontal, Vertical, grupos e os sete serviços.
- [ ] Manter os sete cartões principais: Processos, Resenhas, Decisões, Deferidos, Indeferidos, Refeitos e Tornados sem efeito, com unidade e regra de data claras.
- [ ] Mostrar cobertura, eventos e pendências como informações de apoio.
- [ ] Fazer fatias, legendas, barras e cartões aplicarem os filtros correspondentes a toda a visão, com seleção visível e opção de desfazer.
- [ ] Permitir comparação de mais de um grupo e de mais de um serviço; conservar filtros ativos visíveis com o menu recolhido.
- [ ] Fazer o botão Voltar restaurar o contexto e as datas anteriores; conferir o atalho Publicações do Dia.
- [ ] Manter a alternância por resenha e por processo, paginação coerente, detalhe selecionado e tabela ampliada.
- [ ] Oferecer busca de servidor, processo e resenha apenas conforme permissão, e pesquisar com ou sem acentos.
- [ ] Diferenciar visualmente nenhum registro encontrado, base não carregada, falha e cobertura pendente.
- [ ] Garantir acesso à fonte e à página correta, inclusive para eventos modificadores.
- [ ] Revisar responsividade, contraste, navegação por teclado e rótulos para leitores de tela.

**Etapa concluída quando:** cada filtro e gráfico produzir uma lista coerente com o universo selecionado e as permissões do usuário.

## 8. Downloads e segurança

- [ ] Exportar todos os dados autorizados da visão filtrada, e não somente a página visível da tabela.
- [ ] No Excel, gravar quantidades como números, datas como datas e identificadores como texto; incluir filtros, período, cobertura e fonte.
- [ ] Incluir, quando pertinentes, abas de atos, decisões, eventos, vínculos, pendências e metadados.
- [ ] Proteger CSV e planilhas contra interpretação indevida de texto como fórmula e testar com os programas usados pela GEDIV.
- [ ] Ajustar PDF e imagem para mostrarem a situação real da base e do ambiente; remover rótulos fixos indevidos, como “acesso privado” na cópia pública.
- [ ] Definir e testar política de conteúdo e endereços de conexão permitidos na hospedagem escolhida.
- [ ] Manter credenciais fora do código público; restringir e registrar acessos e exportações conforme política institucional.

**Etapa concluída quando:** os arquivos abertos pela gerência corresponderem à visão selecionada e respeitarem as mesmas permissões da tela.

## 9. Homologação e início da rotina

- [ ] Construir conjunto de referência com edições reais anotadas e conferidas por pessoas autorizadas da GEDIV.
- [ ] Comparar extração, grupos, serviços, resultados, alterações, contagens e fontes com os documentos originais.
- [ ] Medir precisão e cobertura com denominadores registrados; anotar falhas, correções e pendências sem prometer 100% sem prova.
- [ ] Testar falha e recuperação de rede, OCR, arquivo substituído, reprocessamento, deduplicação e restauração.
- [ ] Testar todos os botões, filtros, exportações e páginas no navegador de uso da gerência.
- [ ] Após validação do fluxo completo, executar a carga desde 01/01/2026 em lotes e conferir o período efetivamente coberto.
- [ ] Somente depois configurar e verificar atualização manual e diária, com acompanhamento de erros e horário de execução.
- [ ] Registrar aprovação da GEDIV e das áreas técnicas responsáveis antes de declarar a solução pronta para uso.

## Próxima ação técnica

1. Retomar os 59 arquivos cujo PDF não foi obtido e os 58 em que a busca falhou depois da abertura, inclusive os DOEs de 28 e 29/10, sem tratar falha como ausência.
2. Conferir no documento oficial os candidatos, as sete referências externas e as duas publicações da resenha 473/2026; manter casos não resolvidos em pendência.
3. Revisar a primeira correção preparada em cópia local: ela faz uma edição com pendências retornar à fila e conserva os dados da versão anterior se uma nova tentativa falhar.
4. Preparar OCR em português, conferir novamente a resenha 236/2026 e corrigir a leitura de continuações antes da carga histórica completa.

**Limites da primeira correção:** ela não resolve toda a leitura de colunas, não garante cobertura integral, não implementa versionamento completo e não conecta o robô ao dashboard. Os testes locais não comprovam operação automática no GitHub.

## Fontes do projeto

- [Pacote de captura e referências pendentes](https://chatgpt.com/library?file_id=libfile_f878685b13c481919aed00d2651e4399&account_id=personal).
- [Especificação funcional V3](https://chatgpt.com/library?file_id=libfile_6535d152185c8191b6afa1d32b21323c&account_id=personal).
- [Código atual do robô](https://github.com/gedivseadpb-boop/robo-gediv-pb/blob/main/src/robo.py).
- [Cópia do painel sem dados](https://github.com/gedivseadpb-boop/robo-gediv-pb/tree/main/painel-interativo).
- [Rotina prevista de coleta](https://github.com/gedivseadpb-boop/robo-gediv-pb/blob/main/.github/workflows/gediv.yml).
- [Critérios do projeto de referência](https://github.com/kaiooeduardoo/cursoesafi/blob/main/CRITERIOS_EXTRACAO.md).