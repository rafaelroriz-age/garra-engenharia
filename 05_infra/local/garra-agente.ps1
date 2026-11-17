<#
.SYNOPSIS
    Agente de inicializacao do PC de producao Garra: atualiza, sobe backend + tunel cloudflared e
    publica api.json / snapshot.enc na branch `snapshot` do repo publico (DEC-57, T82).

.DESCRIPTION
    Roda no logon (tarefa agendada "Garra Local", ver `garra-local.ps1 install`) e fica em laco:
      1. git pull --ff-only origin main (so se a arvore estiver limpa e a branch atual for main)
      2. reinstala requirements.txt no venv-prod se o hash mudou
      3. garra-local.ps1 start (Postgres, migrations, seeds, uvicorn)
      4. cloudflared tunnel --url http://127.0.0.1:<porta>; extrai https://*.trycloudflare.com do log
      5. publica api.json {url, api_base, online, desde, heartbeat} e snapshot.enc (T81)
      6. laco: heartbeat a cada AGENTE_HEARTBEAT_MIN, snapshot a cada AGENTE_SNAPSHOT_MIN (so se mudou),
         backup diario; reinicia cloudflared (e republica a nova URL) ou o backend se cairem
      7. ao encerrar (Ctrl+C, fim normal) publica online:false e derruba o cloudflared

    Publicacao: clone dedicado em %LOCALAPPDATA%\garra\publico; a cada vez um commit unico, sem pai
    (equivale a checkout --orphan), e push forcado para a branch `snapshot`. O token
    (GARRA_PUBLIC_TOKEN) so existe em memoria, na URL do push; nunca vai para .git/config nem para o log.

    Parametros de teste (nao usados na tarefa agendada):
      -RemotoAlternativo  caminho/URL de um remoto no lugar do GitHub (ex.: repo bare local)
      -UmaVez             faz um ciclo completo, publica online:false e sai
      -SemBackend         nao sobe o backend nem gera o snapshot
      -SemAtualizar       nao faz git pull nem pip
      -SemTunel           nao sobe o cloudflared (usa -UrlFixa)
      -UrlFixa            URL publica a gravar no api.json quando -SemTunel
      -SnapshotArquivo    copia este arquivo como snapshot.enc em vez de gerar

    Texto so em ASCII de proposito (Windows PowerShell 5.1 le .ps1 sem BOM como ANSI).
