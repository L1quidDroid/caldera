# Phase 6: PDF Reporting with Triskele Branding

**Status**: ✅ Complete  
**Version**: 1.0  
**Last Updated**: January 2025

## Overview

Phase 6 implements professional PDF report generation for Caldera campaigns with Triskele Labs branding. The reporting system collects campaign data, generates visualizations, creates ATT&CK Navigator layers, and produces comprehensive PDF reports suitable for executive briefings and technical reviews.

## Features

### 1. Report Aggregation
- **Async API Collection**: Collects data from CALDERA REST API endpoints
- **Multi-Source Data**: Operations, agents, adversaries, abilities, facts
- **Smart Aggregation**: Calculates success rates, statistics, and timelines
- **Error Tracking**: Captures and categorizes failures for analysis

### 2. Data Visualizations
- **Success Rate Charts**: Pie charts showing ability execution success
- **Platform Distribution**: Bar charts by Windows/Linux/Darwin
- **Technique Heatmaps**: ATT&CK techniques by tactic
- **Timeline Charts**: Chronological event visualization
- **Summary Dashboards**: Multi-metric overview charts
- **Triskele Branding**: Custom color palette (#48CFA0 green accent)

### 3. ATT&CK Navigator Integration
- **Layer Generation**: Creates MITRE ATT&CK Navigator JSON layers
- **Technique Mapping**: Maps executed abilities to ATT&CK techniques
- **Color Coding**: Green (success), red (failed), amber (partial)
- **Comparison Layers**: Multi-campaign comparison support
- **Metadata**: Includes campaign details and execution statistics

### 4. PDF Generation
- **Professional Layout**: Multi-page reports with US Letter format
- **Triskele Design**: Green accent (#48CFA0), Inter font, dark blue (#020816)
- **Comprehensive Sections**:
  - Cover page with campaign details
  - Executive summary with key metrics
  - Operations overview table
  - ATT&CK technique coverage
  - Agent deployment details
  - Timeline visualization
  - Error/failure analysis
- **WeasyPrint Engine**: HTML-to-PDF conversion with CSS styling
- **Optimized Output**: Font and image optimization for file size

## Architecture

### Components

```
orchestrator/
├── report_aggregator.py      # Collects campaign data from CALDERA API
├── attack_navigator.py        # Generates ATT&CK Navigator layers
├── report_visualizations.py   # Creates matplotlib charts
├── pdf_generator.py           # Main PDF generation engine
└── templates/
    └── report_template.html   # Jinja2 HTML template
```

### Data Flow

1. **Collection**: `ReportAggregator` fetches data via async API calls
2. **Processing**: Aggregates operations, agents, techniques, timeline
3. **Visualization**: `ReportVisualizations` generates charts as base64 PNG
4. **Layer**: `AttackNavigatorGenerator` creates ATT&CK JSON layer
5. **Rendering**: `PDFReportGenerator` renders Jinja2 template with data
6. **Output**: WeasyPrint converts HTML to PDF with CSS styling

## Usage

### CLI Command

```bash
# Generate PDF report for campaign
python orchestrator/cli.py report generate <campaign_id>

# Options
python orchestrator/cli.py report generate <campaign_id> \
  --format pdf \
  --output /path/to/report.pdf \
  --include-output \
  --no-facts \
  --no-attack-layer
```

### Arguments

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `campaign_id` | str | Required | Campaign identifier |
| `--format` | str | `pdf` | Report format (`pdf` or `json`) |
| `--output` | str | `data/reports/<id>_report.pdf` | Output file path |
| `--include-output` | flag | False | Include full ability output (verbose) |
| `--no-facts` | flag | False | Exclude agent facts from report |
| `--no-attack-layer` | flag | False | Skip ATT&CK Navigator layer generation |

### Python API

```python
from orchestrator.pdf_generator import PDFReportGenerator

# Initialize generator
generator = PDFReportGenerator(
    caldera_url="http://localhost:8888",
    api_key="ADMIN123"
)

# Generate report
result = await generator.generate_report(
    campaign_id="campaign_001",
    output_path="data/reports/campaign_001.pdf",
    include_output=False,
    include_facts=True,
    attack_layer=True
)

# Result contains:
# - pdf_path: Path to generated PDF
# - attack_layer_path: Path to ATT&CK Navigator JSON
# - file_size_mb: Report file size
# - summary: Campaign summary statistics
# - charts_generated: Number of charts created
```

## Examples

### Basic Report Generation

```bash
# Generate report for campaign "red_team_001"
python orchestrator/cli.py report generate red_team_001
```

**Output**:
```
📊 Generating Campaign Report

Campaign ID:      red_team_001
Format:           pdf
Include Output:   False
Include Facts:    True
ATT&CK Layer:     True

📊 Collecting campaign data...
  ✅ Collected data for 3 operations
📈 Generating charts...
  ✅ Generated 4 charts
🎯 Generating ATT&CK Navigator layer...
  ✅ ATT&CK layer saved to: data/reports/red_team_001_attack_layer.json
📝 Rendering HTML template...
📄 Generating PDF...
  ✅ PDF report generated: data/reports/red_team_001_report.pdf (2.45 MB)

============================================================
📊 REPORT GENERATION COMPLETE
============================================================
Campaign ID       red_team_001
PDF Report        data/reports/red_team_001_report.pdf
ATT&CK Layer      data/reports/red_team_001_attack_layer.json
File Size         2.45 MB
Operations        3
Agents            5
Abilities         127
Success Rate      89.8%
Charts Generated  4
============================================================

💡 Tip: Open the PDF report to view detailed campaign analysis with Triskele branding
💡 Tip: Upload the ATT&CK layer to https://mitre-attack.github.io/attack-navigator/
```

### Verbose Report with Output

```bash
# Include full command output in report (large file)
python orchestrator/cli.py report generate red_team_001 --include-output
```

### JSON Export

```bash
# Export raw JSON data without PDF generation
python orchestrator/cli.py report generate red_team_001 --format json
```

### Custom Output Path

```bash
# Save to specific location
python orchestrator/cli.py report generate red_team_001 \
  --output /tmp/executive_briefing.pdf
```

### Minimal Report

```bash
# Skip facts and ATT&CK layer for faster generation
python orchestrator/cli.py report generate red_team_001 \
  --no-facts \
  --no-attack-layer
```

## Report Sections

### 1. Cover Page
- **TRISKELE LABS** logo and branding
- Campaign ID and name
- Report generation date
- Triskele green accent (#48CFA0)

### 2. Executive Summary
- **Key Metrics Grid**:
  - Total operations executed
  - Unique agents deployed
  - Abilities executed
  - Overall success rate
  - Campaign duration
  - Platforms targeted
- **Campaign Overview**: Brief description

### 3. Operations Overview
- **Table**: All operations with details
  - Operation name and ID
  - Adversary used
  - Start/finish times
  - Duration
  - Abilities executed
  - Success rate

### 4. ATT&CK Coverage
- **Technique List**: Executed ATT&CK techniques
  - Technique ID (e.g., T1003)
  - Technique name
  - Tactic
  - Status badge (success/failed/partial)
  - Success rate

### 5. Agent Deployment
- **Agent Table**: All deployed agents
  - Agent ID
  - Hostname
  - Platform (Windows/Linux/Darwin)
  - Group assignment
  - Status

### 6. Timeline
- **Chronological Events**:
  - Operation starts/stops
  - Agent enrollments
  - Ability executions
  - Key milestones
- **Timeline Chart**: Visual event timeline

### 7. Errors and Failures
- **Failure Analysis**:
  - Failed ability details
  - Error messages
  - Recommendations

### 8. Charts and Visualizations
- Success rate pie chart
- Platform distribution bars
- Technique heatmap by tactic
- Timeline visualization
- Summary dashboard

## ATT&CK Navigator Layer

### Layer Format

```json
{
  "name": "Campaign red_team_001",
  "version": "4.9",
  "domain": "enterprise-attack",
  "description": "Campaign executed from 2025-01-01 to 2025-01-02",
  "techniques": [
    {
      "techniqueID": "T1003",
      "tactic": "credential-access",
      "color": "#48CFA0",
      "comment": "Executed 5 times with 100.0% success",
      "score": 5,
      "enabled": true,
      "metadata": [
        {"name": "operation", "value": "op_001"},
        {"name": "abilities", "value": "3"},
        {"name": "success_rate", "value": "100.0%"}
      ]
    }
  ],
  "gradient": {
    "colors": ["#48CFA0", "#020816"],
    "minValue": 0,
    "maxValue": 10
  }
}
```

### Color Scheme

| Status | Color | Description |
|--------|-------|-------------|
| Success | #48CFA0 (Triskele Green) | All abilities succeeded |
| Failed | #EF4444 (Red) | All abilities failed |
| Partial | #F59E0B (Amber) | Some succeeded, some failed |

### Viewing Layers

1. Open [MITRE ATT&CK Navigator](https://mitre-attack.github.io/attack-navigator/)
2. Click **Open Existing Layer**
3. Select **Upload from local**
4. Choose the generated JSON file (e.g., `red_team_001_attack_layer.json`)
5. View technique coverage with color-coded cells

## Customization

### Template Customization

Edit `orchestrator/templates/report_template.html` to modify:
- Page layout and structure
- Section ordering
- CSS styling
- Cover page design
- Header/footer content

### Chart Styling

Edit `orchestrator/report_visualizations.py` to customize:
- Color palettes
- Chart types (bar, pie, line, scatter)
- Font sizes and styles
- DPI and image quality
- Figure dimensions

### Branding

Update branding elements:
- **Primary Color**: `#48CFA0` (Triskele Green)
- **Dark Background**: `#020816` (Dark Blue)
- **Font**: Inter (Google Fonts)
- **Logo**: Triskele Labs wordmark

## Dependencies

```txt
# Core PDF generation
weasyprint==63.1

# Visualizations
matplotlib==3.9.0
numpy==1.26.4

# Already installed
aiohttp==3.12.14
jinja2==3.1.6
pyyaml==6.0.1
```

Install with:
```bash
pip install -r requirements.txt
```

## Troubleshooting

### WeasyPrint Installation Issues

**macOS**:
```bash
brew install pango cairo gdk-pixbuf
pip install weasyprint
```

**Ubuntu/Debian**:
```bash
sudo apt-get install build-essential python3-dev python3-pip python3-setuptools python3-wheel python3-cffi libcairo2 libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libffi-dev shared-mime-info
pip install weasyprint
```

### Large PDF Files

If reports are too large:
- Use `--no-attack-layer` to skip layer generation
- Omit `--include-output` to exclude verbose output
- Reduce chart DPI in `report_visualizations.py`

### Missing Data

If report is empty:
- Verify campaign ID exists: `python orchestrator/cli.py campaign status <id>`
- Check CALDERA API is running: `python orchestrator/cli.py health-check`
- Ensure operations have completed
- Review logs for API errors

### Font Issues

If fonts don't render:
- Ensure Inter font is available system-wide
- Or update template to use system fonts (Arial, Helvetica)

## Success Criteria

- ✅ PDF reports generated with Triskele branding
- ✅ ATT&CK Navigator layers with technique coverage
- ✅ Matplotlib charts with custom color palette
- ✅ Executive summary with key metrics
- ✅ Operations, agents, and timeline details
- ✅ Error analysis and recommendations
- ✅ CLI integration with `report generate` command
- ✅ File size optimization (<5 MB for typical campaigns)
- ✅ Professional layout suitable for briefings

## Next Steps

- **Phase 7**: Slack/N8N integration for notifications
- **Phase 8**: Governance and compliance features
- **Phase 9**: AI-driven TTP recommendations

## References

- [WeasyPrint Documentation](https://doc.courtbouillon.org/weasyprint/)
- [Matplotlib Gallery](https://matplotlib.org/stable/gallery/index.html)
- [MITRE ATT&CK Navigator](https://github.com/mitre-attack/attack-navigator)
- [Jinja2 Templates](https://jinja.palletsprojects.com/)
- [Triskele Labs Brand Guidelines](../branding/guidelines.md)
