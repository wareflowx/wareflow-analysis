# Run Command Implementation Plan

## Overview

This document provides a comprehensive analysis of implementing the `run` command for the Wareflow Analysis CLI. This command serves as the **pipeline orchestrator**, executing the complete data workflow in a single operation.

## Current State

**Phase 1 (Completed)**: CLI infrastructure and `init` command ✅
**Phase 2 (In Progress)**: Data processing - `import` command 🔄
**Phase 3 (Planned)**: Data analysis - `analyze` command 📋
**Phase 4 (Planned)**: Report generation - `export` command 📋
**Phase 5 (Next)**: Pipeline orchestration - `run` command ❌

The `run` command is the **user-friendly interface** of the system:
- ✅ Executes complete pipeline in one command
- ✅ Ideal for automation and scheduling
- ✅ Perfect for non-technical users
- ✅ Reduces operational complexity to single command

## Why the `run` Command Last?

According to the development flow:
```
init → import → analyze → export → run (orchestration)
```

The `run` command must be implemented last because:
1. It depends on all other commands being complete
2. It orchestrates the complete pipeline
3. It's essentially "glue code" that calls other commands
4. Cannot be tested until all dependencies exist

---

## Command Specifications

### Current Implementation

**File**: `src/wareflow_analysis/cli.py:54-56`

```python
@app.command()
def run() -> None:
    """Run full pipeline (import -> analyze -> export)."""
    typer.echo("Run command not implemented yet")
```

**Status**: Skeleton without implementation

### Command Responsibilities

The `run` command must:

#### 1. Pipeline Orchestration
- **Execute commands in order**: import → analyze → export
- **Handle dependencies**: Ensure each step succeeds
- **Manage errors gracefully**: Decide whether to continue or stop

#### 2. Progress Reporting
- **Display clear progress**: Show which step is running
- **Provide feedback**: Success/failure for each step
- **Generate summary**: Overall pipeline statistics

#### 3. Error Management
- **Critical failures**: Stop if import/export fail
- **Non-critical failures**: Continue if analyze fails (can export raw data)
- **Clear messaging**: Explain what happened and what to do

#### 4. Flexibility
- **Skip steps**: Allow bypassing individual commands
- **Dry-run mode**: Validate without executing
- **Verbose output**: Detailed logging for debugging

---

## Strategic Approach: Lightweight Orchestrator

### Design Philosophy

The `run` command should be **simple and focused**:

| Concern | Approach |
|---------|----------|
| **Code reuse** | Call existing command modules directly |
| **Error handling** | Smart continuation logic |
| **User experience** | Clear progress and summary |
| **Complexity** | Minimal - mostly orchestration |

**Key Insight**: `run` is NOT a rewrite of other commands. It's a coordinator that calls the existing modules.

---

## Technical Architecture

### File Structure

```
src/wareflow_analysis/
├── cli.py                      # ✅ Exists (to modify)
├── init.py                     # ✅ Exists
├── import/                     # 🔄 From import phase
│   └── importer.py             # Has run_import() function
├── analyze/                    # 📋 From analyze phase
│   └── analyzer.py             # Has DatabaseAnalyzer class
├── export/                     # 📋 From export phase
│   └── exporter.py             # Has ReportExporter class
└── run/                        # 🆕 New module (minimal)
    ├── __init__.py
    ├── orchestrator.py         # Pipeline coordination
    └── reporters.py            # Summary and progress reporting
```

### Module Descriptions

**A. Module `orchestrator.py` - Pipeline Coordination**