#>
[CmdletBinding()]
param(
    [string]$RemotoAlternativo = '',
    [switch]$UmaVez,
    [switch]$SemBackend,
    [switch]$SemAtualizar,
    [switch]$SemTunel,
    [string]$UrlFixa = '',
    [string]$SnapshotArquivo = '',
    [string]$PastaPublico = ''
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'

$LocalDir   = $PSScriptRoot
$RepoDir    = (Resolve-Path (Join-Path $LocalDir '..\..')).Path
$BackendDir = Join-Path $RepoDir '04_backend'
$LogDir     = Join-Path $LocalDir 'logs'
$RunDir     = Join-Path $LocalDir 'run'
$EnvFile    = Join-Path $LocalDir '.env'
$LogFile    = Join-Path $LogDir 'garra-agente.log'
$VenvPython = Join-Path $BackendDir '.venv-prod\Scripts\python.exe'
$GarraLocal = Join-Path $LocalDir 'garra-local.ps1'
$PsExe      = Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe'
$TunelLog   = Join-Path $RunDir 'cloudflared.err.log'
$TunelPid   = Join-Path $RunDir 'cloudflared.pid'
$SnapLocal  = Join-Path $RunDir 'snapshot.enc'
$ReqHashArq = Join-Path $RunDir 'requirements.sha256'
$BackupMarca = Join-Path $RunDir 'ultimo-backup.txt'
if ($PastaPublico) { $PublicoDir = $PastaPublico } else { $PublicoDir = Join-Path $env:LOCALAPPDATA 'garra\publico' }
foreach ($d in @($LogDir, $RunDir)) { if (-not (Test-Path -LiteralPath $d)) { New-Item -ItemType Directory -Path $d | Out-Null } }

$script:Segredos = @()
$script:Desde = ''
$script:Url = ''
$script:Tunel = $null

# ----------------------------------------------------------------------------------------------
# Log com rotacao simples (5 MB, mantem 3 anteriores)
# ----------------------------------------------------------------------------------------------
function Invoke-RotacaoLog([string]$Arquivo, [int]$MaxBytes = 5242880) {
    if (-not (Test-Path -LiteralPath $Arquivo)) { return }
    if ((Get-Item -LiteralPath $Arquivo).Length -lt $MaxBytes) { return }
    $base = [IO.Path]::Combine([IO.Path]::GetDirectoryName($Arquivo), [IO.Path]::GetFileNameWithoutExtension($Arquivo))
    $ext = [IO.Path]::GetExtension($Arquivo)
    foreach ($n in 3, 2, 1) {
        $o = '{0}.{1}{2}' -f $base, $n, $ext
        if (Test-Path -LiteralPath $o) {
            if ($n -eq 3) { Remove-Item -LiteralPath $o -Force } else { Move-Item -LiteralPath $o -Destination ('{0}.{1}{2}' -f $base, ($n + 1), $ext) -Force }
        }
    }
    Move-Item -LiteralPath $Arquivo -Destination ('{0}.1{1}' -f $base, $ext) -Force
}

function Hide-Segredos([string]$Texto) {
    foreach ($s in $script:Segredos) { if ($s) { $Texto = $Texto.Replace($s, '***') } }
    return $Texto
}

function Write-Log {
    param([string]$Mensagem, [ValidateSet('INFO', 'WARN', 'ERRO')][string]$Nivel = 'INFO')
    Invoke-RotacaoLog $LogFile
    $linha = '{0} [{1}] {2}' -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $Nivel, (Hide-Segredos $Mensagem)
    Add-Content -LiteralPath $LogFile -Value $linha -Encoding UTF8
    if ($Nivel -eq 'ERRO') { Write-Host $linha -ForegroundColor Red }
    elseif ($Nivel -eq 'WARN') { Write-Host $linha -ForegroundColor Yellow }
    else { Write-Host $linha }
}

# ----------------------------------------------------------------------------------------------
# Execucao de nativos (sem 2>&1, que no PS 5.1 vira ErrorRecord)
# ----------------------------------------------------------------------------------------------
function ConvertTo-ArgWindows([string]$Arg) {
    if ($Arg -eq '') { return '""' }
    if ($Arg -notmatch '[\s"]') { return $Arg }
    $s = $Arg -replace '(\\*)"', '$1$1\"'
    $s = $s -replace '(\\+)$', '$1$1'
    return '"' + $s + '"'
}

function Invoke-Exe {
    param(
        [Parameter(Mandatory)][string]$Exe,
        [string[]]$Argumentos = @(),
        [string]$Diretorio = $RunDir,
        [int]$TimeoutSeg = 600,
        [switch]$Silencioso
    )
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $Exe
    $psi.Arguments = (($Argumentos | ForEach-Object { ConvertTo-ArgWindows $_ }) -join ' ')
    $psi.WorkingDirectory = $Diretorio
    $psi.UseShellExecute = $false
    $psi.CreateNoWindow = $true
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.StandardOutputEncoding = [Text.Encoding]::UTF8
    $psi.StandardErrorEncoding = [Text.Encoding]::UTF8
    $nome = [IO.Path]::GetFileName($Exe)
    if (-not $Silencioso) { Write-Log ("exec: {0} {1}" -f $nome, $psi.Arguments) }
    $p = [Diagnostics.Process]::Start($psi)
    $tOut = $p.StandardOutput.ReadToEndAsync()
    $tErr = $p.StandardError.ReadToEndAsync()
    if (-not $p.WaitForExit($TimeoutSeg * 1000)) {
        try { $p.Kill() } catch { }
        return [pscustomobject]@{ Codigo = -1; Saida = "$nome excedeu ${TimeoutSeg}s" }
    }
    $p.WaitForExit()
    $saida = ($tOut.Result + $tErr.Result).TrimEnd()
    if ($saida -and -not $Silencioso) {
        foreach ($l in ($saida -split "`r?`n")) { Add-Content -LiteralPath $LogFile -Value ('    | ' + (Hide-Segredos $l)) -Encoding UTF8 }
    }
    return [pscustomobject]@{ Codigo = $p.ExitCode; Saida = $saida }
}

# ----------------------------------------------------------------------------------------------
# Configuracao (.env local)
# ----------------------------------------------------------------------------------------------
function Get-Config {
    if (-not (Test-Path -LiteralPath $EnvFile)) { throw "Falta $EnvFile. Rode primeiro: garra-local.ps1 setup" }
    $cfg = [ordered]@{}
    foreach ($linha in [IO.File]::ReadAllLines($EnvFile)) {
        $t = $linha.Trim()
        if ($t -eq '' -or $t.StartsWith('#')) { continue }
        $i = $t.IndexOf('=')
        if ($i -lt 1) { continue }
        $cfg[$t.Substring(0, $i).Trim()] = $t.Substring($i + 1).Trim()
    }
    $padroes = @{
        UVICORN_HOST = '127.0.0.1'; UVICORN_PORT = '8000'; GARRA_PUBLIC_REPO = 'rafaelroriz-age/garra-engenharia'
        AGENTE_HEARTBEAT_MIN = '10'; AGENTE_SNAPSHOT_MIN = '30'; AGENTE_TICK_SEG = '15'
    }
    foreach ($k in $padroes.Keys) { if (-not $cfg.Contains($k) -or -not $cfg[$k]) { $cfg[$k] = $padroes[$k] } }
    foreach ($k in 'GARRA_PUBLIC_TOKEN', 'SNAPSHOT_SENHA') { if (-not $cfg.Contains($k)) { $cfg[$k] = '' } }
    $script:Segredos = @($cfg['GARRA_PUBLIC_TOKEN'], $cfg['POSTGRES_PASSWORD'], $cfg['JWT_SECRET_KEY'], $cfg['ADMIN_SENHA'], $cfg['DEEPSEEK_API_KEY'], $cfg['SNAPSHOT_SENHA'] | Where-Object { $_ })
    return $cfg
}

function Set-AmbienteProcesso($cfg) {
    foreach ($k in $cfg.Keys) { Set-Item -Path ("Env:" + $k) -Value ([string]$cfg[$k]) }
    $env:PYTHONPATH = $BackendDir
    $env:PYTHONUTF8 = '1'
    $env:PYTHONIOENCODING = 'utf-8'
    if ($cfg.Contains('POSTGRES_PASSWORD')) { $env:PGPASSWORD = $cfg['POSTGRES_PASSWORD'] }
    $env:GIT_TERMINAL_PROMPT = '0'
}

# ----------------------------------------------------------------------------------------------
# Atualizacao do codigo
# ----------------------------------------------------------------------------------------------
function Get-Git {
    $g = Get-Command git -ErrorAction SilentlyContinue
    if (-not $g) { throw 'git nao encontrado no PATH.' }
    return $g.Source
}

function Update-Codigo {
    $git = Get-Git
    $sujo = Invoke-Exe $git @('-C', $RepoDir, 'status', '--porcelain') -Silencioso
    if ($sujo.Codigo -ne 0) { Write-Log "atualizacao pulada: git status falhou ($($sujo.Saida))" 'WARN'; return }
    if ($sujo.Saida) { Write-Log 'atualizacao pulada: arvore de trabalho com alteracoes; segue com o codigo atual' 'WARN'; return }
    $br = Invoke-Exe $git @('-C', $RepoDir, 'rev-parse', '--abbrev-ref', 'HEAD') -Silencioso
    if ($br.Saida.Trim() -ne 'main') { Write-Log ("atualizacao pulada: branch atual '{0}' nao e main; segue com o codigo atual" -f $br.Saida.Trim()) 'WARN'; return }
    $r = Invoke-Exe $git @('-C', $RepoDir, 'pull', '--ff-only', 'origin', 'main') -TimeoutSeg 180
    if ($r.Codigo -ne 0) { Write-Log 'git pull --ff-only falhou; segue com o codigo atual' 'WARN' }
}

function Update-Dependencias {
    $req = Join-Path $BackendDir 'requirements.txt'
    if (-not (Test-Path -LiteralPath $req) -or -not (Test-Path -LiteralPath $VenvPython)) { return }
    $hash = (Get-FileHash -LiteralPath $req -Algorithm SHA256).Hash
    $antigo = ''
    if (Test-Path -LiteralPath $ReqHashArq) { $antigo = ([IO.File]::ReadAllText($ReqHashArq)).Trim() }
    if ($hash -eq $antigo) { Write-Log 'requirements.txt inalterado'; return }
    Write-Log 'requirements.txt mudou: pip install -r'
    $r = Invoke-Exe $VenvPython @('-m', 'pip', 'install', '--disable-pip-version-check', '-r', $req) -TimeoutSeg 1800
    if ($r.Codigo -eq 0) { [IO.File]::WriteAllText($ReqHashArq, $hash) } else { Write-Log 'pip install falhou; segue com as dependencias atuais' 'WARN' }
}

# ----------------------------------------------------------------------------------------------
# Backend
# ----------------------------------------------------------------------------------------------
function Test-Backend($cfg) {
    $url = 'http://{0}:{1}/health' -f $cfg['UVICORN_HOST'], $cfg['UVICORN_PORT']
    try { $r = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 5; return ([int]$r.StatusCode -eq 200) }
    catch { return $false }
}

function Start-Backend {
    Write-Log 'subindo o backend (garra-local.ps1 start)'
    $r = Invoke-Exe $PsExe @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $GarraLocal, 'start') -TimeoutSeg 900
    if ($r.Codigo -ne 0) { Write-Log "garra-local.ps1 start terminou com codigo $($r.Codigo)" 'ERRO'; return $false }
    return $true
}

