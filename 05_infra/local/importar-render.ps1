<#
.SYNOPSIS
  Importa o banco do Render para o PostgreSQL local do PC do dono (DEC-57, T84).

.DESCRIPTION
  Rodar UMA vez, pelo dono, antes de desligar o Render. Windows PowerShell 5.1.
  Passos:
    1. le a External Database URL (parametro -OrigemUrl ou prompt seguro Read-Host -AsSecureString;
       nunca de arquivo, nunca gravada em disco nem no log);
    2. pg_dump -Fc da origem (somente leitura) -> 05_infra/local/backups/render-final-AAAAMMDD-HHmmss.dump;
    3. backup do banco local de destino -> backups/local-antes-import-*.dump (se ele ja tiver tabelas);
    4. pg_restore --clean --if-exists --no-owner no destino (padrao garra_producao);
    5. alembic upgrade head no destino;
    6. conta linhas por tabela nos dois lados, imprime lado a lado e termina com OK ou DIVERGENTE
       (exit 0 / exit 2).

  A conexao com o destino vem de 05_infra/local/.env (POSTGRES_USER/PASSWORD/HOST/PORT), o mesmo do
  garra-local.ps1. O Postgres local precisa estar no ar (garra-local.ps1 start).
  Os binarios (pg_dump, pg_restore, psql) sao os de garra-local.ps1: %LOCALAPPDATA%\garra\pgsql\bin
  (juncao para 05_infra/local/bin/pgsql); se nao existirem, os de 05_infra/local/bin/pgsql/bin.

.PARAMETER OrigemUrl
  postgres://usuario:senha@host:porta/banco?sslmode=require. Sem ele, pede de forma segura.
.PARAMETER DestinoDb
  Banco local de destino (padrao garra_producao). Criado se nao existir.
.PARAMETER Forcar
  Nao pede a confirmacao "SIM" antes de sobrescrever o destino.
.PARAMETER DestinoUrl
  Modo Neon (DEC-58, T88): restaura num Postgres REMOTO (ex.: Neon) em vez do local. Aceita a URL
  postgres://usuario:senha@host:porta/banco?sslmode=require; se o parametro for passado sem valor util
  (ou com -DestinoPrompt) pede de forma segura (Read-Host -AsSecureString). Nunca de arquivo versionado.
  Neste modo o .env local nao e usado, o banco ja deve existir (criado pelo Neon), o host nao pode ter
  `-pooler` (asyncpg/alembic nao funcionam no PgBouncer) e o alembic roda com POSTGRES_SSL conforme o sslmode.
.PARAMETER DestinoPrompt
  Pede a URL de destino de forma segura (sem aparecer no historico do shell). Implica modo Neon.
.PARAMETER EnvLocal
  Caminho alternativo do .env local (padrao 05_infra/local/.env). Usado nos testes.
.PARAMETER Python
  Python com alembic e as dependencias do backend (padrao 04_backend\.venv-prod, depois 04_backend\.venv).