```python
# orchestrator.py

from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple
import sys

class PipelineOrchestrator:
    """Orchestrates the complete Wareflow pipeline."""

    def __init__(self, project_dir: Path, verbose: bool = False):
        self.project_dir = project_dir
        self.verbose = verbose
        self.results = {}
        self.start_time = None
        self.end_time = None

    def run(self,
             skip_import: bool = False,
             skip_analyze: bool = False,
             skip_export: bool = False,
             dry_run: bool = False) -> Dict:
        """Execute the complete pipeline."""

        self.start_time = datetime.now()

        if dry_run:
            return self._dry_run()

        # Step 1: Import
        if not skip_import:
            import_result = self._run_import()
            self.results['import'] = import_result

            if import_result['status'] == 'failed':
                # Critical failure - cannot continue
                self.end_time = datetime.now()
                self.results['analyze'] = {'status': 'skipped', 'reason': 'import failed'}
                self.results['export'] = {'status': 'skipped', 'reason': 'import failed'}
                return self._generate_summary()
        else:
            self.results['import'] = {'status': 'skipped'}

        # Step 2: Analyze
        if not skip_analyze:
            analyze_result = self._run_analyze()
            self.results['analyze'] = analyze_result
        else:
            self.results['analyze'] = {'status': 'skipped'}

        # Step 3: Export
        if not skip_export:
            export_result = self._run_export()
            self.results['export'] = export_result
        else:
            self.results['export'] = {'status': 'skipped'}

        self.end_time = datetime.now()
        return self._generate_summary()

    def _run_import(self) -> Dict:
        """Execute the import step."""
        if self.verbose:
            print("[DEBUG] Starting import step...")

        try:
            from import.importer import run_import

            success, message = run_import(self.project_dir)

            if success:
                return {
                    'status': 'success',
                    'message': message,
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return {
                    'status': 'failed',
                    'error': message,
                    'timestamp': datetime.now().isoformat()
                }
        except Exception as e:
            return {
                'status': 'failed',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    def _run_analyze(self) -> Dict:
        """Execute the analyze step."""
        if self.verbose:
            print("[DEBUG] Starting analyze step...")

        try:
            from analyze.analyzer import DatabaseAnalyzer

            db_path = self.project_dir / "warehouse.db"
            analyzer = DatabaseAnalyzer(db_path)

            # Connect and verify
            connected, msg = analyzer.connect()
            if not connected:
                return {
                    'status': 'failed',
                    'error': msg,
                    'timestamp': datetime.now().isoformat()
                }

            # Run analyses
            analyze_results = analyzer.run_all_analyses()

            analyzer.close()

            return {
                'status': 'success',
                'results': analyze_results,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            # Non-critical failure - can export raw data
            return {
                'status': 'failed',
                'error': str(e),
                'recoverable': True,
                'timestamp': datetime.now().isoformat()
            }

    def _run_export(self) -> Dict:
        """Execute the export step."""
        if self.verbose:
            print("[DEBUG] Starting export step...")

        try:
            from export.exporter import ReportExporter

            db_path = self.project_dir / "warehouse.db"
            output_dir = self.project_dir / "output"

            exporter = ReportExporter(db_path, output_dir)

            # Connect
            connected, msg = exporter.connect()
            if not connected:
                return {
                    'status': 'failed',
                    'error': msg,
                    'timestamp': datetime.now().isoformat()
                }

            # Choose export mode
            if (self.results.get('analyze', {}).get('status') == 'success'):
                export_results = exporter.export_analysis_report()
                mode = 'analysis'
            else:
                export_results = exporter.export_raw_data()
                mode = 'raw'

            # Save
            output_info = exporter.save()
            exporter.close()

            return {
                'status': 'success',
                'mode': mode,
                'file': str(output_info['path']),
                'size_mb': output_info['size_mb'],
                'sheets': output_info['sheets'],
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'status': 'failed',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    def _dry_run(self) -> Dict:
        """Validate pipeline without executing."""
        validations = []

        # Check config
        config_path = self.project_dir / "config.yaml"
        validations.append(("config.yaml", config_path.exists()))

        # Check database
        db_path = self.project_dir / "warehouse.db"
        validations.append(("warehouse.db", db_path.exists()))

        # Check output directory
        output_dir = self.project_dir / "output"
        validations.append(("output/ directory", output_dir.exists()))

        # Check Excel files
        data_dir = self.project_dir / "data"
        if data_dir.exists():
            excel_files = list(data_dir.glob("*.xlsx"))
            validations.append(("Excel files", len(excel_files) > 0))
        else:
            validations.append(("Excel files", False))

        return {
            'dry_run': True,
            'validations': validations,
            'ready': all(v[1] for v in validations)
        }

    def _generate_summary(self) -> Dict:
        """Generate pipeline execution summary."""
        duration = (self.end_time - self.start_time).total_seconds()

        summary = {
            'pipeline': 'wareflow',
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat(),
            'duration_seconds': round(duration, 2),
            'steps': self.results,
            'overall_status': self._determine_overall_status()
        }

        return summary

    def _determine_overall_status(self) -> str:
        """Determine overall pipeline status."""
        # Import is critical
        if self.results['import']['status'] == 'failed':
            return 'failed'

        # Export is critical
        if self.results['export']['status'] == 'failed':
            return 'failed'

        # Analyze is optional
        if self.results.get('analyze', {}).get('status') == 'failed':
            return 'partial'

        # All succeeded
        return 'success'
```