# ----------------------------------------------------------------------------------------------
# Tunel cloudflared
# ----------------------------------------------------------------------------------------------
function Find-Cloudflared {
    $c = Get-Command cloudflared -ErrorAction SilentlyContinue
    if ($c) { return $c.Source }
    foreach ($p in @("${env:ProgramFiles(x86)}\cloudflared\cloudflared.exe", "$env:ProgramFiles\cloudflared\cloudflared.exe")) {
        if ($p -and (Test-Path -LiteralPath $p)) { return $p }
    }
    throw 'cloudflared nao encontrado (PATH ou C:\Program Files (x86)\cloudflared).'
}

function Stop-Tunel {
    if ($script:Tunel) { try { if (-not $script:Tunel.HasExited) { $script:Tunel.Kill() } } catch { } }
    $script:Tunel = $null
    if (Test-Path -LiteralPath $TunelPid) {
        $velho = 0
        [int]::TryParse(([IO.File]::ReadAllText($TunelPid)).Trim(), [ref]$velho) | Out-Null
        if ($velho -gt 0) {
            $p = Get-Process -Id $velho -ErrorAction SilentlyContinue
            if ($p -and $p.ProcessName -eq 'cloudflared') { try { $p.Kill() } catch { } }
        }
        Remove-Item -LiteralPath $TunelPid -Force -ErrorAction SilentlyContinue
    }
}