#>
[CmdletBinding()]
param(
    [string]$OrigemUrl,
    [string]$DestinoDb = 'garra_producao',
    [string]$DestinoUrl,
    [switch]$DestinoPrompt,
    [switch]$Forcar,
    [string]$EnvLocal,
    [string]$Python
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2

$LocalDir   = Split-Path -Parent $MyInvocation.MyCommand.Path
$InfraDir   = Split-Path -Parent $LocalDir
$RepoRoot   = Split-Path -Parent $InfraDir
$BackendDir = Join-Path $RepoRoot '04_backend'
$BackupDir  = Join-Path $LocalDir 'backups'
$LogDir     = Join-Path $LocalDir 'logs'
$RunDir     = Join-Path $LocalDir 'run'
if (-not $EnvLocal) { $EnvLocal = Join-Path $LocalDir '.env' }
foreach ($d in @($BackupDir, $LogDir, $RunDir)) {
    if (-not (Test-Path -LiteralPath $d)) { New-Item -ItemType Directory -Path $d | Out-Null }
}
$LogFile = Join-Path $LogDir 'importar-render.log'
$script:Segredos = @()

function Write-Log {
    param([string]$Mensagem, [ValidateSet('INFO', 'WARN', 'ERRO')][string]$Nivel = 'INFO')
    foreach ($s in $script:Segredos) { if ($s) { $Mensagem = $Mensagem.Replace($s, '***') } }
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

function ConvertTo-ArgWindows([string]$Arg) {
    if ($Arg -eq '') { return '""' }
    if ($Arg -notmatch '[\s"]') { return $Arg }
    $s = $Arg -replace '(\\*)"', '$1$1\"'
    $s = $s -replace '(\\+)$', '$1$1'
    return '"' + $s + '"'
}

# Roda um programa nativo com variaveis de ambiente PG* so para ele (a senha nunca vai em argumento).
function Invoke-Nativo {
    param(
        [Parameter(Mandatory)][string]$Exe,
        [string[]]$Argumentos = @(),
        [hashtable]$Ambiente = @{},
        [int]$TimeoutSeg = 3600,
        [switch]$PermitirFalha
    )
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $Exe
    $psi.Arguments = (($Argumentos | ForEach-Object { ConvertTo-ArgWindows $_ }) -join ' ')
    $psi.WorkingDirectory = $RunDir
    $psi.UseShellExecute = $false
    $psi.CreateNoWindow = $true
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.StandardOutputEncoding = [Text.Encoding]::UTF8
    $psi.StandardErrorEncoding = [Text.Encoding]::UTF8
    foreach ($k in $Ambiente.Keys) { $psi.EnvironmentVariables[$k] = [string]$Ambiente[$k] }
    $nome = [IO.Path]::GetFileName($Exe)
    Write-Log ("exec: {0} {1}" -f $nome, $psi.Arguments)
    $p = [Diagnostics.Process]::Start($psi)
    $tOut = $p.StandardOutput.ReadToEndAsync()
    $tErr = $p.StandardError.ReadToEndAsync()
    if (-not $p.WaitForExit($TimeoutSeg * 1000)) {
        try { $p.Kill() } catch { }
        Stop-ComErro ("{0} excedeu {1}s" -f $nome, $TimeoutSeg)
    }
    $p.WaitForExit()
    $saida = ($tOut.Result + $tErr.Result).TrimEnd()
    if ($saida) {
        foreach ($l in ($saida -split "`r?`n")) { Add-Content -LiteralPath $LogFile -Value ('    | ' + $l) -Encoding UTF8 }
    }
    if ($p.ExitCode -ne 0 -and -not $PermitirFalha) {
        if ($saida) { Write-Host $saida }
        Stop-ComErro ("{0} terminou com codigo {1} (detalhes em {2})" -f $nome, $p.ExitCode, $LogFile)
    }
    return [pscustomobject]@{ Codigo = $p.ExitCode; Saida = $saida }
}

function Get-PgExe([string]$Nome) {
    $cands = @(
        (Join-Path $env:LOCALAPPDATA ("garra\pgsql\bin\{0}.exe" -f $Nome)),
        (Join-Path $LocalDir ("bin\pgsql\bin\{0}.exe" -f $Nome))
    )
    foreach ($c in $cands) { if (Test-Path -LiteralPath $c) { return $c } }
    Stop-ComErro "$Nome.exe nao encontrado. Rode 05_infra\local\garra-local.ps1 setup antes."
}

function Read-EnvArquivo([string]$Caminho) {
    if (-not (Test-Path -LiteralPath $Caminho)) { Stop-ComErro "Arquivo .env nao encontrado: $Caminho. Rode garra-local.ps1 setup." }
    $cfg = @{}
    foreach ($l in (Get-Content -LiteralPath $Caminho -Encoding UTF8)) {
        if ($l -match '^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*?)\s*$' -and $l -notmatch '^\s*#') { $cfg[$Matches[1]] = $Matches[2] }
    }
    return $cfg
}

# postgres://user:senha@host:porta/banco?sslmode=require -> hashtable PG* (sem expor a senha).
function ConvertFrom-PgUrl([string]$Url) {
    if ($Url -notmatch '^postgres(?:ql)?://(?<u>[^:@/]*)(?::(?<p>[^@]*))?@(?<h>[^:/?]+)(?::(?<port>\d+))?/(?<d>[^?]+)(?:\?(?<q>.*))?$') {
        Stop-ComErro 'URL de origem invalida. Formato: postgres://usuario:senha@host:porta/banco'
    }
    # Captura tudo de $Matches ANTES de qualquer outro -match (que o sobrescreveria).
    $uUrl = $Matches['u']; $pUrl = [string]$Matches['p']; $hostOrigem = $Matches['h']; $dUrl = $Matches['d']
    $porta = '5432'; if ($Matches['port']) { $porta = $Matches['port'] }
    $qUrl = [string]$Matches['q']
    $dec = { param($t) [Uri]::UnescapeDataString([string]$t) }
    $ssl = $null
    if ($qUrl -match '(?:^|&)sslmode=([a-z-]+)') { $ssl = $Matches[1] }
    if (-not $ssl) { if ($hostOrigem -in @('localhost', '127.0.0.1')) { $ssl = 'prefer' } else { $ssl = 'require' } }
    $senha = & $dec $pUrl
    $script:Segredos += @($senha, $pUrl)
    return @{
        PGHOST = $hostOrigem; PGPORT = $porta; PGUSER = (& $dec $uUrl); PGPASSWORD = $senha
        PGDATABASE = (& $dec $dUrl); PGSSLMODE = $ssl; PGCONNECT_TIMEOUT = '20'
    }
}

function Invoke-Psql([hashtable]$Amb, [string]$Sql) {
    $r = Invoke-Nativo (Get-PgExe 'psql') @('-X', '-A', '-t', '-F', '|', '-v', 'ON_ERROR_STOP=1', '-c', $Sql) -Ambiente $Amb
    return $r.Saida
}

# Tabelas de public (exceto as do proprio PG) -> hashtable nome=linhas. $null se a tabela nao existe.
function Get-Contagens([hashtable]$Amb) {
    $nomes = @((Invoke-Psql $Amb "select tablename from pg_tables where schemaname='public' order by 1") -split "`r?`n" | Where-Object { $_ })
    $res = @{}
    if ($nomes.Count -eq 0) { return $res }
    $partes = foreach ($n in $nomes) {
        $q = '"' + ($n -replace '"', '""') + '"'
        "select '" + ($n -replace "'", "''") + "', count(*) from public." + $q
    }
    foreach ($l in ((Invoke-Psql $Amb ($partes -join ' union all ')) -split "`r?`n")) {
        if ($l -match '^(.+)\|(\d+)$') { $res[$Matches[1]] = [long]$Matches[2] }
    }
    return $res
}

$inicio = Get-Date
Write-Log "=== importar-render: inicio (destino=$DestinoDb) ==="
if ($DestinoDb -notmatch '^[a-z_][a-z0-9_]*$') { Stop-ComErro "-DestinoDb invalido: $DestinoDb (use minusculas, digitos e _)" }

# --- 1. Origem ------------------------------------------------------------------------------------
if (-not $OrigemUrl) {
    $sec = Read-Host -Prompt 'Cole a External Database URL do Render (a digitacao fica oculta)' -AsSecureString
    $bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($sec)
    try { $OrigemUrl = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr) }
    finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr) }
}
if (-not $OrigemUrl) { Stop-ComErro 'Nenhuma URL de origem informada.' }
$amOrigem = ConvertFrom-PgUrl $OrigemUrl.Trim()
$OrigemUrl = $null
Write-Log ("origem: {0}:{1}/{2} (usuario {3}, sslmode {4})" -f $amOrigem.PGHOST, $amOrigem.PGPORT, $amOrigem.PGDATABASE, $amOrigem.PGUSER, $amOrigem.PGSSLMODE)