**B. Module `reporters.py` - Progress and Summary**

```python
# reporters.py

import typer
from datetime import datetime

class PipelineReporter:
    """Report pipeline progress and results."""

    @staticmethod
    def print_header():
        """Print pipeline header."""
        typer.echo("")
        typer.echo("🚀 Starting Wareflow pipeline...")
        typer.echo(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        typer.echo("")

    @staticmethod
    def print_step_header(step_number: int, total_steps: int, step_name: str):
        """Print step header."""
        typer.echo("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        typer.echo(f"Step {step_number}/{total_steps}: {step_name}")
        typer.echo("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        typer.echo("")

    @staticmethod
    def print_step_result(step_name: str, result: dict):
        """Print step result."""
        status = result['status']

        if status == 'success':
            typer.echo(f"✅ {step_name}: Completed successfully")

            # Add specific details
            if 'file' in result:
                typer.echo(f"   📄 {result['file']}")
            if 'sheets' in result:
                typer.echo(f"   📊 {result['sheets']} sheets")
            if 'size_mb' in result:
                typer.echo(f"   💾 {result['size_mb']} MB")

        elif status == 'failed':
            typer.echo(f"❌ {step_name}: Failed")

            if 'error' in result:
                typer.echo(f"   Error: {result['error']}")

        elif status == 'skipped':
            typer.echo(f"⏭️  {step_name}: Skipped")

            if 'reason' in result:
                typer.echo(f"   Reason: {result['reason']}")

        typer.echo("")

    @staticmethod
    def print_summary(summary: dict):
        """Print pipeline summary."""
        typer.echo("")
        typer.echo("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        typer.echo("📊 PIPELINE SUMMARY")
        typer.echo("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        typer.echo("")

        # Step results
        for step_name, step_result in summary['steps'].items():
            status = step_result['status']
            icon = {
                'success': '✅',
                'failed': '❌',
                'skipped': '⏭️',
                'partial': '⚠️'
            }.get(status, '❓')

            typer.echo(f"{icon} {step_name.capitalize()}: {status}")

        typer.echo("")

        # Timing
        duration = summary['duration_seconds']
        typer.echo(f"⏱️  Total time: {duration:.1f} seconds")
        typer.echo(f"🏁 Finished at: {summary['end_time']}")

        # Overall status
        overall = summary['overall_status']
        if overall == 'success':
            typer.echo("")
            typer.echo("✅ Pipeline completed successfully!")

            if 'export' in summary['steps'] and summary['steps']['export']['status'] == 'success':
                file = summary['steps']['export']['file']
                typer.echo("")
                typer.echo("💡 Next steps:")
                typer.echo(f"   open {file}")
                typer.echo("   wareflow status")

        elif overall == 'partial':
            typer.echo("")
            typer.echo("⚠️  Pipeline completed with warnings")

            if 'analyze' in summary['steps'] and summary['steps']['analyze']['status'] == 'failed':
                typer.echo("")
                typer.echo("💡 Note: Analysis failed, but raw data was exported")
                typer.echo("   Report contains raw database tables only")

        elif overall == 'failed':
            typer.echo("")
            typer.echo("❌ Pipeline failed")
            typer.echo("")
            typer.echo("💡 Solution:")

            if summary['steps']['import']['status'] == 'failed':
                typer.echo("   Check that Excel files are in data/ directory")
                typer.echo("   Verify config.yaml is correct")

            elif summary['steps']['export']['status'] == 'failed':
                typer.echo("   Check disk space availability")
                typer.echo("   Verify output/ directory is writable")
```