function Get-UrlDoLog {
    if (-not (Test-Path -LiteralPath $TunelLog)) { return '' }
    $fs = [IO.File]::Open($TunelLog, 'Open', 'Read', 'ReadWrite')
    try { $texto = (New-Object IO.StreamReader($fs, [Text.Encoding]::UTF8)).ReadToEnd() } finally { $fs.Dispose() }
    foreach ($m in [regex]::Matches($texto, 'https://([a-z0-9-]+)\.trycloudflare\.com')) {
        if ($m.Groups[1].Value -ne 'api') { return $m.Value }
    }
    return ''
}

function Start-Tunel($cfg) {
    Stop-Tunel
    $exe = Find-Cloudflared
    $alvo = 'http://{0}:{1}' -f $cfg['UVICORN_HOST'], $cfg['UVICORN_PORT']
    Remove-Item -LiteralPath $TunelLog -Force -ErrorAction SilentlyContinue
    Write-Log "subindo cloudflared tunnel --url $alvo"
    $script:Tunel = Start-Process -FilePath $exe -ArgumentList @('tunnel', '--no-autoupdate', '--url', $alvo) `
        -WindowStyle Hidden -PassThru -RedirectStandardError $TunelLog -RedirectStandardOutput (Join-Path $RunDir 'cloudflared.out.log')
    [IO.File]::WriteAllText($TunelPid, [string]$script:Tunel.Id)
    $limite = (Get-Date).AddSeconds(90)
    while ((Get-Date) -lt $limite) {
        if ($script:Tunel.HasExited) { Write-Log "cloudflared encerrou (codigo $($script:Tunel.ExitCode)) antes de gerar a URL" 'ERRO'; return $false }
        $u = Get-UrlDoLog
        if ($u) {
            $script:Url = $u
            $script:Desde = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
            Write-Log "tunel no ar: $u"
            return $true
        }
        Start-Sleep -Seconds 1
    }
    Write-Log 'cloudflared nao informou a URL em 90s' 'ERRO'
    Stop-Tunel
    return $false
}

function Test-TunelVivo {
    if ($SemTunel) { return $true }
    return ($script:Tunel -and -not $script:Tunel.HasExited)
}

# ----------------------------------------------------------------------------------------------
# Publicacao (clone dedicado, commit unico orfao, push forcado)
# ----------------------------------------------------------------------------------------------
function Get-UrlPush($cfg) {
    if ($RemotoAlternativo) { return $RemotoAlternativo }
    $repo = $cfg['GARRA_PUBLIC_REPO']
    if ($cfg['GARRA_PUBLIC_TOKEN']) { return "https://x-access-token:$($cfg['GARRA_PUBLIC_TOKEN'])@github.com/$repo.git" }
    return "https://github.com/$repo.git"
}

function Initialize-Publico($cfg) {
    $git = Get-Git
    if (-not (Test-Path -LiteralPath (Join-Path $PublicoDir '.git'))) {
        New-Item -ItemType Directory -Path $PublicoDir -Force | Out-Null
        Invoke-Exe $git @('init', '-q', $PublicoDir) -Silencioso | Out-Null
        # Remoto sem token: o .git/config nunca guarda segredo.
        if ($RemotoAlternativo) { $urlLimpa = $RemotoAlternativo } else { $urlLimpa = "https://github.com/$($cfg['GARRA_PUBLIC_REPO']).git" }
        Invoke-Exe $git @('-C', $PublicoDir, 'remote', 'add', 'origin', $urlLimpa) -Silencioso | Out-Null
        # Recupera o snapshot.enc ja publicado (reinstalacao do PC): fetch raso, falha e tolerada.
        $f = Invoke-Exe $git @('-C', $PublicoDir, 'fetch', '--depth', '1', (Get-UrlPush $cfg), 'snapshot') -Silencioso -TimeoutSeg 120
        if ($f.Codigo -eq 0) {
            $show = Invoke-Exe $git @('-C', $PublicoDir, 'show', 'FETCH_HEAD:snapshot.enc') -Silencioso
            if ($show.Codigo -eq 0) {
                Invoke-Exe $git @('-C', $PublicoDir, 'checkout', 'FETCH_HEAD', '--', 'snapshot.enc') -Silencioso | Out-Null
                Write-Log 'snapshot.enc anterior recuperado do remoto'
            }
        }
        else { Write-Log 'branch snapshot ainda nao existe no remoto (ou sem acesso): primeira publicacao' }
    }
}

function Publish-Estado {
    param($cfg, [bool]$Online, [string]$ArquivoSnapshot = '')
    $git = Get-Git
    Initialize-Publico $cfg
    $agora = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
    $url = $script:Url
    if (-not $url) { $url = '' }
    $apiBase = ''
    if ($url) { $apiBase = $url.TrimEnd('/') + '/api/v1' }
    $obj = [ordered]@{ url = $url; api_base = $apiBase; online = $Online; desde = $script:Desde; heartbeat = $agora }
    $utf8 = New-Object System.Text.UTF8Encoding($false)
    [IO.File]::WriteAllText((Join-Path $PublicoDir 'api.json'), (($obj | ConvertTo-Json -Compress) + "`n"), $utf8)
    if ($ArquivoSnapshot -and (Test-Path -LiteralPath $ArquivoSnapshot)) {
        Copy-Item -LiteralPath $ArquivoSnapshot -Destination (Join-Path $PublicoDir 'snapshot.enc') -Force
    }
    $arquivos = @('api.json')
    if (Test-Path -LiteralPath (Join-Path $PublicoDir 'snapshot.enc')) { $arquivos += 'snapshot.enc' }
    # Index so com os arquivos publicados; o commit nao tem pai (orfao), como checkout --orphan.
    Invoke-Exe $git @('-C', $PublicoDir, 'rm', '-r', '--cached', '-q', '--ignore-unmatch', '.') -Silencioso | Out-Null
    $a = Invoke-Exe $git (@('-C', $PublicoDir, 'add', '--') + $arquivos) -Silencioso
    if ($a.Codigo -ne 0) { Write-Log "git add falhou: $($a.Saida)" 'ERRO'; return $false }
    $t = Invoke-Exe $git @('-C', $PublicoDir, 'write-tree') -Silencioso
    $c = Invoke-Exe $git @('-C', $PublicoDir, '-c', 'user.name=garra-agente', '-c', 'user.email=garra-agente@localhost',
        'commit-tree', $t.Saida.Trim(), '-m', "snapshot $agora") -Silencioso
    if ($c.Codigo -ne 0) { Write-Log "git commit-tree falhou: $($c.Saida)" 'ERRO'; return $false }
    Invoke-Exe $git @('-C', $PublicoDir, 'update-ref', 'refs/heads/snapshot', $c.Saida.Trim()) -Silencioso | Out-Null
    Invoke-Exe $git @('-C', $PublicoDir, 'symbolic-ref', 'HEAD', 'refs/heads/snapshot') -Silencioso | Out-Null
    $p = Invoke-Exe $git @('-C', $PublicoDir, 'push', '--force', (Get-UrlPush $cfg), 'snapshot:snapshot') -Silencioso -TimeoutSeg 180
    if ($p.Codigo -ne 0) {
        Write-Log ("push falhou (codigo {0}): {1}" -f $p.Codigo, $p.Saida) 'WARN'
        return $false
    }
    Write-Log ("publicado: online={0} url={1} arquivos={2}" -f $Online, $url, ($arquivos -join ','))
    return $true
}

