param([string]$Python = "python")
$ErrorActionPreference = "Stop"
$projectRoot = $PSScriptRoot
Push-Location -LiteralPath $projectRoot
try {
    $env:PYTHONUTF8 = "1"
    if (-not (Test-Path -LiteralPath '.venv\Scripts\python.exe')) {
        & $Python -m venv .venv
        if ($LASTEXITCODE -ne 0) { throw "Cannot create Python virtual environment." }
    }
    $projectPython = Join-Path $projectRoot '.venv\Scripts\python.exe'
    & $projectPython -m pip install --upgrade pip
    if ($LASTEXITCODE -ne 0) { throw "pip upgrade failed." }
    if (Test-Path -LiteralPath 'requirements.lock.txt') {
        & $projectPython -m pip install -r requirements.lock.txt
    } else {
        & $projectPython -m pip install -r requirements.txt 'https://github.com/Panniantong/Agent-Reach/releases/latest/download/agent-reach.zip'
        if ($LASTEXITCODE -ne 0) { throw "Dependency installation failed." }
        & $projectPython -m pip install torch==2.9.1 torchvision==0.24.1 --index-url https://download.pytorch.org/whl/cu126
    }
    if ($LASTEXITCODE -ne 0) { throw "Dependency installation failed." }
    & $projectPython -m pip install -e .
    if ($LASTEXITCODE -ne 0) { throw "Project installation failed." }
    & $projectPython -m pip check
    if ($LASTEXITCODE -ne 0) { throw "Dependency compatibility check failed." }
    & $projectPython -c "import tkinter; import torch; print('Tcl/Tk:',tkinter.TclVersion,'PyTorch:',torch.__version__,'CUDA:',torch.cuda.is_available())"
    if ($LASTEXITCODE -ne 0) { throw "Desktop needs Tcl/Tk. Install Python from python.org with Tcl/Tk enabled." }
    & '.\.venv\Scripts\agent-reach.exe' version
    Write-Host 'Ready. Double-click run-desktop.bat to open the Windows application.'
} finally {
    Pop-Location
}
