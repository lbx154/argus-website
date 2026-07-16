$ErrorActionPreference = "Stop"

$RegistryUrl = if ($env:ARGUS_NPM_REGISTRY) { $env:ARGUS_NPM_REGISTRY.TrimEnd("/") } else { "https://registry.npmjs.org" }
$InstallBin = if ($env:ARGUS_INSTALL_BIN) { $env:ARGUS_INSTALL_BIN } else { Join-Path $env:LOCALAPPDATA "Programs\Argus\bin" }
$PackagePath = "@argusevolve%2fargus"

if (-not [Environment]::Is64BitOperatingSystem) {
  throw "Argus currently supports Windows x64 only."
}
if (-not (Get-Command tar.exe -ErrorAction SilentlyContinue)) {
  throw "Windows tar.exe is required."
}

$Tags = Invoke-RestMethod "$RegistryUrl/-/package/$PackagePath/dist-tags"
$BetaVersion = $Tags.beta
if (-not $BetaVersion) {
  throw "The Argus npm beta tag is unavailable."
}

$PlatformVersion = "$BetaVersion-win32-x64"
$VersionMetadata = Invoke-RestMethod "$RegistryUrl/$PackagePath/$PlatformVersion"
$TarballUrl = $VersionMetadata.dist.tarball
if (-not $TarballUrl) {
  throw "Could not resolve the Windows binary tarball."
}

$TempDir = Join-Path ([IO.Path]::GetTempPath()) ("argus-install-" + [Guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Force -Path $TempDir | Out-Null

try {
  $Archive = Join-Path $TempDir "argus.tgz"
  Invoke-WebRequest -UseBasicParsing $TarballUrl -OutFile $Archive
  & tar.exe -xzf $Archive -C $TempDir package/bin/argus-core.exe package/bin/argus-core.exe.sha256
  if ($LASTEXITCODE -ne 0) { throw "Failed to extract the Argus archive." }

  $SourceBinary = Join-Path $TempDir "package\bin\argus-core.exe"
  $DigestFile = Join-Path $TempDir "package\bin\argus-core.exe.sha256"
  $ExpectedDigest = ((Get-Content $DigestFile -Raw).Trim() -split "\s+")[0].ToLowerInvariant()
  $ActualDigest = (Get-FileHash -Algorithm SHA256 $SourceBinary).Hash.ToLowerInvariant()
  if ($ExpectedDigest -ne $ActualDigest) {
    throw "Argus binary SHA-256 verification failed."
  }

  New-Item -ItemType Directory -Force -Path $InstallBin | Out-Null
  Copy-Item -Force $SourceBinary (Join-Path $InstallBin "argus.exe")
  @'
@echo off
set ARGUS_BINARY_MODE=cli
"%~dp0argus.exe" %*
'@ | Set-Content -Encoding ASCII (Join-Path $InstallBin "argus-skill.cmd")

  $UserPath = [Environment]::GetEnvironmentVariable("Path", "User")
  $PathEntries = @($UserPath -split ";" | Where-Object { $_ })
  if ($PathEntries -notcontains $InstallBin) {
    $UpdatedPath = (($PathEntries + $InstallBin) -join ";")
    [Environment]::SetEnvironmentVariable("Path", $UpdatedPath, "User")
  }
  if (($env:Path -split ";") -notcontains $InstallBin) {
    $env:Path = "$InstallBin;$env:Path"
  }

  Write-Host "Argus $BetaVersion installed to $(Join-Path $InstallBin 'argus.exe')"
  Write-Host "Open a new terminal and run: argus --setup"
}
finally {
  Remove-Item -Recurse -Force $TempDir -ErrorAction SilentlyContinue
}