# ----------------------------------------------------------------------------------------------
# Snapshot (T81) e backup
# ----------------------------------------------------------------------------------------------
# Retorna: 'mudou' | 'igual' | 'falhou' | 'pulado'
function New-SnapshotLocal($cfg) {
    if ($SnapshotArquivo) { return 'mudou' }
    if ($SemBackend) { return 'pulado' }
    if (-not $cfg['SNAPSHOT_SENHA']) { Write-Log 'SNAPSHOT_SENHA vazia no .env: snapshot.enc nao sera gerado (HT-14)' 'WARN'; return 'pulado' }
    $pyArgs = @('-m', 'app.scripts.gerar_snapshot', '--saida', $SnapLocal)
    # Sem snapshot publicado ainda, gera sempre; depois so se mudou.
    if (Test-Path -LiteralPath (Join-Path $PublicoDir 'snapshot.enc')) { $pyArgs += '--somente-se-mudou' }
    $r = Invoke-Exe $VenvPython $pyArgs -Diretorio $BackendDir -TimeoutSeg 900
    switch ($r.Codigo) {
        0 { return 'mudou' }
        3 { return 'igual' }
        default { Write-Log "gerar_snapshot falhou (codigo $($r.Codigo))" 'WARN'; return 'falhou' }
    }
}

