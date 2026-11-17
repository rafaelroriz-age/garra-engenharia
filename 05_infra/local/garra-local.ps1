<#
.SYNOPSIS
    Runtime local de producao do backend Garra no PC Windows do dono, sem Docker (DEC-57, T79).

.DESCRIPTION
    Subcomandos:
      setup   Baixa o PostgreSQL 16 portatil (zip EDB) para 05_infra/local/bin/pgsql, faz initdb em
              %LOCALAPPDATA%\garra\pgdata (scram-sha-256, porta do .env), cria o banco, cria o venv
              04_backend/.venv-prod com requirements.txt, instala o Pango (MSYS2 portatil) para o
              WeasyPrint e cria/completa o 05_infra/local/.env sem sobrescrever valores existentes.
      start   Sobe o Postgres (se parado), aplica `alembic upgrade head`, roda os seeds idempotentes e
              sobe o uvicorn em segundo plano (PID em 05_infra/local/run/uvicorn.pid).
      stop    Encerra o uvicorn pelo PID e para o Postgres (pg_ctl stop -m fast).
      status  Mostra Postgres, uvicorn e GET /health.
      backup  pg_dump -Fc para 05_infra/local/backups/garra-AAAAMMDD-HHmm.dump, retencao BACKUP_RETENCAO.

    Compativel com Windows PowerShell 5.1. O texto do script e so ASCII de proposito: o PS 5.1 le
    .ps1 sem BOM como ANSI e corromperia acentos. Todos os caminhos derivam de $PSScriptRoot, pois o
    repositorio fica numa pasta com espacos e acentos.

.EXAMPLE
    powershell -NoProfile -ExecutionPolicy Bypass -File .\05_infra\local\garra-local.ps1 setup
    powershell -NoProfile -ExecutionPolicy Bypass -File .\05_infra\local\garra-local.ps1 start
