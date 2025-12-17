# CALDERA Documentation

**Welcome to CALDERA!** A comprehensive cyber security platform for adversary emulation, red team operations, and incident response automation.

---

## 📚 Complete Documentation Index

**→ [INDEX.md - Full Documentation Directory](INDEX.md)**

The INDEX provides a comprehensive, organized guide to all CALDERA documentation resources.

---

## ⚡ Quick Links

### Getting Started
- **[Installation & Setup](guides/getting-started.md)** - Get CALDERA running in minutes
- **[Quick Reference](../QUICK_REFERENCE.md)** - Common commands and workflows
- **[Demo Walkthrough](../DEMO_WALKTHROUGH.md)** - Interactive demonstration

### Core Guides
- **[Orchestration Guide](guides/orchestration-guide.md)** - Campaign automation and management
- **[End-to-End User Journey](../END_TO_END_USER_JOURNEY.md)** - Complete workflow examples
- **[Testing Guide](../TESTING_GUIDE_DEVELOPER.md)** - Quality assurance

### For Developers
- **[Contributing](../CONTRIBUTING.md)** - How to contribute
- **[Folder Structure](../FOLDER_STRUCTURE_PLAN.md)** - Project organization
- **[Implementation Summary](implementation-summary.md)** - Technical details

---

## 🎯 What Can CALDERA Do?

### Adversary Emulation
- Execute MITRE ATT&CK techniques automatically
- Multi-platform agent support (Windows, Linux, macOS)
- Custom adversary profile creation

### Campaign Orchestration
- Automated multi-phase operations
- Infrastructure provisioning (Docker, Terraform, Kubernetes)
- Dynamic agent enrollment and management

### SIEM Integration
- Real-time event streaming to Elastic, Splunk, QRadar
- Webhook notifications (Slack, N8N, custom endpoints)
- Comprehensive audit logging

### Reporting & Visualization
- PDF reports with executive summaries
- ATT&CK Navigator layer generation
- Timeline visualizations and statistics

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                  CALDERA Core                        │
│  REST API • Web UI • C2 Server • Plugin System     │
└──────────────────┬──────────────────────────────────┘
                   │
    ┌──────────────┼──────────────┐
    │              │              │
    ▼              ▼              ▼
┌─────────┐   ┌─────────┐   ┌─────────┐
│ Agents  │   │Reporting│   │ SIEM    │
│Sandcat  │   │PDF/JSON │   │ATT&CK   │
│Manx     │   │Webhooks │   │Navigator│
└─────────┘   └─────────┘   └─────────┘
```

---

## 📖 Documentation by Audience

### New Users
1. [Getting Started Guide](guides/getting-started.md)
2. [Demo Walkthrough](../DEMO_WALKTHROUGH.md)
3. [Quick Reference](../QUICK_REFERENCE.md)

### Operators
1. [Orchestration Guide](guides/orchestration-guide.md)
2. [End-to-End User Journey](../END_TO_END_USER_JOURNEY.md)
3. [Campaign Management](guides/orchestration-guide.md#campaign-management)

### Developers
1. [Contributing Guide](../CONTRIBUTING.md)
2. [Testing Guide](../TESTING_GUIDE_DEVELOPER.md)
3. [Implementation Summary](implementation-summary.md)

---

## 🚀 Recent Updates

### Codebase Cleanup (December 2025)
- ✅ **Phase 1**: Comprehensive docstrings for core services
- ✅ **Phase 2**: WCAG 2.1 accessibility compliance
- ✅ **Phase 3**: Duplicate code elimination with tests
- ✅ **Phase 4**: Custom exception handling system
- ✅ **Phase 5**: Magic number extraction to constants

[View Dev Session Summary](../DEV_SESSION_SUMMARY.md)

### Phase 6: PDF Reporting (Complete)
- Professional PDF report generation
- ATT&CK Navigator layer export
- Visualizations and statistics

[View Phase 6 Documentation](phases/phase6-pdf-reporting.md)

---

## 🔗 External Resources

- **Official Site**: https://caldera.mitre.org
- **GitHub**: https://github.com/mitre/caldera
- **MITRE ATT&CK**: https://attack.mitre.org/
- **Video Tutorials**: [YouTube Playlist](https://www.youtube.com/playlist?list=PLF2bj1pw7-ZvLTjIwSaTXNLN2D2yx-wXH)

---

## 📧 Community & Support

- **GitHub Issues**: Bug reports and feature requests
- **Security**: See [SECURITY.md](../SECURITY.md)
- **User Survey**: https://forms.office.com/g/ByBWxYTf8e

---

**Version**: 5.0.0 (Triskele Labs Enhanced)  
**Last Updated**: December 17, 2025
