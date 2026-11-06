# Reddit Lead Search

CLI em Python para pesquisar posts públicos nas comunidades e pelos termos que o operador configurar. O programa somente lê dados via PRAW: não publica, comenta, vota, envia mensagens nem cria conteúdo de IA. A pontuação de relevância é uma regra simples e explicável baseada na quantidade de palavras-chave encontradas; não é uma avaliação de intenção comercial.

## Acesso à API e uso comercial

O Reddit exige aprovação explícita antes de qualquer acesso aos dados pela API. Uso comercial requer um acordo escrito separado. Este repositório não contém evidência de que essas aprovações foram concedidas. Por isso, o cliente API permanece bloqueado por padrão e a validação deste projeto usa mocks locais, sem chamadas ao Reddit.

Configure `REDDIT_API_APPROVED=true` e `REDDIT_COMMERCIAL_APPROVED=true` somente depois de obter as aprovações aplicáveis. Esses valores são travas locais e não concedem autorização. Consulte os [termos de desenvolvedor](https://redditinc.com/policies/developer-terms), os [termos da Data API](https://redditinc.com/policies/data-api-terms) e a [Responsible Builder Policy](https://support.reddithelp.com/hc/en-us/articles/42728983564564-Responsible-Builder-Policy).

## Requisitos e instalação

Validado com Python 3.13.14 no Windows. Crie um ambiente isolado:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-lock.txt
Copy-Item .env.example .env
```

No Linux/macOS:

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-lock.txt
cp .env.example .env
```

Credenciais e travas de aprovação ficam em `.env`, ignorado pelo Git. Use credenciais OAuth emitidas para o aplicativo autorizado; não use senha da conta pessoal. O programa não coleta nomes de usuário dos autores.

## Configurar busca e exportação

A busca aceita comunidades, termos, limite global, janela de tempo e quantidade mínima de termos correspondentes. Saída pode ser JSON ou CSV. Exemplo, depois das aprovações necessárias:

```powershell
python reddit_lead_scraper.py `
  --communities SEO,marketing,smallbusiness `
  --keywords "need seo,marketing help,looking for recommendations" `
  --max-results 50 `
  --lookback-days 7 `
  --min-matches 1 `
  --format csv `
  --output output\leads.csv
```

`--max-results` aceita de 1 a 1000; cada consulta individual pode percorrer até 1000 itens (o limite fornecido ao gerador do PRAW), e PRAW respeita os limites e backoff devolvidos pelo Reddit. Resultados repetidos pelo ID são eliminados. A janela exata também é filtrada localmente. A relevância vai de 0 a 100 e equivale à porcentagem dos termos configurados que apareceram no título ou texto do post.

O CSV escapa valores que planilhas poderiam interpretar como fórmulas. JSON/CSV incluem apenas ID do post, comunidade, título, permalink, data, pontuação, termos encontrados e relevância; não salvam nome do autor nem o corpo completo. Observe as regras de uso, privacidade e retenção de dados aplicáveis ao seu acordo com o Reddit.

O escape do CSV também cobre a célula de termos encontrados após a junção. Datas não finitas ou futuras são descartadas. Falhas de preparação ou paginação encerram a coleta com erro, sem apresentar uma coleta parcial como sucesso; a mensagem pública mostra contexto e classe da falha, sem copiar texto bruto de exceções que poderia conter credenciais.

Exemplo sintético (não são dados reais do Reddit):

```json
[
  {
    "post_id": "synthetic-001",
    "community": "smallbusiness",
    "title": "Looking for recommendations on SEO",
    "permalink": "https://www.reddit.com/r/smallbusiness/comments/synthetic-001/",
    "created_utc": 1790000000,
    "score": 3,
    "matched_keywords": ["looking for recommendations"],
    "relevance_score": 33
  }
]
```

## Testes sem credenciais

```powershell
python -m unittest discover -s tests -v
```

Os testes usam posts sintéticos e um cliente mockado. Não fazem chamadas externas e não requerem credenciais.

A auditoria final passou em 21 testes e também construiu o cliente PRAW real com dados sintéticos e HTTP bloqueado, verificando `read_only`. Isso comprova configuração local, não autenticação, permissões ou acesso real à API. Evidências em `docs/recovery/02-final-audit.md`.

## Escopo e limitações

- Busca posts, não comentários; comunidades, termos, janela e limite são configuráveis.
- Busca de texto e relevância são limitadas pelo que a API retorna e pela regra local simples; não representam completude nem intenção de compra.
- Uma execução real depende de credenciais, aprovação explícita para API e acordo comercial escrito. Nenhuma execução real foi feita nesta recuperação.
- `openclaw_wrapper.py` é um protótipo legado: aponta para um caminho fixo de Linux e menciona `outreach_engine.py`, que não existe neste repositório. Não é parte do fluxo suportado. Não há publicação automática ou integração de aprovação validada.
