# Arquitetura

Documento de apoio ao TCC: como o sistema está organizado, por que cada decisão foi
tomada e quais defeitos da versão anterior elas corrigem.

## 1. Requisitos que moldaram o desenho

Três restrições determinaram quase tudo:

1. **Precisa rodar em qualquer computador.** A versão anterior carregava telas, banco e
   imagens de um compartilhamento de rede corporativo. Fora daquela rede, o programa
   quebrava na inicialização.
2. **Não pode depender de rede nem da internet.** Sem servidor, sem API, sem nuvem. Isso
   descartou o dashboard hospedado e a automação de navegador que o abria.
3. **Não pode conter dado sensível.** O código-fonte anterior trazia e-mail e senha
   corporativos em texto puro, e o banco guardava senhas de usuário sem qualquer proteção.

## 2. Camadas

```
┌─────────────────────────────────────────────┐
│ telas/        Kivy + KivyMD                 │  coleta entrada, mostra resultado
├─────────────────────────────────────────────┤
│ servicos/     regras de negócio             │  valida, converte, decide
├─────────────────────────────────────────────┤
│ dados/        repositórios + SQL            │  única camada que fala com o banco
├─────────────────────────────────────────────┤
│ dominio/      catálogo e estruturas         │  vocabulário do problema
└─────────────────────────────────────────────┘
```

A dependência aponta sempre para baixo. Uma tela não monta SQL; um repositório não sabe
que existe interface. É o que permite testar toda a regra de negócio sem abrir janela —
os 119 testes rodam em cerca de 15 segundos, sem instanciar o Kivy.

### O que cada camada faz

| Camada | Responsabilidade | Exemplo |
|---|---|---|
| `dominio/` | Vocabulário: 27 categorias, 134 serviços, e as estruturas `Ocorrencia`, `Queima`, `RegistroClima` | `catalogo.separar_codigo("4.1 - Buracos")` |
| `dados/` | Criar o banco, semear o catálogo, executar consultas parametrizadas | `repositorio_ocorrencias.listar(filtro)` |
| `servicos/` | Validar o formulário, converter texto em tipo, aplicar regra | `registros.concluir_ocorrencia(...)` |
| `telas/` | Ler campos, chamar o serviço, exibir a mensagem que voltar | `TelaLancamento.salvar()` |

## 3. Decisões e o defeito que cada uma corrige

### 3.1 Caminhos resolvidos em execução

**Antes.** Onze caminhos absolutos escritos no código, todos apontando para uma unidade de
rede mapeada (`U:\...`). Os cinco arquivos `.kv` e as cinco imagens vinham de lá, e o banco
também. As imagens sequer estavam versionadas.

**Agora.** `config.py` resolve tudo em tempo de execução. Recursos estáticos saem de
`Path(__file__).parent` (ou de `sys._MEIPASS`, sob PyInstaller). O diretório de dados
segue três regras, nesta ordem: variável `DONC_DIR`; pasta `dados/` ao lado do executável,
se existir — o que dá o modo portátil em pendrive; senão, o diretório do usuário do
sistema operacional.

Escrever no diretório do usuário, e não ao lado do programa, também evita o problema de
permissão de quem instala em `Program Files`.

### 3.2 Senhas com PBKDF2

**Antes.** `Usuarios.Senha` guardava a senha legível. Quem abrisse o arquivo `.db` com
qualquer visualizador SQLite via as senhas de todo mundo.

**Agora.** Guarda-se `senha_hash` e `sal`, resultado de PBKDF2-HMAC-SHA256 com 240 mil
iterações e um sal aleatório de 16 bytes por usuário. Só a biblioteca padrão, sem
dependência externa. A comparação usa `hmac.compare_digest`, que não vaza informação pelo
tempo de resposta.

O sal por usuário importa: sem ele, dois usuários com a mesma senha teriam o mesmo hash, e
isso seria visível na tabela.

### 3.3 Datas em ISO-8601

**Antes.** As datas eram gravadas como `dd/mm/aaaa`, e os dias pendentes calculados assim:

```sql
CASE WHEN Data_conclusao = "" THEN (strftime("%d/%m/%Y","now") - "Data Parada")
     ELSE (Data_conclusao - "Data Parada") END
```

Em SQLite isso é subtração entre strings. `"11/09/2026"` convertido para número vira `11`,
e a conta devolve um valor sem relação alguma com a quantidade de dias.

**Agora.** As datas vão para o banco em `AAAA-MM-DD`, único formato que o SQLite ordena e
compara corretamente como texto. O cálculo virou:

```sql
CAST(julianday(COALESCE(data_conclusao, date('now','localtime')))
     - julianday(data_abertura) AS INTEGER) AS dias_pendentes
```

A conversão para `dd/mm/aaaa` acontece só na hora de exibir, em `servicos/formato.py`.
O teste `test_dias_pendentes_conta_ate_hoje` fixa o comportamento.

### 3.4 Esquema normalizado

**Antes.** Uma tabela, `BANCO_DE_OLHO_NA_CANA`, com 16 colunas de texto, incluindo uma
chamada `"Data Parada"` — com espaço no nome, o que obriga aspas em toda consulta. Categoria
e serviço eram texto livre repetido em cada linha.

**Agora.** Sete tabelas e uma visão. Categorias e serviços viraram tabelas próprias,
referenciadas por chave estrangeira; glebas também, substituindo a planilha
`Espelho_banco_Glebas.xlsx` e eliminando a dependência do pandas. Restrições `CHECK`
garantem no banco aquilo que antes dependia da interface lembrar:

