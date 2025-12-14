# Orchestrator Plugin - Campaign Orchestration for Caldera

Integrates campaign orchestration capabilities into Caldera, including webhook publishing, SIEM integration, and campaign management.

## Features

- Webhook event publishing to external systems
- SIEM integration (Elasticsearch, Splunk)
- Campaign lifecycle management
- Slack/N8N notifications
- REST API for orchestration

## Usage

The plugin is automatically loaded if present in the `plugins/` directory.

Access the plugin UI at: `http://localhost:8888/plugin/orchestrator`

Use the CLI for campaign management: `python3 orchestrator/cli.py`
