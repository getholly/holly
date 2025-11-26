# Path to your .env file
$envFilePath = ".env"

# Check if .env file exists
if (!(Test-Path $envFilePath)) {
    Write-Error "The .env file was not found at path: $envFilePath"
    exit 1
}

# Read and process each line
Get-Content $envFilePath | ForEach-Object {
    # Skip empty lines and comments
    if ($_ -match '^\s*$' -or $_ -match '^\s*#') {
        return
    }

    # Parse key=value pairs
    if ($_ -match '^\s*([^=]+?)\s*=\s*(.*)$') {
        $key = $matches[1].Trim()
        $value = $matches[2].Trim('"').Trim()

        # Set the environment variable for the current session
        [System.Environment]::SetEnvironmentVariable($key, $value, "Process")

        # Optional: Uncomment to set for current user or system
        # [System.Environment]::SetEnvironmentVariable($key, $value, "User")
        # [System.Environment]::SetEnvironmentVariable($key, $value, "Machine")

        Write-Output "Set $key=$value"
    } else {
        Write-Warning "Skipping invalid line: $_"
    }
}
