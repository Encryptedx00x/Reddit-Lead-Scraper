# Auditoria final do PR #1

Revisado contra `origin/main`; commit `ab81904` preservado.

## Defeitos e correções

- O CSV aplicava escape ao título, mas ignorava a célula `matched_keywords` após a junção; palavra-chave `=1+1` ficava como fórmula potencial. Escape agora é aplicado a todos os textos finais.
- Timestamp `NaN`/infinito passava pela comparação e abortava a busca ao converter para inteiro. São descartadas datas não finitas e posteriores ao relógio de referência.
- Exceção ao preparar uma comunidade escapava do tratamento da CLI. Agora é contextualizada como `RedditClientError`.
- Exceções de paginação eram copiadas integralmente na mensagem pública. Testes mostraram propagação de segredo sintético; agora só classe/contexto são expostos.

## Verificação

- `python -m unittest discover -s tests -q`: **21 testes aprovados**.
- Deduplicação, janela, filtros/relevância, limite global, orçamento máximo de consultas, erros de paginação e saída JSON/CSV verificados com dados sintéticos.
- Construtor PRAW real foi usado com credenciais sintéticas e `requests.Session.request` bloqueado: `read_only=True`, nenhuma chamada HTTP. Configuração `ratelimit_seconds=300` e gates de aprovação cobertos pelos testes.
- Falha em página posterior termina em erro; não retorna sucesso parcial silencioso.
- `pip check`, CLI `--help` e `git diff --check`: aprovados.
- Nenhuma chamada de dados à API Reddit, conta pessoal ou envio de mensagens foi realizado.

## Decisão

**GO para merge da CLI com ressalva de integração externa**. Autenticação real, permissões concedidas, limites/quota e comportamento do servidor Reddit não foram homologados. Continuam pendentes credenciais e evidência das aprovações aplicáveis. O wrapper OpenClaw legado continua fora do fluxo suportado; não é integração de outreach validada. PR permanece draft.
