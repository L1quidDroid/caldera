# CALDERA Documentation Index

**Version**: 5.0.0 (Triskele Labs Enhanced)  
**Last Updated**: December 17, 2025

Welcome to the CALDERA documentation! This index provides quick access to all documentation resources.

---

## 📚 Quick Links

### For New Users
- [Getting Started Guide](guides/getting-started.md) - Installation and first steps
- [Demo Walkthrough](orchestration/demo.md) - Guided tutorial
- [Troubleshooting Guide](TROUBLESHOOTING.md) - Common issues and solutions

### For Developers
- [API Documentation](api/rest-api.md) - REST API reference
- [Plugin Development](#) - Creating custom plugins
- [Contributing Guidelines](../CONTRIBUTING.md) - How to contribute

### For Operators
- [Orchestration Overview](orchestration/overview.md) - Campaign management
- [End-to-End User Journey](orchestration/user-journey.md) - Complete workflow
- [Webhook Integration](api/webhooks.md) - Event notifications

---

## 📖 Documentation Structure

```
docs/
├── INDEX.md (this file)
├── TROUBLESHOOTING.md
├── guides/
│   ├── getting-started.md
│   ├── installation.md
│   └── advanced-configuration.md
├── api/
│   ├── rest-api.md
│   ├── webhooks.md
│   └── authentication.md
└── orchestration/
    ├── overview.md
    ├── user-journey.md
    ├── demo.md
    └── campaigns.md
```

---

## 🚀 Getting Started

### 1. Installation

Follow the [Getting Started Guide](guides/getting-started.md) for detailed installation instructions.

**Quick Start**:
```bash
# Clone repository
git clone https://github.com/mitre/caldera.git --recursive
cd caldera

# Setup virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run setup validation
./scripts/setup_check.sh

# Start server
python server.py --insecure
```

### 2. Verify Installation

```bash
# Run health check
curl http://localhost:8888/api/v2/health

# Run integration tests
python3 tests/integration_test.py --quick
```

### 3. Access Web UI

Open browser to: http://localhost:8888

**Default credentials**:
- Red Team: `admin` / `admin`
- Blue Team: `blue` / `admin`

---

## 📋 Documentation by Use Case

### I want to...

#### Run my first operation
1. [Getting Started Guide](guides/getting-started.md) - Setup basics
2. [Demo Walkthrough](orchestration/demo.md) - Step-by-step tutorial
3. [Troubleshooting Guide](TROUBLESHOOTING.md) - If you hit issues

#### Integrate CALDERA into my workflow
1. [REST API Documentation](api/rest-api.md) - API endpoints
2. [Webhook Integration](api/webhooks.md) - Event notifications
3. [Orchestration Overview](orchestration/overview.md) - Campaign automation

#### Deploy agents at scale
1. [Enrollment API Guide](orchestration/user-journey.md#phase-5-enrollment-api-plugin) - Automated enrollment
2. [Agent Configuration](#) - Customizing agents
3. [Multi-Environment Deployment](#) - Cloud and on-premises

#### Develop plugins or extensions
1. [Plugin Architecture](#) - Plugin system overview
2. [Plugin Development Guide](#) - Creating custom plugins
3. [Contributing Guidelines](../CONTRIBUTING.md) - Submitting contributions

#### Troubleshoot issues
1. [Troubleshooting Guide](TROUBLESHOOTING.md) - Comprehensive problem solving
2. [FAQ](#) - Frequently asked questions
3. [Debug Mode](#) - Enabling verbose logging

---

## 🔗 Root-Level Documentation (Legacy)

These files remain in the repository root for backward compatibility:

| File | Description | New Location |
|------|-------------|--------------|
| [README.md](../README.md) | Project overview | (Keep in root) |
| [GETTING_STARTED.md](../GETTING_STARTED.md) | Installation guide | [docs/guides/getting-started.md](guides/getting-started.md) |
| [ORCHESTRATION_GUIDE.md](../ORCHESTRATION_GUIDE.md) | Orchestration details | [docs/orchestration/overview.md](orchestration/overview.md) |
| [END_TO_END_USER_JOURNEY.md](../END_TO_END_USER_JOURNEY.md) | Complete workflow | [docs/orchestration/user-journey.md](orchestration/user-journey.md) |
| [DEMO_WALKTHROUGH.md](../DEMO_WALKTHROUGH.md) | Tutorial walkthrough | [docs/orchestration/demo.md](orchestration/demo.md) |
| [BUGFIX_PLAN.md](../BUGFIX_PLAN.md) | Development planning | (Development use only) |

---

## 📚 External Resources

### Official CALDERA Resources
- **Official Docs**: https://caldera.readthedocs.io
- **GitHub Repository**: https://github.com/mitre/caldera
- **MITRE Website**: https://caldera.mitre.org

### Community Resources
- **GitHub Discussions**: https://github.com/mitre/caldera/discussions
- **Issue Tracker**: https://github.com/mitre/caldera/issues
- **Plugin Repository**: https://github.com/mitre-caldera

### Standards & Frameworks
- **ATT&CK Framework**: https://attack.mitre.org
- **ATLAS Framework**: https://atlas.mitre.org
- **D3FEND**: https://d3fend.mitre.org

---

## 🔍 Search Documentation

Can't find what you're looking for? Try these search methods:

### 1. Grep search across all docs
```bash
cd docs/
grep -r "your search term" .
```

### 2. GitHub search
Visit: https://github.com/mitre/caldera and use the search bar

### 3. ReadTheDocs search
Visit: https://caldera.readthedocs.io and use the search function

---

## 📝 Documentation Standards

### For Contributors

When adding documentation:

1. **Markdown format** - Use standard Markdown with GitHub extensions
2. **Code examples** - Include working code snippets
3. **Screenshots** - Add visuals for UI-heavy sections
4. **Cross-references** - Link to related documentation
5. **Update INDEX.md** - Add new docs to this index

### Style Guide

- Use sentence case for headings
- Include code examples for all procedures
- Add troubleshooting sections where applicable
- Keep line length ≤ 120 characters
- Use relative links for internal references

---

## 🆘 Getting Help

### Quick Troubleshooting
1. Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md) first
2. Run `./scripts/setup_check.sh` for diagnostics
3. Review server logs: `tail -f logs/caldera.log`

### Support Channels
1. **GitHub Issues** - Bug reports and feature requests
2. **GitHub Discussions** - Questions and community support
3. **Documentation** - Search existing docs first

### Reporting Documentation Issues
Found an error or gap in the documentation?

1. Open an issue: https://github.com/mitre/caldera/issues
2. Tag with `documentation` label
3. Include:
   - Document name and section
   - What's wrong or missing
   - Suggested improvement

---

## 🎯 Documentation Roadmap

### Completed ✅
- ✅ Getting Started Guide
- ✅ API v2 Documentation
- ✅ Troubleshooting Guide
- ✅ Orchestration Overview
- ✅ End-to-End User Journey
- ✅ Demo Walkthrough

### In Progress 🚧
- 🚧 Plugin Development Guide
- 🚧 Advanced Configuration Guide
- 🚧 Security Best Practices
- 🚧 Performance Tuning Guide

### Planned 📋
- 📋 Video tutorials
- 📋 Interactive examples
- 📋 Architecture deep-dives
- 📋 Case studies

---

## 📊 Documentation Metrics

| Metric | Value |
|--------|-------|
| Total documentation files | 25+ |
| Code examples | 150+ |
| API endpoints documented | 40+ |
| Troubleshooting scenarios | 30+ |
| Last full review | December 2025 |

---

**Maintained by**: Triskele Labs Development Team  
**Questions?** Open an issue on GitHub  
**Contributions Welcome!** See [CONTRIBUTING.md](../CONTRIBUTING.md)