# --- 2. Destino -----------------------------------------------------------------------------------
$modoRemoto = [bool]($DestinoUrl -or $DestinoPrompt)
$amAlembic = $null
if ($modoRemoto) {
    # Modo Neon: destino remoto informado por URL (nunca gravada em disco nem no log).
    if (-not $DestinoUrl) {
        $sec = Read-Host -Prompt 'Cole a connection string DIRETA do Neon (a digitacao fica oculta)' -AsSecureString
        $bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($sec)
        try { $DestinoUrl = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr) }
        finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr) }
    }
    if (-not $DestinoUrl) { Stop-ComErro 'Nenhuma URL de destino informada.' }
    $amDestino = ConvertFrom-PgUrl $DestinoUrl.Trim()
    $DestinoUrl = $null
    $DestinoDb = $amDestino.PGDATABASE
    $script:Segredos += @($amDestino.PGHOST)
    if ($amDestino.PGHOST -match '-pooler') { Stop-ComErro 'Host de destino com -pooler: use a conexao DIRETA (desligue "Pooled connection" no Neon).' }
    if ($amDestino.PGHOST -eq $amOrigem.PGHOST -and $amDestino.PGPORT -eq $amOrigem.PGPORT -and $amDestino.PGDATABASE -eq $amOrigem.PGDATABASE) {
        Stop-ComErro 'Origem e destino sao o mesmo banco. Abortando.'
    }
    $amDestinoAdmin = $amDestino
    $hostLocal = $amDestino.PGHOST; $portaLocal = $amDestino.PGPORT
    $cfg = @{}
    Write-Log ("destino REMOTO (modo Neon): banco {0}, sslmode {1}" -f $DestinoDb, $amDestino.PGSSLMODE)
    $r = Invoke-Nativo (Get-PgExe 'psql') @('-X', '-A', '-t', '-c', "select 'conectado tls=' || coalesce((select ssl::text from pg_stat_ssl where pid = pg_backend_pid()), 'n/d')") -Ambiente $amDestino -PermitirFalha
    if ($r.Codigo -ne 0) { Stop-ComErro 'Nao foi possivel conectar ao destino (o Neon escala a zero: tente de novo em alguns segundos; confira a URL).' }
    Write-Log ("destino: {0}" -f $r.Saida)
    $existe = '1'
    $temTabelas = ((Invoke-Psql $amDestino "select count(*) from pg_tables where schemaname='public'") -ne '0')
    $sslFlag = 'true'; if ($amDestino.PGSSLMODE -in @('disable', 'allow', 'prefer')) { $sslFlag = 'false' }
    $amAlembicBase = @{
        POSTGRES_USER = $amDestino.PGUSER; POSTGRES_PASSWORD = $amDestino.PGPASSWORD; POSTGRES_DB = $DestinoDb
        POSTGRES_HOST = $amDestino.PGHOST; POSTGRES_PORT = $amDestino.PGPORT; POSTGRES_SSL = $sslFlag
        PYTHONPATH = $BackendDir; PYTHONUTF8 = '1'
    }
} else {
    $cfg = Read-EnvArquivo $EnvLocal
    foreach ($k in @('POSTGRES_USER', 'POSTGRES_PASSWORD')) { if (-not $cfg[$k]) { Stop-ComErro "$k vazio em $EnvLocal" } }
    $script:Segredos += @($cfg['POSTGRES_PASSWORD'])
    $hostLocal = 'localhost'; if ($cfg['POSTGRES_HOST']) { $hostLocal = $cfg['POSTGRES_HOST'] }
    $portaLocal = '5434'; if ($cfg['POSTGRES_PORT']) { $portaLocal = $cfg['POSTGRES_PORT'] }
    if ($hostLocal -notin @('localhost', '127.0.0.1', '::1')) { Stop-ComErro "Destino precisa ser local (POSTGRES_HOST=$hostLocal). Para o Neon use -DestinoUrl." }
    if ($amOrigem.PGHOST -in @('localhost', '127.0.0.1') -and $amOrigem.PGPORT -eq $portaLocal -and $amOrigem.PGDATABASE -eq $DestinoDb) {
        Stop-ComErro 'Origem e destino sao o mesmo banco. Abortando.'
    }
    $amDestinoAdmin = @{ PGHOST = $hostLocal; PGPORT = $portaLocal; PGUSER = $cfg['POSTGRES_USER']; PGPASSWORD = $cfg['POSTGRES_PASSWORD']; PGDATABASE = 'postgres'; PGCONNECT_TIMEOUT = '10' }
    $amDestino = @{} + $amDestinoAdmin; $amDestino['PGDATABASE'] = $DestinoDb
    $amAlembicBase = @{
        POSTGRES_USER = $cfg['POSTGRES_USER']; POSTGRES_PASSWORD = $cfg['POSTGRES_PASSWORD']; POSTGRES_DB = $DestinoDb
        POSTGRES_HOST = $hostLocal; POSTGRES_PORT = $portaLocal; PYTHONPATH = $BackendDir; PYTHONUTF8 = '1'
    }

    $ready = Invoke-Nativo (Get-PgExe 'pg_isready') @('-h', $hostLocal, '-p', $portaLocal) -PermitirFalha
    if ($ready.Codigo -ne 0) { Stop-ComErro "Postgres local nao responde em ${hostLocal}:${portaLocal}. Rode 05_infra\local\garra-local.ps1 start." }

    $existe = Invoke-Psql $amDestinoAdmin "select 1 from pg_database where datname='$DestinoDb'"
    $temTabelas = $false
    if ($existe -eq '1') { $temTabelas = ((Invoke-Psql $amDestino "select count(*) from pg_tables where schemaname='public'") -ne '0') }
}

