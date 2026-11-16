# Guardião Anti-Riot

Contador de **"dias livre do LoL"** com uma camada de vigilância que age automaticamente
quando algo da Riot aparece no PC. Feito para quem quer se manter longe de League of
Legends / VALORANT.

## O que faz

- Mostra há quantos dias você está livre do LoL.
- **Vigilância por eventos** (não fica varrendo o disco o tempo todo):
  - Remove instaladores da Riot que apareçam nas pastas monitoradas (Downloads, Desktop, Temp).
  - Encerra processos da Riot (Riot Client, VALORANT, League) assim que eles iniciam.
- **Escudo de pastas:** cria arquivos chamados `Riot Games` nas raízes dos discos para
  impedir a criação das pastas de instalação do jogo.
- **Bloqueio de rede** (opcional, requer administrador): bloqueia os domínios da Riot
  pelo arquivo `hosts`.

## Requisitos

- Windows 10 ou 11
- Python 3 (o `tkinter`, usado na interface, já vem no instalador oficial do python.org)

## Como usar

1. Instale o Python 3 em https://www.python.org/downloads/ (marque **Add python.exe to PATH**).
2. Dê duplo-clique em **`Iniciar.vbs`**.
3. Clique em **Configurar data de início** e informe desde quando você está livre.

Para abrir junto com o Windows, crie um atalho de `Iniciar.vbs` na pasta de Inicializar
(Win+R → `shell:startup`).

## Configuração (`config.json`)

Criado automaticamente na primeira execução:

| Campo              | Descrição                                              |
|--------------------|--------------------------------------------------------|
| `quit_date`        | Data em que você parou (AAAA-MM-DD)                    |
| `guardian_enabled` | Liga/desliga a vigilância                              |
| `folder_shield`    | Liga/desliga o escudo de pastas                        |
| `network_block`    | Estado do bloqueio de rede                             |
| `watch_dirs`       | Pastas extras a monitorar, ex.: `["E:\\1BAIXADOS"]`    |

## Estrutura

| Arquivo                   | Função                                                        |
|---------------------------|---------------------------------------------------------------|
| `guardiao.py`             | Interface, contador e servidor local (instância única)        |
| `monitor.ps1`             | Vigilância por eventos (FileSystemWatcher + WMI)              |
| `ativar_bloqueio.ps1`     | Ativa o bloqueio de rede (hosts)                              |
| `desativar_bloqueio.ps1`  | Desativa o bloqueio de rede (hosts)                           |
| `Iniciar.vbs`             | Inicializador sem janela de console                           |
| `guardiao.ico`            | Ícone do app                                                  |

## Aviso

Ferramenta pessoal de disciplina. Use por sua conta e risco.

## Licença

MIT — veja o arquivo [LICENSE](LICENSE).