function Invoke-BackupDiario {
    $hoje = (Get-Date).ToString('yyyy-MM-dd')
    $ultimo = ''
    if (Test-Path -LiteralPath $BackupMarca) { $ultimo = ([IO.File]::ReadAllText($BackupMarca)).Trim() }
    if ($ultimo -eq $hoje) { return }
    Write-Log 'backup diario (garra-local.ps1 backup)'
    $r = Invoke-Exe $PsExe @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $GarraLocal, 'backup') -TimeoutSeg 1800
    if ($r.Codigo -eq 0) { [IO.File]::WriteAllText($BackupMarca, $hoje) } else { Write-Log "backup falhou (codigo $($r.Codigo))" 'WARN' }
}

function Publish-ComSnapshot($cfg, [bool]$ForcarSnapshot) {
    $arq = ''
    $estado = 'pulado'
    if ($ForcarSnapshot) {
        $estado = New-SnapshotLocal $cfg
        if ($estado -eq 'mudou') { if ($SnapshotArquivo) { $arq = $SnapshotArquivo } else { $arq = $SnapLocal } }
        elseif ($estado -eq 'igual') { Write-Log 'snapshot inalterado: so heartbeat' }
    }
    return (Publish-Estado $cfg $true $arq)
}

# ----------------------------------------------------------------------------------------------
# Principal
# ----------------------------------------------------------------------------------------------
$mutex = New-Object System.Threading.Mutex($false, 'Local\GarraAgente')
if (-not $mutex.WaitOne(0)) { Write-Host 'Outra instancia do agente ja esta rodando.'; exit 0 }

