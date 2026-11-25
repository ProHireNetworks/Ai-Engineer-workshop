# TripMate AI - Agent Benchmark Evaluation Runner Script
$ErrorActionPreference = "Stop"
Write-Host "Starting TripMate AI Multi-Agent Benchmark Evaluation (105 Test Cases)..." -ForegroundColor Cyan

$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = "1"
$env:PYTHONPATH = "backend"
$pythonExe = ".\.venv\Scripts\python.exe"

if (!(Test-Path $pythonExe)) {
    Write-Error "Virtual environment not found at $pythonExe"
}

# Run the benchmark runner script
& $pythonExe -c "
import asyncio
from app.evaluation.runner import EvaluationRunner

async def main():
    runner = EvaluationRunner()
    summary = await runner.run_benchmark(output_report=True)
    print(f'=== EVALUATION COMPLETE ===')
    print(f'Total Cases: {summary.total_cases}')
    print(f'Passed Cases: {summary.passed_cases}')
    print(f'Failed Cases: {summary.failed_cases}')
    print(f'Pass Rate: {summary.pass_rate_pct}%')
    print(f'Avg Latency: {summary.avg_latency_ms} ms')
    print(f'Total Tokens: {summary.total_tokens}')
    print(f'Estimated Cost: ${summary.total_cost_usd:.4f} USD')

asyncio.run(main())
"

if ($LASTEXITCODE -ne 0) {
    Write-Error "Benchmark execution failed with exit code $LASTEXITCODE"
} else {
    Write-Host "Benchmark evaluation reports saved to benchmark/evaluation_report.json and benchmark/EVALUATION_REPORT.md" -ForegroundColor Green
}