---

## Complete Execution Flow

### Pipeline Algorithm

```
┌─────────────────────────────────────────┐
│ 1. INITIALIZE ORCHESTRATOR             │
│    - Set start time                    │
│    - Load configuration                │
└──────────┬──────────────────────────────┘
           ↓
┌─────────────────────────────────────────┐
│ 2. RUN IMPORT (if not skipped)         │
│    → Execute import logic              │
│    → Capture results                   │
│    ⚠️  If failed: STOP pipeline        │
└──────────┬──────────────────────────────┘
           ↓
┌─────────────────────────────────────────┐
│ 3. RUN ANALYZE (if not skipped)        │
│    → Execute analyze logic             │
│    → Capture results                   │
│    ⚠️  If failed: CONTINUE (warning)   │
└──────────┬──────────────────────────────┘
           ↓
┌─────────────────────────────────────────┐
│ 4. RUN EXPORT (if not skipped)         │
│    → Execute export logic              │
│    → Choose mode (raw/analysis)        │
│    → Capture results                   │
│    ⚠️  If failed: STOP pipeline        │
└──────────┬──────────────────────────────┘
           ↓
┌─────────────────────────────────────────┐
│ 5. GENERATE SUMMARY                    │
│    - Calculate duration                │
│    - Determine overall status          │
│    - Print formatted report            │
└─────────────────────────────────────────┘
```

---

## Error Handling Strategy

### Error Classification

| Step | Severity | Action | Rationale |
|------|----------|--------|-----------|
| **Import** | Critical | Stop pipeline | Cannot analyze/export without data |
| **Analyze** | Non-critical | Continue, export raw | Can still provide value with raw data |
| **Export** | Critical | Stop pipeline | User expects file output |

### Error Recovery Logic

```python
# Import failed
if import_result['status'] == 'failed':
    # Cannot continue - no data
    analyze_result = {'status': 'skipped', 'reason': 'import failed'}
    export_result = {'status': 'skipped', 'reason': 'import failed'}
    overall_status = 'failed'

# Analyze failed
elif analyze_result['status'] == 'failed':
    # Can still export raw data
    export_mode = 'raw'  # Instead of 'analysis'
    overall_status = 'partial'

# Export failed
elif export_result['status'] == 'failed':
    # Critical - user wants the file
    overall_status = 'failed'
```

---

## User Experience Design

### Scenario 1: Successful Pipeline

**Context**: First time running complete pipeline

```bash
$ wareflow run
```

**Output**:
```
🚀 Starting Wareflow pipeline...
⏰ Started at: 2025-01-21 14:30:00

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Step 1/3: Import Data
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✓ Starting import process...

[Import progress...]

✅ Import: Completed successfully
  Total rows imported: 47,701
  Total time: 12.8 seconds

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Step 2/3: Analyze Data
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✓ Starting analysis process...

[Analyze progress...]

✅ Analyze: Completed successfully
  Analyses run: 4
  Total time: 1.8 seconds

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Step 3/3: Export Report
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✓ Starting export process...

[Export progress...]

✅ Export: Completed successfully
   📄 warehouse_report_20250121_143045.xlsx
   📊 4 sheets
   💾 2.8 MB


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 PIPELINE SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Import:   success
✅ Analyze:  success
✅ Export:   success

⏱️  Total time: 17.2 seconds
🏁 Finished at: 2025-01-21 14:30:17

✅ Pipeline completed successfully!

💡 Next steps:
   open output/warehouse_report_20250121_143045.xlsx
   wareflow status
```