```sql
CHECK ((status = 'Finalizado' AND data_conclusao IS NOT NULL)
    OR (status = 'Pendente'   AND data_conclusao IS NULL))
```

Não há como gravar uma ocorrência finalizada sem data de conclusão, nem uma conclusão
anterior à abertura — dois testes provam que o banco recusa.

A visão `vw_ocorrencias` concentra a junção com o catálogo e o cálculo de dias pendentes,
para que nenhuma consulta da aplicação precise repetir isso.

### 3.5 Indicadores locais no lugar do Power BI

**Antes.** O botão de dashboard abria o Chrome com Selenium, digitava e-mail e senha
corporativos escritos no código e navegava até um relatório na nuvem. Exigia internet,
Chrome instalado e um ChromeDriver da versão exata — o repositório antigo chegava a
carregar um `chromedriver.exe` de 19 MB.

**Agora.** `servicos/indicadores.py` lê o banco e desenha quatro gráficos com matplotlib
no backend `Agg`, salvando um PNG que a tela exibe. Sem rede, sem navegador, sem
credencial. O backend `Agg` é obrigatório: o matplotlib não pode tentar abrir uma janela
enquanto o Kivy é dono do laço gráfico.

### 3.6 Anexos copiados, não referenciados

**Antes.** O caminho absoluto da foto escolhida ia direto para o banco. Mover ou renomear
o arquivo original quebrava o registro.

**Agora.** `servicos/anexos.py` copia a imagem para `dados/anexos/` com um nome único
derivado de UUID, e o banco guarda só esse nome. Banco e pasta de anexos formam um
conjunto autocontido que pode ser copiado para outra máquina. Duas fotos chamadas
`foto.jpg` não colidem.

### 3.7 Um seletor de arquivos, não quatro

**Antes.** Quatro instâncias de `MDFileManager`, quatro métodos `file_manager_openN`,
quatro `select_pathN`, quatro `exit_managerN` e quatro `eventsN` — cerca de cem linhas de
código idêntico. Três deles escreviam em ids (`imagem1`, `imagem2`, `imagem3`) que não
existiam no arquivo `.kv`, de modo que só um dos quatro chegava a funcionar.

**Agora.** Um `MDFileManager` em `app.py`, e quem chama informa o que fazer com o caminho:

```python
self.aplicativo.escolher_arquivo(lambda caminho: self._foto_escolhida(indice, caminho))
```

### 3.8 Injeção de SQL fechada na atualização

`repositorio_ocorrencias.atualizar` monta a cláusula `SET` a partir de nomes de coluna.
Para que nome nenhum chegue ao SQL vindo da tela, há uma lista de permissão:

```python
desconhecidas = set(campos) - COLUNAS_EDITAVEIS
if desconhecidas:
    raise ValueError(f"Colunas inválidas: {...}")
```

Todos os valores seguem por parâmetros `?`. O teste
`test_atualizar_rejeita_coluna_desconhecida` cobre o caso.

## 4. Fluxo de um lançamento

1. `TelaLancamento.salvar()` lê os campos e chama `registros.salvar_ocorrencia(...)`.
2. O serviço valida: data preenchida e não futura, categoria e serviço escolhidos, gleba e
   quadra informadas. Qualquer falha vira `ErroValidacao` com mensagem pronta para o usuário.
3. As fotos passam por `anexos.guardar()`, que confere extensão e tamanho e copia o arquivo.
4. A gleba é consultada para preencher fazenda, município e administrador.
5. `repositorio_ocorrencias.inserir()` grava a ocorrência e os anexos **numa transação só**
   — se qualquer anexo falhar, a ocorrência não fica gravada pela metade.
6. A tela mostra o número gerado e limpa o formulário.

## 5. Tratamento de erro

Cada camada tem sua exceção, e cada uma carrega uma frase que pode ser mostrada ao usuário
sem tradução:

| Exceção | Origem | Vira |
|---|---|---|
| `ErroValidacao` | `servicos/registros.py` | diálogo "Não foi possível salvar" |
| `ErroAutenticacao` | `servicos/autenticacao.py` | diálogo "Não foi possível entrar" |
| `PrecisaTrocarSenha` | `servicos/autenticacao.py` | desvio para a tela de troca de senha |
| `ErroAnexo` | `servicos/anexos.py` | convertida em `ErroValidacao` |
| `sqlite3.IntegrityError` | banco | erro de programação; não é capturada para esconder |

A última linha é deliberada: violação de `CHECK` significa que a validação da camada de
serviço deixou passar algo. Esconder isso mascararia o defeito.

## 6. Limites conhecidos

- **Um computador por vez.** Sem sincronização entre máquinas — é requisito, não omissão.
  SQLite aceita leitura concorrente, mas o sistema não foi pensado para acesso simultâneo.
- **Sem teste de interface.** As telas não têm cobertura automatizada; foram verificadas
  por um roteiro manual que percorre as nove telas.
- **Paginação da tabela em inglês.** "Rows per page" vem do próprio KivyMD 1.2.0 e não é
  configurável sem alterar a biblioteca.
- **KivyMD 1.2.0.** A série 2.x removeu o `MDDataTable`, usado nas telas de consulta e de
  usuários. Migrar exigiria reescrever essas duas telas.
