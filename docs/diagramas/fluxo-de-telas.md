# Fluxo de telas

Nove telas, gerenciadas por um `ScreenManager`. O menu principal é o centro: toda tela de
trabalho volta para ele.

```mermaid
stateDiagram-v2
    [*] --> Login

    Login --> AlterarSenha : primeiro acesso
    Login --> Inicio : credenciais válidas
    Login --> Login : usuário ou senha incorretos

    AlterarSenha --> Inicio : senha definida
    AlterarSenha --> Login : cancelar no primeiro acesso

    Inicio --> Lancamento : Lançar ocorrência
    Inicio --> Consulta : Consultar / Pendentes
    Inicio --> Queima : Registrar queima
    Inicio --> Clima : Registrar clima
    Inicio --> Indicadores : Indicadores
    Inicio --> Usuarios : Usuários (só admin)
    Inicio --> AlterarSenha : Trocar senha
    Inicio --> Login : Sair da conta
    Inicio --> [*] : Fechar programa

    Lancamento --> Inicio : Voltar
    Consulta --> Inicio : Voltar
    Queima --> Inicio : Voltar
    Clima --> Inicio : Voltar
    Indicadores --> Inicio : Voltar
    Usuarios --> Inicio : Voltar
    Usuarios --> Inicio : acesso negado a não-admin
```

## Sequência de um lançamento

Mostra a separação entre as camadas: a tela nunca fala com o banco.

```mermaid
sequenceDiagram
    actor U as Operador
    participant T as TelaLancamento
    participant S as servicos.registros
    participant A as servicos.anexos
    participant R as dados.repositorio_ocorrencias
    participant B as SQLite

    U->>T: preenche o formulário e clica em SALVAR
    T->>S: salvar_ocorrencia(campos como texto)

    S->>S: valida data, categoria, serviço, gleba e quadra
    alt algum campo inválido
        S-->>T: ErroValidacao("Informe a quadra.")
        T-->>U: diálogo "Não foi possível salvar"
    else formulário completo
        S->>A: guardar(cada foto escolhida)
        A->>A: confere extensão e tamanho
        A-->>S: nome único do arquivo copiado
        S->>R: buscar_gleba(código)
        R-->>S: fazenda, município, administrador
        S->>R: inserir(Ocorrencia)
        R->>B: INSERT ocorrencia + INSERT anexos (uma transação)
        B-->>R: id gerado
        R-->>S: id
        S-->>T: id
        T-->>U: "Ocorrência 46 registrada." e formulário limpo
    end
```

## Sequência do login

```mermaid
sequenceDiagram
    actor U as Usuário
    participant T as TelaLogin
    participant G as GerenciadorAutenticacao
    participant R as repositorio_usuarios
    participant Sg as seguranca

    U->>T: login e senha
    T->>G: entrar(login, senha)
    G->>G: verifica bloqueio por tentativas
    G->>R: buscar_por_login / obter_credencial
    R-->>G: usuário, (hash, sal)
    G->>Sg: verificar_senha(senha, hash, sal)
    Sg-->>G: verdadeiro ou falso

    alt senha incorreta
        G->>G: incrementa tentativas (bloqueia na quinta)
        G-->>T: ErroAutenticacao("Usuário ou senha incorretos.")
        T-->>U: diálogo de erro
    else primeiro acesso
        G-->>T: PrecisaTrocarSenha(login)
        T-->>U: tela de troca de senha
    else tudo certo
        G->>G: abre a sessão
        G-->>T: usuário
        T-->>U: menu principal
    end
```
