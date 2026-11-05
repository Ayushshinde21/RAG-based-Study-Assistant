[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$ProjectId,
    [Parameter(Mandatory = $true)][string]$ArtifactRepository,
    [Parameter(Mandatory = $true)][string]$SqlInstanceConnectionName,
    [Parameter(Mandatory = $true)][string]$DbUser,
    [Parameter(Mandatory = $true)][string]$DbName,
    [Parameter(Mandatory = $true)][string]$AdminEmail,
    [string]$Region = "asia-south1",
    [string]$ServiceName = "campus-study-desk",
    [string]$DbPasswordSecret = "study-assistant-db-password",
    [string]$GroqApiKeySecret = "study-assistant-groq-api-key",
    [string]$AdminPasswordSecret = "study-assistant-admin-password",
    [string]$ServiceAccount = "",
    [string]$Memory = "8Gi",
    [string]$Cpu = "4"
)

$ErrorActionPreference = "Stop"

function Invoke-Gcloud {
    param([string[]]$Arguments)
    & gcloud @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "gcloud command failed with exit code $LASTEXITCODE."
    }
}

if (-not (Get-Command gcloud -ErrorAction SilentlyContinue)) {
    throw "Google Cloud CLI (gcloud) is not installed or not on PATH."
}

if ($AdminEmail -notmatch '^[^\s@]+@[^\s@]+\.[^\s@]+$') {
    throw "AdminEmail must be a valid email address."
}

Write-Host "Selecting Google Cloud project..."
Invoke-Gcloud @("config", "set", "project", $ProjectId)

Write-Host "Enabling required Google Cloud APIs..."
Invoke-Gcloud @(
    "services", "enable",
    "run.googleapis.com",
    "cloudbuild.googleapis.com",
    "artifactregistry.googleapis.com",
    "sqladmin.googleapis.com",
    "secretmanager.googleapis.com",
    "--project", $ProjectId
)

Write-Host "Checking Artifact Registry repository..."
& gcloud artifacts repositories describe $ArtifactRepository --location $Region --project $ProjectId 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
    Invoke-Gcloud @(
        "artifacts", "repositories", "create", $ArtifactRepository,
        "--repository-format", "docker",
        "--location", $Region,
        "--description", "Campus Study Desk container images",
        "--project", $ProjectId
    )
}

$imageTag = Get-Date -Format "yyyyMMdd-HHmmss"
$imageUri = "$Region-docker.pkg.dev/$ProjectId/$ArtifactRepository/$ServiceName`:$imageTag"

Write-Host "Building container image..."
Invoke-Gcloud @("builds", "submit", "--tag", $imageUri, "--timeout", "3600s", "--project", $ProjectId, ".")

$envVars = @(
    "APP_ENV=production",
    "SESSION_COOKIE_SECURE=1",
    "DATABASE_BACKEND=postgres",
    "VECTOR_STORE_BACKEND=postgres",
    "DB_USER=$DbUser",
    "DB_NAME=$DbName",
    "INSTANCE_UNIX_SOCKET=/cloudsql/$SqlInstanceConnectionName",
    "DB_SSLMODE=disable",
    "VECTOR_DIMENSIONS=384",
    "EMBEDDING_MODEL=all-MiniLM-L6-v2",
    "EMBEDDING_DEVICE=cpu",
    "YOUTUBE_ENABLED=0",
    "MAX_UPLOAD_MB=30",
    "WARMUP=1",
    "ADMIN_EMAIL=$AdminEmail"
) -join ","

$secrets = @(
    "DB_PASSWORD=$DbPasswordSecret`:latest",
    "GROQ_API_KEY=$GroqApiKeySecret`:latest",
    "ADMIN_PASSWORD=$AdminPasswordSecret`:latest"
) -join ","

$deployArgs = @(
    "run", "deploy", $ServiceName,
    "--image", $imageUri,
    "--region", $Region,
    "--project", $ProjectId,
    "--platform", "managed",
    "--allow-unauthenticated",
    "--add-cloudsql-instances", $SqlInstanceConnectionName,
    "--set-env-vars", $envVars,
    "--set-secrets", $secrets,
    "--memory", $Memory,
    "--cpu", $Cpu,
    "--timeout", "3600",
    "--concurrency", "1",
    "--min", "1",
    "--max", "1"
)

if ($ServiceAccount) {
    $deployArgs += @("--service-account", $ServiceAccount)
}

Write-Host "Deploying a single-instance staging revision..."
Invoke-Gcloud $deployArgs

Write-Host "Deployment command completed. Check the Cloud Run URL and /api/health before migrating production data."
