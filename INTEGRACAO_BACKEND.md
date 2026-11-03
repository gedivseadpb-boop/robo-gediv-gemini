# Integração com o backend GEDIV

As duas interfaces usam `GET /api/gediv/data`, na mesma origem. A resposta segue o contrato de `/api/data` do painel privado de conferência. O servidor acessa somente esse destino fixo e mantém a credencial fora do navegador.

- `painel-interativo/index.html`: gráficos, filtros e exportações da visão selecionada.
- `site/index.html`: interface anterior e template dos arquivos produzidos pelo robô.
- `shared/gediv-client.mjs`: validação da resposta e adaptação para a interface anterior.
- `shared/gediv-gateway.mjs`: acesso de leitura ao backend e projeção autorizada.
- `server/local-preview.mjs`: servidor local restrito a `127.0.0.1`, para conferência privada. Requer `GEDIV_BACKEND_TOKEN` no ambiente do processo. Não serve para hospedagem pública.

## Comportamento

O carregamento inicial e Atualizar dados consultam o backend. Uma falha não apaga os dados já exibidos. A atualização de leitura não executa o robô nem homologa registros.

A gerente autorizada pode alternar entre Em conferência e Conferidos. Pendentes não são convertidos em conferidos. Refeitos e sem efeito permanecem sem total preliminar enquanto falta o vínculo documental. Resenhas usam seu identificador completo para evitar a fusão de publicações homônimas.

A consulta pública recebe somente decisões conferidas, sem matrícula e com nomes abreviados. O objeto privado original, textos de revisão, rejeições e pendências não são serializados para esse público. A autorização é verificada no servidor; escolher uma opção na tela não concede acesso.

## Ativação

O Observatório possui a implementação correspondente em `app/api/gediv/data/route.ts`. A variável secreta `GEDIV_BACKEND_TOKEN` deve ser configurada no servidor durante a ativação, preservando `OWNER_EMAIL` e a política de acesso existente. Não adicionar credencial em `data.js`, `NEXT_PUBLIC_*`, HTML, `.openai/hosting.json` ou arquivos versionados.

Os frontends estáticos precisam desse servidor na mesma origem. Abrir o código no GitHub ou publicar apenas os arquivos no GitHub Pages não configura a API privada.

Esta correção foi preparada para revisão sem alterar a branch principal, a execução agendada, o armazenamento ou a versão publicada. Nenhum banco adicional foi criado.

## Verificação

`node --test tests/integration.test.mjs` verifica contagens, separação por situação, projeção pública, respostas inválidas e falhas de conexão. As fixtures de testes são sintéticas e isoladas. O ensaio com a API real, quando realizado, é descrito separadamente no registro de validação.