---

### Scenario 2: Pipeline with Analyze Failure

**Context**: Database has issues but import succeeds

```bash
$ wareflow run
```

**Output**:
```
🚀 Starting Wareflow pipeline...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Step 1/3: Import Data
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Import: Completed successfully

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Step 2/3: Analyze Data
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

❌ Analyze: Failed
   Error: Missing table 'mouvements'

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Step 3/3: Export Report
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Export: Completed successfully (raw data mode)
   📄 raw_data_20250121_143200.xlsx
   📊 4 sheets
   💾 3.2 MB


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 PIPELINE SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Import:   success
⚠️  Analyze:  failed
✅ Export:   success

⏱️  Total time: 15.1 seconds
🏁 Finished at: 2025-01-21 14:32:15

⚠️  Pipeline completed with warnings

💡 Note: Analysis failed, but raw data was exported
   Report contains raw database tables only
   Check analyze errors for details
```

---

### Scenario 3: Dry Run Mode

**Context**: User wants to validate before executing

```bash
$ wareflow run --dry-run
```

**Output**:
```
🔍 Dry-run mode: Pipeline validation

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Checking pipeline prerequisites...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ config.yaml          exists
✅ warehouse.db         exists
✅ output/ directory    exists
✅ Excel files          found (3 files)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ All checks passed! Ready to run pipeline.

💡 To execute the pipeline:
  wareflow run

💡 Estimated time: ~15-20 seconds
```

---

### Scenario 4: Selective Step Execution

**Context**: Data already imported, just need analyze + export

```bash
$ wareflow run --skip-import
```

**Output**:
```
🚀 Starting Wareflow pipeline...
⏭️  Skipping import step

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Step 1/2: Analyze Data (step 1 skipped)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Analyze: Completed successfully

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Step 2/2: Export Report
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Export: Completed successfully


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 PIPELINE SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⏭️  Import:   skipped
✅ Analyze:  success
✅ Export:   success

⏱️  Total time: 4.1 seconds
```

---

## Command Options

| Option | Purpose | When to Use |
|--------|---------|-------------|
| `--skip-import` | Skip import step | Data already up-to-date |
| `--skip-analyze` | Skip analyze step | Want raw data only |
| `--skip-export` | Skip export step | Testing/debugging |
| `--dry-run` | Validate without executing | Pre-flight check |
| `--verbose` | Show detailed output | Debugging issues |

---

## Integration Examples

### Windows Task Scheduler

**Create scheduled task** (run daily at 6 AM):

```batch
# File: daily_warehouse_report.bat
@echo off
cd C:\Users\dpereira\Documents\mon-entrepot
wareflow run
```

**Task Scheduler Configuration**:
- Trigger: Daily at 6:00 AM
- Action: Start program
- Program: `daily_warehouse_report.bat`
- Start in: `C:\Users\dpereira\Documents\mon-entrepot`

### Linux Cron Job

**Edit crontab**:
```bash
crontab -e
```

**Add entry** (run daily at 6 AM):
```
0 6 * * 1-5 cd /path/to/mon-entrepot && /usr/local/bin/wareflow run
```

### GitHub Actions

**File**: `.github/workflows/daily-report.yml`

```yaml
name: Daily Warehouse Report

on:
  schedule:
    - cron: '0 6 * * 1-5'  # 6 AM, Mon-Fri
  workflow_dispatch:      # Allow manual trigger

jobs:
  warehouse-report:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v2

      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.10'

      - name: Install Wareflow
        run: pip install wareflow-analysis

      - name: Run pipeline
        run: |
          cd my-warehouse
          wareflow run

      - name: Upload report
        uses: actions/upload-artifact@v2
        with:
          name: warehouse-report-${{ github.run_number }}
          path: my-warehouse/output/*.xlsx
          retention-days: 30
```