if (-not $Forcar) {
    Write-Host ''
    if ($modoRemoto) {
        Write-Host ("Vai SOBRESCREVER o banco REMOTO '{0}' (Neon) com os dados da origem." -f $DestinoDb) -ForegroundColor Yellow
    } else {
        Write-Host ("Vai SOBRESCREVER o banco local '{0}' em {1}:{2} com os dados da origem." -f $DestinoDb, $hostLocal, $portaLocal) -ForegroundColor Yellow
    }
    if ($temTabelas) { Write-Host 'O destino ja tem tabelas: um backup dele sera feito antes.' -ForegroundColor Yellow }
    $resp = Read-Host -Prompt 'Digite SIM para continuar'
    if ($resp -ne 'SIM') { Stop-ComErro 'Cancelado pelo usuario.' }
}

# --- 3. pg_dump da origem (somente leitura) ----------------------------------------------------------
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$dumpOrigem = Join-Path $BackupDir "render-final-$stamp.dump"
Write-Log "pg_dump da origem -> $dumpOrigem"
Invoke-Nativo (Get-PgExe 'pg_dump') @('-Fc', '--no-owner', '--no-privileges', '-f', $dumpOrigem) -Ambiente $amOrigem | Out-Null
$tam = (Get-Item -LiteralPath $dumpOrigem).Length
if ($tam -lt 1024) { Stop-ComErro "Dump suspeito de tao pequeno ($tam bytes)." }
Write-Log ("dump da origem ok: {0:N1} MB" -f ($tam / 1MB))
$null = Invoke-Nativo (Get-PgExe 'pg_restore') @('--list', $dumpOrigem)

