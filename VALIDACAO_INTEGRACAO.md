# Validação da integração — 02/11/2026

## Resultado verificável

- Nove testes de contrato e integração dos frontends passaram.
- Dois testes dos handlers reais do Observatório passaram: autorização da gerente, exclusão de pendências da resposta pública, adaptação das categorias e resposta 503 em falha.
- A verificação TypeScript e a compilação do Observatório passaram.
- Os testes de domínio existentes passaram, incluindo contagens, filtros, deduplicação e localização de páginas.
- O histórico real incluído no código do backend foi reprojetado localmente: 310 recebidos, 309 pendentes. As duas interfaces do GitHub e a adaptação do Observatório selecionaram os mesmos 309 candidatos. Esse ensaio não acessou nem alterou o armazenamento de produção.
- O JavaScript do template anterior foi analisado, preservando sua execução offline e o marcador usado pelo coletor.

## Limites de verificação

O status oficial consultado no início deste trabalho retornou 328 recebidos, 327 pendentes, um rejeitado e zero conferidos. Esse retorno comprova o estado informado pelo backend, mas não comprova o funcionamento da nova integração HTTP.

A chamada direta ao endpoint privado neste ambiente recebeu HTTP 403. A prévia gerenciada iniciou, mas o navegador não conseguiu abrir sua URL interna. Portanto, não há homologação visual nem comprovação de leitura HTTP entre os serviços publicados. Não se atribuiu a causa do 403 a um componente específico sem evidência.

## Entrega e ativação

As alterações ficam em revisão no GitHub e em uma versão salva do mesmo Observatório, sem implantação. Não foram criados Sites, bancos, lotes, validações ou agendamentos. A versão pública existente e a audiência foram preservadas.

Para ativar, é necessário configurar no servidor o segredo de leitura do backend privado, publicar a versão salva e verificar a sessão autorizada e a consulta pública. A configuração da variável e a publicação alteram produção e ficaram fora desta entrega, preservando a restrição anterior da usuária.

O botão Atualizar dados consulta resultados já recebidos. A extração dos PDFs, a conclusão da cobertura histórica e a remessa automática do coletor ao backend continuam sendo tarefas distintas. Os dados pendentes não foram homologados.