---

## Performance Considerations

### Total Execution Time

| Operation | Expected Time | % of Total |
|-----------|---------------|------------|
| Import | 10-15 seconds | 70-80% |
| Analyze | 1-2 seconds | 5-10% |
| Export | 2-4 seconds | 10-20% |
| **Total** | **13-21 seconds** | **100%** |

### Optimization Strategies

1. **Parallel Steps** (future)
   - Analyze could start while import still running last tables
   - Currently sequential for simplicity

2. **Incremental Mode** (future)
   - Skip import if data hasn't changed
   - Check file modification times

3. **Progress Callbacks**
   - Show real-time progress from each step
   - Currently limited to step-level granularity

---

## Tests to Implement

### Unit Tests

```python
# tests/test_run_orchestrator.py
def test_orchestrator_initialization()
def test_run_import_step()
def test_run_analyze_step()
def test_run_export_step()
def test_determine_overall_status_success()
def test_determine_overall_status_partial()
def test_determine_overall_status_failed()
def test_dry_run_validation()

# tests/test_run_reporters.py
def test_print_header()
def test_print_step_header()
def test_print_step_result_success()
def test_print_step_result_failed()
def test_print_summary_success()
def test_print_summary_partial()
```

### Integration Tests

```python
# tests/test_run_integration.py
def test_full_pipeline_success()
def test_pipeline_with_import_failure()
def test_pipeline_with_analyze_failure()
def test_pipeline_with_export_failure()
def test_skip_import_mode()
def test_skip_analyze_mode()
def test_dry_run_mode()
def test_verbose_mode()
```

---

## Success Metrics

### Functional Objectives

- ✅ Execute complete pipeline in one command
- ✅ Handle errors gracefully at each step
- ✅ Provide clear progress feedback
- ✅ Generate useful summary report
- ✅ Support selective step execution

### Technical Objectives

- ✅ Zero code duplication (reuse existing modules)
- ✅ Clean error propagation
- ✅ Proper exit codes
- ✅ Total execution time < 30 seconds

### Quality Objectives

- ✅ Test coverage > 80%
- ✅ Clear, actionable error messages
- ✅ Professional output formatting
- ✅ Complete documentation

---

## Best Practices

### Error Handling

1. **Fail-Fast for Critical Steps**
   - Import failure → Stop immediately
   - Export failure → Stop immediately

2. **Best-Effort for Optional Steps**
   - Analyze failure → Continue with warning
   - User still gets value (raw data export)

3. **Clear Communication**
   - Always explain what happened
   - Provide actionable next steps
   - Indicate overall status clearly

### Code Organization

1. **Reuse Over Rewrite**
   - Call existing command modules
   - Don't duplicate business logic
   - Keep orchestrator lightweight

2. **Separation of Concerns**
   - Orchestrator: Coordination logic
   - Reporters: Display logic
   - Commands: Business logic

3. **Testability**
   - Mock command modules for testing
   - Test orchestration logic independently
   - Integration tests with real commands

---

## Comparison: Individual Commands vs Run

| Aspect | Individual Commands | `wareflow run` |
|--------|---------------------|----------------|
| **Commands needed** | 3 separate commands | 1 command |
| **User knowledge** | Must know all commands | Just one command |
| **Error handling** | Manual | Automatic |
| **Automation** | Requires script | Built-in |
| **Progress feedback** | Per command | Unified |
| **Use case** | Development, debugging | Daily operations |
| **Target audience** | Technical | Non-technical |

---

## Common Use Cases

### Use Case 1: Daily Automation

**Scenario**: Warehouse manager wants daily report every morning at 6 AM

**Solution**: Schedule `wareflow run` to run automatically

**Result**: Report ready when they arrive at work