# --- 4. Backup do local e restauracao ------------------------------------------------------------------
if ($existe -ne '1' -and -not $modoRemoto) {
    Write-Log "banco $DestinoDb nao existe: criando"
    Invoke-Psql $amDestinoAdmin "create database $DestinoDb encoding 'UTF8'" | Out-Null
} elseif ($temTabelas) {
    $dumpLocal = Join-Path $BackupDir "local-antes-import-$DestinoDb-$stamp.dump"
    Write-Log "backup do destino -> $dumpLocal"
    Invoke-Nativo (Get-PgExe 'pg_dump') @('-Fc', '--no-owner', '-f', $dumpLocal) -Ambiente $amDestino | Out-Null
}

if ($temTabelas) {
    # O destino pode ja estar numa revisao MAIS NOVA que o dump (ex.: garra-local.ps1 start no Neon aplicou o
    # alembic antes da importacao): o --clean sozinho falha em dependencias que o dump nao conhece (FK de tabelas
    # novas). O backup acima ja foi feito e o usuario confirmou: zera o schema public antes de restaurar.
    Write-Log "destino com tabelas: recriando o schema public (backup ja feito)"
    Invoke-Psql $amDestino 'drop schema public cascade; create schema public;' | Out-Null
}
Write-Log "pg_restore --clean --if-exists --no-owner em $DestinoDb"
Invoke-Nativo (Get-PgExe 'pg_restore') @('--clean', '--if-exists', '--no-owner', '--no-privileges', '--exit-on-error', '-d', $DestinoDb, $dumpOrigem) -Ambiente $amDestino | Out-Null