$codigo = 0
$cfg = $null
try {
    Invoke-RotacaoLog (Join-Path $LogDir 'garra-local.log')
    Write-Log '=== agente iniciado ==='
    $cfg = Get-Config
    Set-AmbienteProcesso $cfg
    if (-not $SemAtualizar) { Update-Codigo; Update-Dependencias }
    if (-not $SemBackend) { if (-not (Start-Backend)) { Write-Log 'backend nao subiu; o laco tenta de novo' 'WARN' } }

    if ($SemTunel) { $script:Url = $UrlFixa; $script:Desde = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ') }
    else {
        $tentativas = 0
        while (-not (Start-Tunel $cfg)) {
            $tentativas++
            if ($UmaVez -or $tentativas -ge 5) { throw 'nao foi possivel subir o tunel' }
            Start-Sleep -Seconds 20
        }
    }
    $okPub = Publish-ComSnapshot $cfg $true
    $ultimoHeartbeat = Get-Date
    $ultimoSnapshot = Get-Date
    $heartbeatMin = [double]$cfg['AGENTE_HEARTBEAT_MIN']
    $snapshotMin = [double]$cfg['AGENTE_SNAPSHOT_MIN']
    $tick = [int]$cfg['AGENTE_TICK_SEG']
    $falhasBackend = 0

    if (-not $UmaVez) {
        Write-Log ("laco: heartbeat {0} min, snapshot {1} min, tick {2}s" -f $heartbeatMin, $snapshotMin, $tick)
        while ($true) {
            Start-Sleep -Seconds $tick
            $precisaPublicar = $false
            if (-not (Test-TunelVivo)) {
                Write-Log 'cloudflared caiu: reiniciando' 'WARN'
                if (Start-Tunel $cfg) { $precisaPublicar = $true }
            }
            if (-not $SemBackend) {
                if (Test-Backend $cfg) { $falhasBackend = 0 }
                else {
                    $falhasBackend++
                    if ($falhasBackend -ge 2) { Write-Log 'backend sem resposta em /health: start de novo' 'WARN'; Start-Backend | Out-Null; $falhasBackend = 0 }
                }
            }
            $agora = Get-Date
            $venceuSnap = (($agora - $ultimoSnapshot).TotalMinutes -ge $snapshotMin)
            $venceuHb = (($agora - $ultimoHeartbeat).TotalMinutes -ge $heartbeatMin)
            if ($precisaPublicar -or $venceuSnap -or $venceuHb) {
                if ($venceuSnap) { $ultimoSnapshot = $agora }
                if (Publish-ComSnapshot $cfg $venceuSnap) { $ultimoHeartbeat = $agora }
                else { $ultimoHeartbeat = $agora.AddMinutes(-$heartbeatMin).AddSeconds($tick * 2) }  # tenta de novo em ~2 ticks
            }
            if (-not $SemBackend) { Invoke-BackupDiario }
        }
    }
}
catch {
    Write-Log ("agente falhou: " + $_.Exception.Message) 'ERRO'
    $codigo = 1
}
finally {
    # Ctrl+C / fim normal: marca offline. Se o processo for morto a forca, o heartbeat envelhece
    # e o front trata como offline (ver Doc).
    try {
        if ($cfg) { Write-Log 'encerrando: publicando online:false'; Publish-Estado $cfg $false | Out-Null }
    } catch { Write-Log ("falha ao publicar offline: " + $_.Exception.Message) 'WARN' }
    Stop-Tunel
    Write-Log '=== agente encerrado ==='
    try { $mutex.ReleaseMutex() } catch { }
}
exit $codigo