#>
[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [ValidateSet('setup', 'start', 'stop', 'status', 'backup', 'install', 'uninstall', 'agente', 'help')]
    [string]$Comando = 'help',

    # install/uninstall: aceita -Dry ou --dry (imprime o que seria registrado/removido e sai).
    [switch]$Dry,

    # install: registra a tarefa mas nao a inicia agora.
    [switch]$SemIniciar,

    # Sobras da linha de comando (aceita `--dry` e repassa o resto ao agente).
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Resto = @(),

    # setup: nao instala o MSYS2/Pango (PDF fica indisponivel; DOCX continua funcionando).
    [switch]$PularPango,

    # start: nao roda os seeds (so migrations + uvicorn).
    [switch]$PularSeeds
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'   # Invoke-WebRequest fica muito lento com a barra no PS 5.1
[Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12

# ----------------------------------------------------------------------------------------------
# Caminhos (todos relativos ao proprio script)
# ----------------------------------------------------------------------------------------------
$LocalDir   = $PSScriptRoot
$RepoDir    = (Resolve-Path (Join-Path $LocalDir '..\..')).Path
$BackendDir = Join-Path $RepoDir '04_backend'
$BinDir     = Join-Path $LocalDir 'bin'
$PgHome     = Join-Path $BinDir 'pgsql'
$LogDir     = Join-Path $LocalDir 'logs'
$RunDir     = Join-Path $LocalDir 'run'
$BackupDir  = Join-Path $LocalDir 'backups'
$StorageDir = Join-Path $LocalDir 'storage'
$EnvFile    = Join-Path $LocalDir '.env'
$EnvExample = Join-Path $LocalDir '.env.example'
$LogFile    = Join-Path $LogDir 'garra-local.log'
$PidFile    = Join-Path $RunDir 'uvicorn.pid'
$VenvDir    = Join-Path $BackendDir '.venv-prod'
$VenvPython = Join-Path $VenvDir 'Scripts\python.exe'
# Fora do OneDrive (DEC-57 P1): o cluster nao pode ser sincronizado arquivo a arquivo.
$GarraAppData = Join-Path $env:LOCALAPPDATA 'garra'
$PgData     = Join-Path $GarraAppData 'pgdata'
$MsysDir    = Join-Path $GarraAppData 'msys64'
# O PostgreSQL nao inicializa cluster UTF8 se o caminho de instalacao tiver acento (o post-init le
# os .sql de share/ por um caminho em cp1252: "sequencia de bytes invalida 0xc1 0x72" = "Ar" de
# "Area de Trabalho"). Os binarios ficam em 05_infra/local/bin/pgsql, mas sao sempre executados
# por esta juncao com caminho ASCII.
$PgJuncao   = Join-Path $GarraAppData 'pgsql'
$PgBin      = Join-Path $PgJuncao 'bin'

foreach ($d in @($LogDir, $RunDir)) {
    if (-not (Test-Path -LiteralPath $d)) { New-Item -ItemType Directory -Path $d | Out-Null }
}

# ----------------------------------------------------------------------------------------------
# Log
# ----------------------------------------------------------------------------------------------
function Write-Log {
    param([string]$Mensagem, [ValidateSet('INFO', 'WARN', 'ERRO')][string]$Nivel = 'INFO')
    $linha = '{0} [{1}] {2}' -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $Nivel, $Mensagem
    Add-Content -LiteralPath $LogFile -Value $linha -Encoding UTF8
    if ($Nivel -eq 'ERRO') { Write-Host $linha -ForegroundColor Red }
    elseif ($Nivel -eq 'WARN') { Write-Host $linha -ForegroundColor Yellow }
    else { Write-Host $linha }
}

function Stop-ComErro([string]$Mensagem) {
    Write-Log $Mensagem 'ERRO'
    throw $Mensagem
}

# ----------------------------------------------------------------------------------------------
# Execucao de programas nativos com captura de saida (sem 2>&1, que no PS 5.1 vira ErrorRecord)
# ----------------------------------------------------------------------------------------------
function ConvertTo-ArgWindows([string]$Arg) {
    if ($Arg -eq '') { return '""' }
    if ($Arg -notmatch '[\s"]') { return $Arg }
    # Regras de CommandLineToArgvW: barras antes de aspas sao dobradas.
    $s = $Arg -replace '(\\*)"', '$1$1\"'
    $s = $s -replace '(\\+)$', '$1$1'
    return '"' + $s + '"'
}

function Invoke-Nativo {
    param(
        [Parameter(Mandatory)][string]$Exe,
        [string[]]$Argumentos = @(),
        [string]$Diretorio = $RunDir,
        [int]$TimeoutSeg = 1800,
        [switch]$PermitirFalha,
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
    Write-Log ("exec: {0} {1}" -f $nome, (Hide-Segredos $psi.Arguments))
    $p = [Diagnostics.Process]::Start($psi)
    $tOut = $p.StandardOutput.ReadToEndAsync()
    $tErr = $p.StandardError.ReadToEndAsync()
    if (-not $p.WaitForExit($TimeoutSeg * 1000)) {
        try { $p.Kill() } catch { }
        Stop-ComErro ("{0} excedeu {1}s" -f $nome, $TimeoutSeg)
    }
    $p.WaitForExit()
    $saida = ($tOut.Result + $tErr.Result).TrimEnd()
    if ($saida -and -not $Silencioso) {
        foreach ($l in ($saida -split "`r?`n")) { Add-Content -LiteralPath $LogFile -Value ('    | ' + $l) -Encoding UTF8 }
    }
    if ($p.ExitCode -ne 0 -and -not $PermitirFalha) {
        if ($saida) { Write-Host $saida }
        Stop-ComErro ("{0} terminou com codigo {1}" -f $nome, $p.ExitCode)
    }
    return [pscustomobject]@{ Codigo = $p.ExitCode; Saida = $saida }
}

$script:Segredos = @()
function Hide-Segredos([string]$Texto) {
    foreach ($s in $script:Segredos) { if ($s) { $Texto = $Texto.Replace($s, '***') } }
    return $Texto
}

# ----------------------------------------------------------------------------------------------
# .env local
# ----------------------------------------------------------------------------------------------
function Read-EnvLocal {
    $vars = [ordered]@{}
    if (-not (Test-Path -LiteralPath $EnvFile)) { return $vars }
    foreach ($linha in [IO.File]::ReadAllLines($EnvFile)) {
        $t = $linha.Trim()
        if ($t -eq '' -or $t.StartsWith('#')) { continue }
        $i = $t.IndexOf('=')
        if ($i -lt 1) { continue }
        $vars[$t.Substring(0, $i).Trim()] = $t.Substring($i + 1).Trim()
    }
    return $vars
}

function New-Segredo([int]$Bytes) {
    $buf = New-Object byte[] $Bytes
    $rng = [Security.Cryptography.RandomNumberGenerator]::Create()
    $rng.GetBytes($buf)
    $rng.Dispose()
    return (($buf | ForEach-Object { $_.ToString('x2') }) -join '')
}

function Set-EnvSeVazio([string]$Chave, [string]$Valor) {
    # Preenche KEY= vazio ou acrescenta a chave ausente. Nunca troca um valor existente.
    $linhas = New-Object System.Collections.Generic.List[string]
    $linhas.AddRange([string[]][IO.File]::ReadAllLines($EnvFile))
    $achou = $false
    for ($i = 0; $i -lt $linhas.Count; $i++) {
        if ($linhas[$i] -match ('^\s*' + [regex]::Escape($Chave) + '\s*=(.*)$')) {
            $achou = $true
            if ($Matches[1].Trim() -ne '') { return $false }
            $linhas[$i] = "$Chave=$Valor"
            break
        }
    }
    if (-not $achou) { $linhas.Add("$Chave=$Valor") }
    [IO.File]::WriteAllLines($EnvFile, $linhas, (New-Object Text.UTF8Encoding($false)))
    return $true
}

function Initialize-EnvLocal {
    if (-not (Test-Path -LiteralPath $EnvFile)) {
        if (Test-Path -LiteralPath (Join-Path $PgData 'PG_VERSION')) {
            # Gerar senha nova aqui deixaria o cluster existente inacessivel.
            Stop-ComErro ("Ja existe um cluster em $PgData, mas falta o $EnvFile com a senha dele. " +
                "Restaure o .env original (ou mova o pgdata para outro lugar) e rode setup de novo.")
        }
        Copy-Item -LiteralPath $EnvExample -Destination $EnvFile
        Write-Log ".env criado a partir de .env.example"
    }
    else {
        Write-Log ".env ja existe: so chaves vazias/ausentes serao preenchidas"
    }
    # Chaves do .env.example que faltam no .env ganham o valor padrao do exemplo.
    $exemplo = [ordered]@{}
    foreach ($linha in [IO.File]::ReadAllLines($EnvExample)) {
        if ($linha -match '^\s*([A-Z0-9_]+)\s*=(.*)$') { $exemplo[$Matches[1]] = $Matches[2].Trim() }
    }
    $atual = Read-EnvLocal
    foreach ($k in $exemplo.Keys) {
        if (-not $atual.Contains($k)) {
            Set-EnvSeVazio $k $exemplo[$k] | Out-Null
            Write-Log "chave $k acrescentada ao .env com o padrao do exemplo"
        }
    }
    $gerados = [ordered]@{ POSTGRES_PASSWORD = 24; JWT_SECRET_KEY = 48; ADMIN_SENHA = 12 }
    foreach ($k in $gerados.Keys) {
        if (Set-EnvSeVazio $k (New-Segredo $gerados[$k])) { Write-Log "$k gerada (aleatoria)" }
        else { Write-Log "$k ja definida: mantida" }
    }
    $atual = Read-EnvLocal
    if (-not $atual['SNAPSHOT_SENHA']) {
        Write-Log 'SNAPSHOT_SENHA vazia: o dono deve definir a senha da equipe (>= 16 caracteres, HT-14)' 'WARN'
    }
}

function Get-Config {
    if (-not (Test-Path -LiteralPath $EnvFile)) { Stop-ComErro "Falta $EnvFile. Rode primeiro: garra-local.ps1 setup" }
    $cfg = Read-EnvLocal
    $padroes = @{
        POSTGRES_USER = 'garra'; POSTGRES_DB = 'garra_producao'; POSTGRES_HOST = 'localhost'
        POSTGRES_PORT = '5434'; PG_VERSION = '16.16'; UVICORN_HOST = '127.0.0.1'; UVICORN_PORT = '8000'
        BACKUP_RETENCAO = '14'; ENVIRONMENT = 'production'
    }
    foreach ($k in $padroes.Keys) { if (-not $cfg.Contains($k) -or -not $cfg[$k]) { $cfg[$k] = $padroes[$k] } }
    if (-not $cfg['POSTGRES_PASSWORD']) { Stop-ComErro 'POSTGRES_PASSWORD vazia no .env. Rode setup.' }
    if (-not $cfg['STORAGE_LOCAL_DIR']) { $cfg['STORAGE_LOCAL_DIR'] = $StorageDir }
    if (-not $cfg['WEASYPRINT_DLL_DIRECTORIES']) {
        $dll = Find-Pango
        if ($dll) { $cfg['WEASYPRINT_DLL_DIRECTORIES'] = $dll }
    }
    $script:Segredos = @($cfg['POSTGRES_PASSWORD'], $cfg['JWT_SECRET_KEY'], $cfg['ADMIN_SENHA'], $cfg['DEEPSEEK_API_KEY'], $cfg['SNAPSHOT_SENHA'])
    return $cfg
}

function Set-AmbienteProcesso($cfg) {
    # Exporta o .env local para o processo; filhos (alembic, seeds, uvicorn) herdam.
    foreach ($k in $cfg.Keys) { Set-Item -Path ("Env:" + $k) -Value ([string]$cfg[$k]) }
    $env:PYTHONPATH = $BackendDir
    $env:PYTHONUTF8 = '1'
    $env:PYTHONIOENCODING = 'utf-8'
    $env:PGPASSWORD = $cfg['POSTGRES_PASSWORD']
    if (-not (Test-Path -LiteralPath $cfg['STORAGE_LOCAL_DIR'])) {
        New-Item -ItemType Directory -Path $cfg['STORAGE_LOCAL_DIR'] | Out-Null
    }
}

# ----------------------------------------------------------------------------------------------
# PostgreSQL
# ----------------------------------------------------------------------------------------------
function Get-PgExe([string]$Nome) {
    $exe = Join-Path $PgBin ($Nome + '.exe')
    if (-not (Test-Path -LiteralPath $exe)) { Stop-ComErro "Nao achei $exe. Rode setup." }
    return $exe
}

function Test-PgRodando {
    if (-not (Test-Path -LiteralPath (Join-Path $PgData 'PG_VERSION'))) { return $false }
    $r = Invoke-Nativo (Get-PgExe 'pg_ctl') @('status', '-D', $PgData) -PermitirFalha -Silencioso
    return ($r.Codigo -eq 0)
}

function Wait-PgPronto($cfg, [int]$TimeoutSeg = 60) {
    $limite = (Get-Date).AddSeconds($TimeoutSeg)
    while ((Get-Date) -lt $limite) {
        $r = Invoke-Nativo (Get-PgExe 'pg_isready') @('-h', $cfg['POSTGRES_HOST'], '-p', $cfg['POSTGRES_PORT'], '-U', $cfg['POSTGRES_USER']) -PermitirFalha -Silencioso
        if ($r.Codigo -eq 0) { Write-Log "Postgres aceitando conexoes na porta $($cfg['POSTGRES_PORT'])"; return }
        Start-Sleep -Seconds 1
    }
    Stop-ComErro "Postgres nao aceitou conexao em $TimeoutSeg s (ver $LogDir\postgres.log)"
}

function Start-Pg($cfg) {
    if (Test-PgRodando) { Write-Log 'Postgres ja esta no ar'; Wait-PgPronto $cfg; return $false }
    $pgLog = Join-Path $LogDir 'postgres.log'
    # pg_ctl deixa o postmaster vivo herdando handles: sem redirecionar a saida dele para um pipe,
    # senao a leitura ficaria presa ate o Postgres parar. Espera so o pg_ctl (WaitForExit).
    # A porta vem do postgresql.conf gravado no setup.
    $argv = @('start', '-D', $PgData, '-l', $pgLog, '-w', '-t', '60')
    $linha = (($argv | ForEach-Object { ConvertTo-ArgWindows $_ }) -join ' ')
    Write-Log ('exec: pg_ctl ' + $linha)
    $p = Start-Process -FilePath (Get-PgExe 'pg_ctl') -ArgumentList $linha -WorkingDirectory $RunDir -WindowStyle Hidden -PassThru
    $null = $p.Handle   # sem isso o ExitCode do Start-Process pode vir vazio no PS 5.1
    if (-not $p.WaitForExit(90000)) { Stop-ComErro 'pg_ctl start excedeu 90 s' }
    if ($p.ExitCode -ne 0) { Stop-ComErro "pg_ctl start falhou (codigo $($p.ExitCode)); ver $pgLog" }
    Wait-PgPronto $cfg
    return $true
}

function Stop-Pg {
    if (-not (Test-PgRodando)) { Write-Log 'Postgres ja estava parado'; return }
    Invoke-Nativo (Get-PgExe 'pg_ctl') @('stop', '-D', $PgData, '-m', 'fast', '-w', '-t', '60') | Out-Null
    Write-Log 'Postgres parado (pg_ctl stop -m fast)'
}

function Invoke-Psql($cfg, [string]$Sql, [string]$Banco = 'postgres') {
    $r = Invoke-Nativo (Get-PgExe 'psql') @('-h', $cfg['POSTGRES_HOST'], '-p', $cfg['POSTGRES_PORT'], '-U', $cfg['POSTGRES_USER'],
        '-d', $Banco, '-v', 'ON_ERROR_STOP=1', '-tAc', $Sql)
    return $r.Saida.Trim()
}

function Set-PgJuncao {
    if (-not (Test-Path -LiteralPath $GarraAppData)) { New-Item -ItemType Directory -Path $GarraAppData | Out-Null }
    $item = Get-Item -LiteralPath $PgJuncao -ErrorAction SilentlyContinue
    if ($item) {
        $alvoAtual = [string]($item.Target | Select-Object -First 1)
        if ($item.LinkType -eq 'Junction' -and $alvoAtual -eq $PgHome) { return }
        if ($item.LinkType -ne 'Junction') { Stop-ComErro "$PgJuncao existe e nao e juncao; remova-o e rode setup" }
        # Juncao de outro checkout (ex.: repositorio movido): aponta para este.
        [IO.Directory]::Delete($PgJuncao)
        Write-Log "juncao $PgJuncao apontava para $alvoAtual; recriada" 'WARN'
    }
    New-Item -ItemType Junction -Path $PgJuncao -Target $PgHome | Out-Null
    Write-Log "juncao $PgJuncao -> $PgHome"
}

function Install-PgBinarios($cfg) {
    if (Test-Path -LiteralPath (Join-Path $PgHome 'bin\pg_ctl.exe')) {
        Write-Log "PostgreSQL ja presente em ${PgHome}: download pulado"
        Set-PgJuncao
        return
    }
    if (-not (Test-Path -LiteralPath $BinDir)) { New-Item -ItemType Directory -Path $BinDir | Out-Null }
    $versao = $cfg['PG_VERSION']
    $url = "https://get.enterprisedb.com/postgresql/postgresql-$versao-1-windows-x64-binaries.zip"
    $zip = Join-Path $BinDir "postgresql-$versao-1-windows-x64-binaries.zip"
    Write-Log "Baixando $url"
    Invoke-WebRequest -Uri $url -OutFile $zip -UseBasicParsing
    Write-Log ("Download concluido: {0:N1} MB" -f ((Get-Item -LiteralPath $zip).Length / 1MB))
    # O zip ja contem a pasta pgsql/ na raiz. Extrai numa pasta temporaria vazia e so depois move.
    $tmp = Join-Path $BinDir '_extrair'
    if (Test-Path -LiteralPath $tmp) { Remove-Item -LiteralPath $tmp -Recurse -Force }
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    [IO.Compression.ZipFile]::ExtractToDirectory($zip, $tmp)
    $origem = Join-Path $tmp 'pgsql'
    if (-not (Test-Path -LiteralPath (Join-Path $origem 'bin\pg_ctl.exe'))) { Stop-ComErro 'zip da EDB sem pgsql\bin\pg_ctl.exe' }
    Move-Item -LiteralPath $origem -Destination $PgHome
    Remove-Item -LiteralPath $tmp -Recurse -Force
    Remove-Item -LiteralPath $zip -Force
    # pgAdmin e documentacao nao sao usados pelo runtime: ~ metade do tamanho.
    foreach ($sobra in @('pgAdmin 4', 'doc', 'symbols', 'StackBuilder')) {
        $p = Join-Path $PgHome $sobra
        if (Test-Path -LiteralPath $p) { Remove-Item -LiteralPath $p -Recurse -Force }
    }
    Set-PgJuncao
    $v = Invoke-Nativo (Join-Path $PgBin 'postgres.exe') @('--version')
    Write-Log ("PostgreSQL instalado: " + $v.Saida)
}

function Initialize-Cluster($cfg) {
    if (Test-Path -LiteralPath (Join-Path $PgData 'PG_VERSION')) {
        Write-Log "Cluster ja existe em ${PgData}: initdb pulado"
        return
    }
    if (-not (Test-Path -LiteralPath $GarraAppData)) { New-Item -ItemType Directory -Path $GarraAppData | Out-Null }
    $pwFile = Join-Path $RunDir ('pw-' + [guid]::NewGuid().ToString('N') + '.tmp')
    [IO.File]::WriteAllText($pwFile, $cfg['POSTGRES_PASSWORD'], (New-Object Text.UTF8Encoding($false)))
    try {
        # ICU pt-BR: lower()/ILIKE corretos com acentos (com locale C so ASCII seria tratado).
        Invoke-Nativo (Get-PgExe 'initdb') @('-D', $PgData, '-U', $cfg['POSTGRES_USER'], '--pwfile', $pwFile,
            '-A', 'scram-sha-256', '-E', 'UTF8', '--locale-provider=icu', '--icu-locale=pt-BR', '--locale=pt-BR') | Out-Null
    }
    finally {
        Remove-Item -LiteralPath $pwFile -Force -ErrorAction SilentlyContinue
    }
    $conf = Join-Path $PgData 'postgresql.conf'
    $extra = @(
        '',
        '# --- garra-local.ps1 (DEC-57) ---',
        ("port = " + $cfg['POSTGRES_PORT']),
        "listen_addresses = 'localhost'",
        "password_encryption = 'scram-sha-256'",
        "timezone = 'America/Sao_Paulo'"
    )
    Add-Content -LiteralPath $conf -Value $extra -Encoding ASCII
    Write-Log "initdb concluido em $PgData (porta $($cfg['POSTGRES_PORT']), scram-sha-256, ICU pt-BR)"
}

function New-Banco($cfg) {
    $db = $cfg['POSTGRES_DB']
    if ($db -notmatch '^[a-z_][a-z0-9_]*$') { Stop-ComErro "POSTGRES_DB invalido: $db" }
    $existe = Invoke-Psql $cfg "SELECT 1 FROM pg_database WHERE datname = '$db'"
    if ($existe -eq '1') { Write-Log "Banco $db ja existe"; return }
    Invoke-Psql $cfg "CREATE DATABASE $db" | Out-Null
    Write-Log "Banco $db criado"
}

# ----------------------------------------------------------------------------------------------
# Python / venv
# ----------------------------------------------------------------------------------------------
function Find-Python312 {
    $py = Get-Command py.exe -ErrorAction SilentlyContinue
    if ($py) {
        $r = Invoke-Nativo $py.Source @('-3.12', '-c', 'import sys; print(sys.executable)') -PermitirFalha -Silencioso
        if ($r.Codigo -eq 0 -and $r.Saida) { return $r.Saida.Trim() }
    }
    $cand = Join-Path $env:LOCALAPPDATA 'Programs\Python\Python312\python.exe'
    if (Test-Path -LiteralPath $cand) { return $cand }
    $uv = Get-Command uv.exe -ErrorAction SilentlyContinue
    if ($uv) {
        Invoke-Nativo $uv.Source @('python', 'install', '3.12') | Out-Null
        $r = Invoke-Nativo $uv.Source @('python', 'find', '3.12')
        return $r.Saida.Trim()
    }
    Stop-ComErro 'Python 3.12 nao encontrado (py -3.12, %LOCALAPPDATA%\Programs\Python\Python312 ou uv). Instale-o e rode setup de novo.'
}

function Install-Venv {
    if (-not (Test-Path -LiteralPath $VenvPython)) {
        $py = Find-Python312
        Write-Log "Criando venv $VenvDir com $py"
        Invoke-Nativo $py @('-m', 'venv', $VenvDir) | Out-Null
    }
    else {
        Write-Log "venv ja existe: $VenvDir"
    }
    Invoke-Nativo $VenvPython @('-m', 'pip', 'install', '--disable-pip-version-check', '--upgrade', 'pip') | Out-Null
    Invoke-Nativo $VenvPython @('-m', 'pip', 'install', '--disable-pip-version-check', '-r', (Join-Path $BackendDir 'requirements.txt')) -TimeoutSeg 3600 | Out-Null
    $v = Invoke-Nativo $VenvPython @('-c', 'import sys, fastapi, uvicorn, alembic; print(sys.version.split()[0], fastapi.__version__, uvicorn.__version__, alembic.__version__)')
    Write-Log ("venv ok (python, fastapi, uvicorn, alembic): " + $v.Saida)
}

# ----------------------------------------------------------------------------------------------
# Pango para o WeasyPrint (PDF). No Windows o WeasyPrint carrega libpango/libgobject via
# WEASYPRINT_DLL_DIRECTORIES; a imagem Docker do Render (aposentada no T85) usava apt (libpango-1.0-0 etc.).
# ----------------------------------------------------------------------------------------------
function Find-Pango {
    foreach ($d in @((Join-Path $MsysDir 'ucrt64\bin'), 'C:\msys64\ucrt64\bin', 'C:\msys64\mingw64\bin')) {
        if (Test-Path -LiteralPath (Join-Path $d 'libpango-1.0-0.dll')) { return $d }
    }
    return $null
}

function Install-Pango {
    $achado = Find-Pango
    if ($achado) { Write-Log "Pango ja presente em $achado"; return }
    if (-not (Test-Path -LiteralPath (Join-Path $MsysDir 'usr\bin\bash.exe'))) {
        if (-not (Test-Path -LiteralPath $GarraAppData)) { New-Item -ItemType Directory -Path $GarraAppData | Out-Null }
        $sfx = Join-Path $GarraAppData 'msys2-base.sfx.exe'
        $url = 'https://repo.msys2.org/distrib/msys2-x86_64-latest.sfx.exe'
        Write-Log "Baixando MSYS2 portatil (sem instalador, sem admin): $url"
        Invoke-WebRequest -Uri $url -OutFile $sfx -UseBasicParsing
        Invoke-Nativo $sfx @('-y', ('-o' + $GarraAppData + '\')) -Diretorio $GarraAppData | Out-Null
        Remove-Item -LiteralPath $sfx -Force
    }
    $bash = Join-Path $MsysDir 'usr\bin\bash.exe'
    # 1o login inicializa o chaveiro do pacman; -Syu duas vezes conforme a documentacao do MSYS2.
    Invoke-Nativo $bash @('-lc', 'true') -Diretorio $GarraAppData -TimeoutSeg 900 | Out-Null
    Invoke-Nativo $bash @('-lc', 'pacman -Syu --noconfirm') -Diretorio $GarraAppData -TimeoutSeg 1800 -PermitirFalha | Out-Null
    Invoke-Nativo $bash @('-lc', 'pacman -Syu --noconfirm') -Diretorio $GarraAppData -TimeoutSeg 1800 | Out-Null
    Invoke-Nativo $bash @('-lc', 'pacman -S --noconfirm --needed mingw-w64-ucrt-x86_64-pango') -Diretorio $GarraAppData -TimeoutSeg 1800 | Out-Null
    $achado = Find-Pango
    if (-not $achado) { Stop-ComErro 'pacman terminou, mas libpango-1.0-0.dll nao apareceu' }
    Write-Log "Pango instalado em $achado"
}

function Test-WeasyPrint($cfg) {
    if (-not $cfg['WEASYPRINT_DLL_DIRECTORIES']) { Write-Log 'WeasyPrint: sem pasta do Pango; PDF indisponivel (DOCX ok)' 'WARN'; return }
    $r = Invoke-Nativo $VenvPython @('-c', "import weasyprint; weasyprint.HTML(string='<p>ok</p>').write_pdf(); print('weasyprint', weasyprint.__version__, 'gerou PDF')") -PermitirFalha
    if ($r.Codigo -eq 0) { Write-Log ("WeasyPrint ok: " + $r.Saida) }
    else { Write-Log ("WeasyPrint falhou: " + (($r.Saida -split "`r?`n") | Select-Object -Last 1)) 'WARN' }
}

# ----------------------------------------------------------------------------------------------
# Uvicorn
# ----------------------------------------------------------------------------------------------
function Get-UvicornPid {
    if (-not (Test-Path -LiteralPath $PidFile)) { return $null }
    $txt = ([IO.File]::ReadAllText($PidFile)).Trim()
    $id = 0
    if (-not [int]::TryParse($txt, [ref]$id)) { return $null }
    $p = Get-Process -Id $id -ErrorAction SilentlyContinue
    if ($p) { return $id }
    return $null
}

function Get-DonoPorta([int]$Porta) {
    # PID do processo que escuta a porta (ou $null). Get-NetTCPConnection existe no Windows 8+.
    $c = Get-NetTCPConnection -LocalPort $Porta -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($c) { return [int]$c.OwningProcess }
    return $null
}

function Test-PortaDoRuntime([int]$Porta, [int]$PidRaiz) {
    # O python.exe do venv e um lancador: quem escuta a porta e o python filho dele.
    $dono = Get-DonoPorta $Porta
    if (-not $dono) { return $false }
    if ($dono -eq $PidRaiz) { return $true }
    $proc = Get-CimInstance Win32_Process -Filter "ProcessId=$dono" -ErrorAction SilentlyContinue
    return ($proc -and [int]$proc.ParentProcessId -eq $PidRaiz)
}

function Assert-PortaLivre([int]$Porta) {
    $dono = Get-DonoPorta $Porta
    if ($dono) {
        # Ex.: o backend de dev do Docker Desktop publica a 8000. Responder /health por ele seria enganoso.
        Stop-ComErro ("Porta $Porta ja esta em uso por " + (Get-DescricaoProcesso $dono) + ". Libere a porta ou mude UVICORN_PORT no .env.")
    }
}

function Get-DescricaoProcesso([int]$Id) {
    $proc = Get-CimInstance Win32_Process -Filter "ProcessId=$Id" -ErrorAction SilentlyContinue
    if ($proc) { return "PID $Id ($($proc.Name))" }
    return "PID $Id"
}

function Get-Health($cfg) {
    $url = 'http://{0}:{1}/health' -f $cfg['UVICORN_HOST'], $cfg['UVICORN_PORT']
    try {
        $r = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 5
        # A API responde JSON UTF-8 sem charset no Content-Type; o PS 5.1 decodificaria como Latin-1.
        $corpo = [Text.Encoding]::UTF8.GetString($r.RawContentStream.ToArray())
        return [pscustomobject]@{ Ok = $true; Codigo = [int]$r.StatusCode; Corpo = $corpo; Url = $url }
    }
    catch {
        return [pscustomobject]@{ Ok = $false; Codigo = 0; Corpo = $_.Exception.Message; Url = $url }
    }
}

function Start-Uvicorn($cfg) {
    $atual = Get-UvicornPid
    if ($atual) { Write-Log "uvicorn ja esta no ar (PID $atual)"; return }
    $porta = [int]$cfg['UVICORN_PORT']
    Assert-PortaLivre $porta
    $stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
    $out = Join-Path $LogDir "uvicorn-$stamp.out.log"
    $err = Join-Path $LogDir "uvicorn-$stamp.err.log"
    $argv = @('-m', 'uvicorn', 'app.main:app', '--host', $cfg['UVICORN_HOST'], '--port', $cfg['UVICORN_PORT'],
        '--workers', '1', '--proxy-headers', '--forwarded-allow-ips', '127.0.0.1')
    $linha = (($argv | ForEach-Object { ConvertTo-ArgWindows $_ }) -join ' ')
    Write-Log "exec (2o plano): python $linha"
    $p = Start-Process -FilePath $VenvPython -ArgumentList $linha -WorkingDirectory $RunDir -WindowStyle Hidden `
        -RedirectStandardOutput $out -RedirectStandardError $err -PassThru
    $null = $p.Handle
    [IO.File]::WriteAllText($PidFile, [string]$p.Id)
    Write-Log "uvicorn iniciado (PID $($p.Id)); saida em $err"
    $limite = (Get-Date).AddSeconds(90)
    while ((Get-Date) -lt $limite) {
        Start-Sleep -Seconds 2
        if ($p.HasExited) { Stop-ComErro "uvicorn saiu com codigo $($p.ExitCode); ver $err" }
        if (-not (Test-PortaDoRuntime $porta $p.Id)) { continue }
        $h = Get-Health $cfg
        if ($h.Ok) { Write-Log ("GET /health -> {0} {1}" -f $h.Codigo, $h.Corpo); return }
    }
    Stop-ComErro "uvicorn nao respondeu /health em 90 s; ver $err"
}

function Stop-Uvicorn {
    $id = Get-UvicornPid
    if (-not $id) {
        Write-Log 'uvicorn nao estava no ar'
        if (Test-Path -LiteralPath $PidFile) { Remove-Item -LiteralPath $PidFile -Force }
        return
    }
    # O python.exe do venv e um lancador que cria o python real como filho: encerra a arvore.
    # No Windows nao ha SIGTERM para o uvicorn; /T /F e o encerramento disponivel.
    $taskkill = Join-Path $env:SystemRoot 'System32\taskkill.exe'
    Invoke-Nativo $taskkill @('/PID', [string]$id, '/T', '/F') -PermitirFalha | Out-Null
    Remove-Item -LiteralPath $PidFile -Force
    Write-Log "uvicorn encerrado (PID $id e filhos)"
}

# ----------------------------------------------------------------------------------------------
# Seeds e migrations
# ----------------------------------------------------------------------------------------------
function Invoke-Migrations {
    Invoke-Nativo $VenvPython @('-m', 'alembic', '-c', (Join-Path $BackendDir 'alembic.ini'), 'upgrade', 'head') | Out-Null
    $r = Invoke-Nativo $VenvPython @('-m', 'alembic', '-c', (Join-Path $BackendDir 'alembic.ini'), 'current')
    $rev = ($r.Saida -split "`r?`n") | Where-Object { $_ -and $_ -notmatch '^INFO' } | Select-Object -First 1
    Write-Log ("alembic current: " + $rev)
}

function Invoke-Seeds($cfg) {
    # Mesma ordem do CI (.github/workflows/ci.yml): gabarito e auditor; depois o prompt ativo da
    # legenda IA. Os tres sao idempotentes. seed_demo e seed_benchmark_rfo NAO rodam em producao.
    foreach ($m in @('app.scripts.seed_gabarito', 'app.scripts.seed_admin', 'app.scripts.seed_prompt_legenda')) {
        $r = Invoke-Nativo $VenvPython @('-m', $m)
        Write-Log ("{0}: {1}" -f $m, (($r.Saida -split "`r?`n") | Where-Object { $_ } | Select-Object -Last 1))
    }
    # Base do RAG: idempotente (ON CONFLICT DO NOTHING), mas le todos os convertidos; so roda vazia.
    $n = Invoke-Psql $cfg 'SELECT count(*) FROM trechos_conhecimento_ia' $cfg['POSTGRES_DB']
    if ($n -eq '0') {
        $r = Invoke-Nativo $VenvPython @('-m', 'app.scripts.ingerir_conhecimento_ia') -TimeoutSeg 1800
        Write-Log ("ingerir_conhecimento_ia: " + (($r.Saida -split "`r?`n") | Where-Object { $_ } | Select-Object -Last 1))
    }
    else {
        Write-Log "ingerir_conhecimento_ia pulado: trechos_conhecimento_ia ja tem $n linhas"
    }
}

# ----------------------------------------------------------------------------------------------
# Subcomandos
# ----------------------------------------------------------------------------------------------
function Invoke-Setup {
    Write-Log '=== setup ==='
    Initialize-EnvLocal
    $cfg = Get-Config
    Set-AmbienteProcesso $cfg
    Install-PgBinarios $cfg
    Initialize-Cluster $cfg
    $subiu = Start-Pg $cfg
    try { New-Banco $cfg }
    finally { if ($subiu) { Stop-Pg } }
    Install-Venv
    if ($PularPango) { Write-Log 'Pango pulado (-PularPango): PDF ficara indisponivel' 'WARN' }
    else {
        try { Install-Pango }
        catch { Write-Log ("Instalacao do Pango falhou: " + $_.Exception.Message + ". PDF indisponivel; DOCX segue ok.") 'WARN' }
    }
    $cfg = Get-Config
    Set-AmbienteProcesso $cfg
    Test-WeasyPrint $cfg
    Write-Log '=== setup concluido ==='
}

function Invoke-Start {
    Write-Log '=== start ==='
    $cfg = Get-Config
    if (-not (Test-Path -LiteralPath $VenvPython)) { Stop-ComErro "Falta o venv $VenvDir. Rode setup." }
    Set-AmbienteProcesso $cfg
    # Falha cedo, antes de migrations/seeds, se a porta do uvicorn estiver com outro processo.
    if (-not (Get-UvicornPid)) { Assert-PortaLivre ([int]$cfg['UVICORN_PORT']) }
    Start-Pg $cfg | Out-Null
    Invoke-Migrations
    if ($PularSeeds) { Write-Log 'seeds pulados (-PularSeeds)' } else { Invoke-Seeds $cfg }
    Start-Uvicorn $cfg
    Write-Log '=== start concluido ==='
}

function Invoke-Stop {
    Write-Log '=== stop ==='
    Stop-Uvicorn
    Stop-Pg
    Write-Log '=== stop concluido ==='
}

function Invoke-Status {
    $cfg = Get-Config
    $pg = Test-PgRodando
    $uv = Get-UvicornPid
    $porta = [int]$cfg['UVICORN_PORT']
    $h = Get-Health $cfg
    $saude = 'sem resposta'
    if ($h.Ok) {
        if ($uv -and (Test-PortaDoRuntime $porta $uv)) { $saude = "$($h.Codigo) $($h.Corpo)" }
        else { $saude = "responde, mas a porta $porta e de " + (Get-DescricaoProcesso (Get-DonoPorta $porta)) + " (nao e este runtime)" }
    }
    Write-Log ("status: postgres={0} (porta {1}, dados {2}); uvicorn={3}; GET {4} -> {5}" -f `
        ($(if ($pg) { 'no ar' } else { 'parado' })), $cfg['POSTGRES_PORT'], $PgData, `
        ($(if ($uv) { "no ar (PID $uv)" } else { 'parado' })), $h.Url, $saude)
}

function Invoke-Backup {
    Write-Log '=== backup ==='
    $cfg = Get-Config
    Set-AmbienteProcesso $cfg
    if (-not (Test-PgRodando)) { Stop-ComErro 'Postgres parado: rode start antes do backup' }
    if (-not (Test-Path -LiteralPath $BackupDir)) { New-Item -ItemType Directory -Path $BackupDir | Out-Null }
    $arquivo = Join-Path $BackupDir ('garra-' + (Get-Date -Format 'yyyyMMdd-HHmm') + '.dump')
    $parcial = $arquivo + '.parcial'
    Invoke-Nativo (Get-PgExe 'pg_dump') @('-h', $cfg['POSTGRES_HOST'], '-p', $cfg['POSTGRES_PORT'], '-U', $cfg['POSTGRES_USER'],
        '-d', $cfg['POSTGRES_DB'], '-Fc', '-f', $parcial) | Out-Null
    $tam = (Get-Item -LiteralPath $parcial).Length
    if ($tam -le 0) { Remove-Item -LiteralPath $parcial -Force; Stop-ComErro 'pg_dump gerou arquivo vazio; retencao nao aplicada' }
    # Confere que o dump e legivel antes de aplicar a retencao (nunca apagar o ultimo backup bom).
    $lista = Invoke-Nativo (Get-PgExe 'pg_restore') @('--list', $parcial) -Silencioso
    $itens = @($lista.Saida -split "`r?`n" | Where-Object { $_ -and -not $_.StartsWith(';') }).Count
    Move-Item -LiteralPath $parcial -Destination $arquivo -Force
    Write-Log ("dump ok: {0} ({1:N1} KB, {2} itens no indice)" -f $arquivo, ($tam / 1KB), $itens)
    $reter = [int]$cfg['BACKUP_RETENCAO']
    $antigos = @(Get-ChildItem -LiteralPath $BackupDir -Filter 'garra-*.dump' | Sort-Object Name -Descending | Select-Object -Skip $reter)
    foreach ($a in $antigos) { Remove-Item -LiteralPath $a.FullName -Force; Write-Log "retencao: removido $($a.Name)" }
    Write-Log ("retencao: {0} dump(s) mantidos (limite {1})" -f @(Get-ChildItem -LiteralPath $BackupDir -Filter 'garra-*.dump').Count, $reter)
    Write-Log '=== backup concluido ==='
}

# ----------------------------------------------------------------------------------------------
# install / uninstall / agente (T82, DEC-57)
# ----------------------------------------------------------------------------------------------
$NomeTarefa = 'Garra Local'
$AgenteScript = Join-Path $LocalDir 'garra-agente.ps1'

function Get-ArgumentoAgente {
    $psExe = Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe'
    $arg = '-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File "{0}"' -f $AgenteScript
    return [pscustomobject]@{ Exe = $psExe; Argumentos = $arg }
}

function Invoke-Install {
    $usuario = '{0}\{1}' -f $env:USERDOMAIN, $env:USERNAME
    $a = Get-ArgumentoAgente
    $acao = New-ScheduledTaskAction -Execute $a.Exe -Argument $a.Argumentos -WorkingDirectory $LocalDir
    $gatilho = New-ScheduledTaskTrigger -AtLogOn -User $usuario
    # Reinicio automatico em falha; sem limite de duracao; roda na bateria; sem segunda instancia.
    $config = New-ScheduledTaskSettingsSet -RestartCount 5 -RestartInterval (New-TimeSpan -Minutes 1) `
        -ExecutionTimeLimit ([TimeSpan]::Zero) -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
        -StartWhenAvailable -MultipleInstances IgnoreNew
    # Interactive + Limited: roda como o usuario atual, sem elevacao (nao pede admin para rodar).
    $principal = New-ScheduledTaskPrincipal -UserId $usuario -LogonType Interactive -RunLevel Limited
    $dryRun = $Dry -or ($Resto -contains '--dry')
    if ($dryRun) {
        Write-Host "[dry] Register-ScheduledTask -TaskName '$NomeTarefa' -Force"
        Write-Host "[dry]   Acao      : $($a.Exe) $($a.Argumentos)"
        Write-Host "[dry]   Diretorio : $LocalDir"
        Write-Host "[dry]   Gatilho   : AtLogOn, usuario $usuario"
        Write-Host "[dry]   Execucao  : usuario $usuario, LogonType Interactive, RunLevel Limited (sem admin)"
        Write-Host "[dry]   Falha     : RestartCount 5, RestartInterval 1 min; sem limite de duracao; MultipleInstances IgnoreNew"
        Write-Host "[dry] Start-ScheduledTask -TaskName '$NomeTarefa'  (omitido com -SemIniciar)"
        Write-Host "[dry] Nada foi registrado."
        return
    }
    if (-not (Test-Path -LiteralPath $AgenteScript)) { Stop-ComErro "Falta $AgenteScript" }
    try {
        Register-ScheduledTask -TaskName $NomeTarefa -Action $acao -Trigger $gatilho -Settings $config -Principal $principal `
            -Description 'Garra Local: backend + tunel cloudflared + publicacao do snapshot (DEC-57)' -Force | Out-Null
    }
    catch {
        Stop-ComErro ("Register-ScheduledTask falhou: {0}. Se for 'acesso negado', rode install uma vez num PowerShell 'Como administrador'." -f $_.Exception.Message)
    }
    Write-Log "tarefa agendada '$NomeTarefa' registrada (logon de $usuario)"
    if (-not $SemIniciar) {
        Start-ScheduledTask -TaskName $NomeTarefa
        Write-Log "tarefa '$NomeTarefa' iniciada; acompanhe em $LogDir\garra-agente.log"
    }
}

function Invoke-Uninstall {
    $dryRun = $Dry -or ($Resto -contains '--dry')
    if ($dryRun) {
        Write-Host "[dry] Stop-ScheduledTask -TaskName '$NomeTarefa'"
        Write-Host "[dry] Unregister-ScheduledTask -TaskName '$NomeTarefa' -Confirm:`$false"
        Write-Host "[dry] Nada foi removido."
        return
    }
    $t = Get-ScheduledTask -TaskName $NomeTarefa -ErrorAction SilentlyContinue
    if (-not $t) { Write-Log "tarefa '$NomeTarefa' nao existe; nada a remover"; return }
    Stop-ScheduledTask -TaskName $NomeTarefa -ErrorAction SilentlyContinue
    Unregister-ScheduledTask -TaskName $NomeTarefa -Confirm:$false
    # O cloudflared e filho do agente e pode sobreviver a um Stop forcado.
    $pidArq = Join-Path $RunDir 'cloudflared.pid'
    if (Test-Path -LiteralPath $pidArq) {
        $id = 0
        [int]::TryParse(([IO.File]::ReadAllText($pidArq)).Trim(), [ref]$id) | Out-Null
        $p = if ($id -gt 0) { Get-Process -Id $id -ErrorAction SilentlyContinue } else { $null }
        if ($p -and $p.ProcessName -eq 'cloudflared') { $p.Kill(); Write-Log "cloudflared (PID $id) encerrado" }
        Remove-Item -LiteralPath $pidArq -Force -ErrorAction SilentlyContinue
    }
    Write-Log "tarefa '$NomeTarefa' removida (Postgres/uvicorn seguem no ar; use stop se quiser parar)"
}

function Invoke-Agente {
    # Roda o agente em primeiro plano (depuracao); repassa o resto da linha de comando.
    $extra = @($Resto | Where-Object { $_ -ne '--dry' })
    & (Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe') -NoProfile -ExecutionPolicy Bypass -File $AgenteScript @extra
    if ($LASTEXITCODE -ne 0) { Stop-ComErro "agente terminou com codigo $LASTEXITCODE" }
}

try {
    switch ($Comando) {
        'install'   { Invoke-Install }
        'uninstall' { Invoke-Uninstall }
        'agente'    { Invoke-Agente }
        'setup'  { Invoke-Setup }
        'start'  { Invoke-Start }
        'stop'   { Invoke-Stop }
        'status' { Invoke-Status }
        'backup' { Invoke-Backup }
        default  {
            Write-Host 'Uso: garra-local.ps1 setup|start|stop|status|backup|install|uninstall|agente [-PularPango] [-PularSeeds] [--dry]'
            Write-Host '  install   registra a tarefa agendada "Garra Local" (logon, sem admin) que roda garra-agente.ps1'
            Write-Host '  uninstall remove a tarefa agendada; --dry imprime sem registrar/remover'
            Write-Host '  agente    roda o agente em primeiro plano (depuracao)'
            Write-Host '  setup   PostgreSQL 16 portatil + initdb + banco + venv-prod + Pango + .env (idempotente)'
            Write-Host '  start   Postgres + alembic upgrade head + seeds idempotentes + uvicorn em 2o plano'
            Write-Host '  stop    encerra uvicorn (PID em run/) e pg_ctl stop -m fast'
            Write-Host '  status  Postgres, uvicorn e GET /health'
            Write-Host '  backup  pg_dump -Fc em backups/ com retencao BACKUP_RETENCAO (padrao 14)'
            Write-Host "Log: $LogFile"
        }
    }
}
catch {
    Write-Log ("falhou: " + $_.Exception.Message) 'ERRO'
    exit 1
}
exit 0