# --- 5. alembic upgrade head -----------------------------------------------------------------------------
if (-not $Python) {
    foreach ($c in @((Join-Path $BackendDir '.venv-prod\Scripts\python.exe'), (Join-Path $BackendDir '.venv\Scripts\python.exe'))) {
        if (Test-Path -LiteralPath $c) { $Python = $c; break }
    }
}
if (-not $Python -or -not (Test-Path -LiteralPath $Python)) { Stop-ComErro 'Python do backend nao encontrado (04_backend\.venv-prod). Rode garra-local.ps1 setup ou passe -Python.' }
$amAlembic = $amAlembicBase
Write-Log 'alembic upgrade head'
Invoke-Nativo $Python @('-m', 'alembic', '-c', (Join-Path $BackendDir 'alembic.ini'), 'upgrade', 'head') -Ambiente $amAlembic | Out-Null

# --- 6. Contagens lado a lado --------------------------------------------------------------------------------
$cOrigem = Get-Contagens $amOrigem
$cDestino = Get-Contagens $amDestino
$tabelas = @($cOrigem.Keys) + @($cDestino.Keys) | Sort-Object -Unique
$diverg = 0
$linhas = foreach ($t in $tabelas) {
    $o = $null; if ($cOrigem.ContainsKey($t)) { $o = $cOrigem[$t] }
    $d = $null; if ($cDestino.ContainsKey($t)) { $d = $cDestino[$t] }
    # Tabela criada so pelo alembic (nao existia na origem) e vazia no destino nao e divergencia.
    $ok = ($null -ne $o -and $null -ne $d -and $o -eq $d) -or ($null -eq $o -and $d -eq 0)
    if (-not $ok) { $diverg++ }
    $so = '-'; if ($null -ne $o) { $so = [string]$o }
    $sd = '-'; if ($null -ne $d) { $sd = [string]$d }
    $st = 'ok'; if (-not $ok) { $st = 'DIVERGE' }
    [pscustomobject]@{ Tabela = $t; Origem = $so; Destino = $sd; Status = $st }
}
Write-Host ''
$tabela = ($linhas | Format-Table -AutoSize | Out-String).TrimEnd()
Write-Host $tabela
Add-Content -LiteralPath $LogFile -Value $tabela -Encoding UTF8
Write-Host ''
$seg = [int]((Get-Date) - $inicio).TotalSeconds
if ($diverg -eq 0) {
    Write-Log ("RESULTADO: OK ({0} tabelas conferidas, {1}s). Dump da origem guardado em {2}" -f @($tabelas).Count, $seg, $dumpOrigem)
    Write-Host 'OK' -ForegroundColor Green
    exit 0
}
Write-Log ("RESULTADO: DIVERGENTE ({0} tabela(s) com contagem diferente, {1}s)" -f $diverg, $seg) 'ERRO'
Write-Host 'DIVERGENTE' -ForegroundColor Red
exit 2