### Use Case 2: Quick Update

**Scenario**: New Excel files received, need updated report ASAP

**Solution**: Single `wareflow run` command

**Result**: Fresh report in ~15 seconds

### Use Case 3: Data Validation

**Scenario**: Want to check if pipeline will work before running

**Solution**: `wareflow run --dry-run`

**Result**: Quick validation without executing

### Use Case 4: Partial Pipeline

**Scenario**: Data already imported, just need refresh report

**Solution**: `wareflow run --skip-import`

**Result**: Faster execution (~4 seconds vs ~15 seconds)

---

## Future Enhancements

### Email Notifications (Future)

Send report via email after pipeline completion:

```bash
wareflow run --email manager@company.com
```

### Slack/Teams Integration (Future)

Post notification to channel when report ready:

```bash
wareflow run --slack "#warehouse-reports"
```

### Retry Logic (Future)

Automatic retry on transient failures:

```bash
wareflow run --retry 3 --retry-delay 60
```

### Parallel Execution (Future)

Run analyze in parallel with last import tables:

```yaml
pipeline:
  import:
    parallel_analyze: true
```

---

## Dependencies with Other Commands

### Complete Dependency Chain

```
run DEPENDS ON:
├── import (CRITICAL)
│   └── Must succeed for pipeline to continue
├── analyze (OPTIONAL)
│   └── Failure reduces value but doesn't stop pipeline
└── export (CRITICAL)
    └── Must succeed for user to get output
```

### Module Dependencies

```
run/
├── orchestrator.py
│   ├── from import.importer import run_import
│   ├── from analyze.analyzer import DatabaseAnalyzer
│   └── from export.exporter import ReportExporter
└── reporters.py
    └── typer (for output)
```

**No new business logic** - Just coordination and reporting.

---

## Expected Deliverables

### Code
- 2 Python modules in `src/wareflow_analysis/run/`
- Modified `cli.py` with run command
- Pipeline orchestration logic

### Tests
- 8+ unit tests
- 7+ integration tests
- Pipeline test fixtures

### Documentation
- Complete docstrings
- User guide for automation
- Scheduling examples
- Troubleshooting guide

### Artifacts
- Example scheduled tasks
- Sample automation scripts
- Integration examples

---

## Implementation Phases

### Phase 1: Basic Orchestration (Day 1)
1. Create `run/` module structure
2. Implement orchestrator with 3 steps
3. Basic progress reporting
4. CLI integration

### Phase 2: Error Handling (Day 2)
5. Implement error classification
6. Add recovery logic
7. Enhanced summary reporting
8. Skip options

### Phase 3: Polish & Testing (Day 3)
9. Dry-run mode
10. Verbose mode
11. Complete testing
12. Documentation and examples

---

## Conclusion

The `run` command is the **user-friendly gateway** that makes the entire Wareflow system accessible and practical for daily operations. It transforms technical complexity into a single, simple command.

**Key Insights**:
1. **Minimal complexity** - Just orchestration, no new business logic
2. **Maximum value** - One command replaces three
3. **Smart error handling** - Continues when possible, stops when necessary
4. **Automation-ready** - Perfect for scheduling and integration

**Implementation Philosophy**:
- **Don't repeat yourself** - Reuse existing command modules
- **Keep it simple** - Orchestration is just coordination
- **User experience first** - Clear progress and useful summaries
- **Automation-friendly** - Designed for scheduling

**Value Delivered**:
- Single command for complete workflow
- Ideal for non-technical users
- Perfect for automation and scheduling
- Reduces operational overhead

**Next Steps After Run**:
- Gather user feedback on complete pipeline
- Optimize performance based on real usage
- Add notification features (email, Slack)
- Consider web dashboard for monitoring

---

*Document created: 2025-01-21*
*Status: Implementation Plan - Ready for Development*
*Priority: HIGH - User-friendly automation layer*
*Complexity: LOW - Orchestration only*
