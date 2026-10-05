param(
    [switch]$CheckOnly,
    [int]$Port = 8000
)

$ErrorActionPreference = 'Stop'
$python = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $python)) {
    $python = (Get-Command python -ErrorAction Stop).Source
}

$databaseHostCode = 'import os,sys; from dotenv import dotenv_values; from urllib.parse import urlparse; print(urlparse(os.environ.get("DATABASE_URL") or dotenv_values(sys.argv[1]).get("DATABASE_URL", "")).hostname or "")'
$databaseHost = & $python -c $databaseHostCode (Join-Path $PSScriptRoot '.env')
if (-not $databaseHost) {
    throw 'DATABASE_URL is missing. Set it in the ignored local .env or in the current environment.'
}

$databaseAddress = $null
try {
    $databaseAddress = [System.Net.Dns]::GetHostAddresses($databaseHost) |
        Where-Object AddressFamily -eq InterNetwork |
        Select-Object -First 1 -ExpandProperty IPAddressToString
} catch {
    # Some home router DNS resolvers cannot resolve Neon branch hostnames.
}

if (-not $databaseAddress) {
    try {
        $databaseAddress = Resolve-DnsName -Name $databaseHost -Server '1.1.1.1' -Type A -ErrorAction Stop |
            Where-Object IPAddress |
            Select-Object -First 1 -ExpandProperty IPAddress
    } catch {
        throw 'Could not resolve the Neon database host using system DNS or the Cloudflare DNS fallback.'
    }
}

if (-not $databaseAddress) {
    throw 'The Neon database host did not return an IPv4 address.'
}

if ($CheckOnly) {
    Write-Output 'Neon database host DNS check passed.'
    exit 0
}

# Keep the hostname in DATABASE_URL for TLS hostname validation; PGHOSTADDR
# only supplies the resolved network address to libpq for this process.
$previousHostAddress = $env:PGHOSTADDR
$env:PGHOSTADDR = $databaseAddress
try {
    & $python (Join-Path $PSScriptRoot 'manage.py') runserver "127.0.0.1:$Port"
    exit $LASTEXITCODE
} finally {
    if ($null -eq $previousHostAddress) {
        Remove-Item Env:PGHOSTADDR -ErrorAction SilentlyContinue
    } else {
        $env:PGHOSTADDR = $previousHostAddress
    }
}
