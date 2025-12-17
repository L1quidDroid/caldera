# CALDERA Global Orchestration Roadmap

**Last Updated**: December 17, 2025  
**Maintained By**: Triskele Labs Development Team

---

## Current Status Overview

| Phase | Feature | Status | Target Completion |
|-------|---------|--------|-------------------|
| 1-3 | Core Orchestration | ✅ Released | Q3 2025 ✅ |
| 4 | Advanced Automation | 🚧 In Progress | Q1 2026 |
| 5 | Enrollment API | ✅ Released | Q4 2025 ✅ |
| 6 | PDF Reporting | ✅ Released | Q4 2025 ✅ |

---

## ✅ Completed Phases (Released)

### Phase 1-3: Core Orchestration Platform
**Release Date**: September 2025  
**Status**: Production Ready

**Features Delivered**:
- ✅ Campaign-as-code with YAML specifications
- ✅ REST API for campaign management
- ✅ Webhook publisher for real-time events
- ✅ SIEM integration (Elasticsearch, Splunk, QRadar)
- ✅ Multi-platform agent enrollment
- ✅ Comprehensive CLI tool

**Documentation**: 
- [ORCHESTRATION_GUIDE.md](ORCHESTRATION_GUIDE.md)
- [GETTING_STARTED.md](GETTING_STARTED.md)

---

### Phase 5: Dynamic Agent Enrollment
**Release Date**: November 2025  
**Status**: Production Ready

**Features Delivered**:
- ✅ REST API plugin architecture
- ✅ Bootstrap script generation (Windows, Linux, macOS, Docker, Terraform)
- ✅ Environment-based configuration
- ✅ Health check endpoints
- ✅ 50+ automated tests

**Documentation**:
- [plugins/enrollment/README.md](plugins/enrollment/README.md)
- [tests/README_PHASE5_TESTS.md](tests/README_PHASE5_TESTS.md)

---

### Phase 6: PDF Reporting with Branding
**Release Date**: December 2025  
**Status**: Production Ready

**Features Delivered**:
- ✅ HTML-to-PDF generation (WeasyPrint)
- ✅ ATT&CK Navigator layer generation
- ✅ Matplotlib visualizations with Triskele branding
- ✅ Campaign aggregation and reporting
- ✅ CLI integration

**Documentation**:
- [PHASE6_COMPLETE.md](PHASE6_COMPLETE.md)
- [DEV_SESSION_SUMMARY.md](DEV_SESSION_SUMMARY.md)

---

## 🚧 Phase 4: Advanced Operation Automation (In Progress)

**Current Progress**: 60% Complete  
**Target Completion**: Q1 2026 (January-March)

### ✅ Already Functional

#### Manual Operation Control
- CLI command: `python orchestrator/cli.py campaign start <id>`
- Real-time status monitoring
- Operation pause/resume capabilities
- Result collection and logging

#### Campaign Management
- YAML-based campaign specifications
- Multi-operation campaigns
- Agent group targeting
- Adversary profile selection

#### Monitoring & Observability
- Campaign status tracking
- Agent health monitoring
- Operation progress reporting
- Webhook event publishing

### 🚧 In Active Development

#### Q1 2026 - January: Operation Sequencing
**Target**: January 31, 2026  
**Status**: Design Complete (40% implemented)

**Features**:
- Automatic operation chaining based on dependencies
- Conditional execution (if-then-else logic)
- Parallel operation execution
- Wait conditions and timeouts

**Technical Approach**:
```yaml
# Example: Sequential operations with dependencies
operations:
  - id: recon
    adversary: discovery-adversary
    
  - id: lateral-movement
    adversary: movement-adversary
    depends_on: recon
    wait_for: all_links_complete
    
  - id: exfil
    adversary: exfil-adversary
    depends_on: lateral-movement
    condition: "links_successful > 5"
```

**Implementation Files**:
- `orchestrator/sequencer.py` - Operation dependency graph
- `orchestrator/conditions.py` - Conditional logic engine
- `app/objects/c_campaign.py` - Enhanced campaign model

---

#### Q1 2026 - February: Advanced Failure Recovery
**Target**: February 28, 2026  
**Status**: Prototype Stage (20% implemented)

**Features**:
- Automatic retry with exponential backoff
- Agent failover and redundancy
- Graceful degradation
- Error categorization and handling
- Dead letter queue for failed operations

**Technical Approach**:
```yaml
# Example: Retry configuration
recovery:
  max_retries: 3
  backoff_strategy: exponential  # 1s, 2s, 4s
  failover_agents: auto  # Use alternate agents
  on_failure:
    - notify_webhook
    - pause_campaign
    - log_to_siem
```

**Implementation Files**:
- `orchestrator/recovery.py` - Failure detection and recovery
- `orchestrator/retry_policy.py` - Retry strategies
- `app/service/planning_svc.py` - Enhanced planner integration

---

#### Q1 2026 - March: Auto-Scaling Agent Deployment
**Target**: March 31, 2026  
**Status**: Planning Phase (10% designed)

**Features**:
- Dynamic agent provisioning based on campaign needs
- Cloud provider integration (AWS, Azure, GCP)
- Container orchestration (Docker, Kubernetes)
- Auto-teardown after campaign completion
- Cost optimization and resource limits

**Technical Approach**:
```yaml
# Example: Auto-scaling configuration
agents:
  target_count: auto  # Calculate from operations
  platforms:
    - windows: 5
    - linux: 3
  provisioning:
    provider: aws
    instance_type: t3.medium
    max_cost_per_hour: 10.00
  lifecycle:
    auto_terminate: true
    retention_hours: 2
```

**Implementation Files**:
- `orchestrator/provisioner.py` - Cloud provider abstraction
- `orchestrator/scaling.py` - Auto-scaling logic
- `plugins/enrollment/auto_deploy.py` - Automated enrollment

---

### 🔮 Planned Enhancements (Beyond Q1 2026)

#### Intelligent Operation Planning
**Status**: Research Phase  
**Target**: Q2 2026

- Machine learning-based operation ordering
- Success prediction using historical data
- Adaptive planning based on agent responses
- Technique recommendation engine

#### Advanced Scheduling
**Status**: Design Phase  
**Target**: Q2 2026

- Cron-style campaign scheduling
- Time-zone aware execution
- Maintenance windows and blackout periods
- Calendar integration

#### Multi-Tenant Campaigns
**Status**: Requirements Gathering  
**Target**: Q3 2026

- Isolated campaign workspaces
- Team-based access control
- Resource quotas and limits
- Audit logging per tenant

---

## 🎯 How to Contribute

We welcome community contributions to accelerate Phase 4 completion!

### Priority Areas for Contribution

1. **Operation Sequencing** (January 2026)
   - Dependency graph implementation
   - Conditional logic parser
   - Unit tests for edge cases

2. **Failure Recovery** (February 2026)
   - Retry policy implementations
   - Agent health monitoring
   - Integration tests

3. **Documentation**
   - User guides for new features
   - API documentation
   - Tutorial videos

### Contribution Process

1. **Check Issues**: https://github.com/L1quidDroid/caldera/issues
2. **Discuss First**: Open an issue or comment before major work
3. **Follow Standards**: See [CONTRIBUTING.md](CONTRIBUTING.md)
4. **Submit PR**: Include tests and documentation
5. **Code Review**: Team will review within 48 hours

### Getting Started

```bash
# Clone the repository
git clone https://github.com/L1quidDroid/caldera.git
cd caldera

# Install dependencies
pip install -r requirements.txt

# Run tests
python -m pytest tests/

# Start development server
python server.py --insecure --log DEBUG
```

---

## 📊 Success Metrics

We track these metrics to measure Phase 4 progress:

| Metric | Current | Target | Status |
|--------|---------|--------|--------|
| Manual operation success rate | 85% | 85% | ✅ |
| Automated sequencing accuracy | N/A | 95% | 🚧 |
| Failure recovery time | Manual | <5 min | 🚧 |
| Agent provisioning time | Manual | <2 min | 🚧 |
| Campaign setup time | 10 min | <5 min | 🚧 |

---

## 📞 Contact & Support

- **Issues**: https://github.com/L1quidDroid/caldera/issues
- **Discussions**: https://github.com/L1quidDroid/caldera/discussions
- **Documentation**: [docs/README.md](docs/README.md)
- **Email**: Contact repository maintainers

---

## 📅 Release Schedule

### Q1 2026
- **January 15**: Operation sequencing alpha release
- **January 31**: Operation sequencing beta
- **February 15**: Failure recovery alpha
- **February 28**: Failure recovery beta
- **March 15**: Auto-scaling alpha
- **March 31**: Phase 4 v1.0 release candidate

### Q2 2026
- **April 30**: Phase 4 v1.0 stable release
- **May-June**: Enterprise features (multi-tenant, RBAC)

### Q3 2026
- **July-September**: Advanced analytics and ML features

---

## 🔄 Changelog

### December 2025
- ✅ Phase 6 PDF reporting completed
- ✅ Phase 5 enrollment API completed
- ✅ Documentation overhaul completed
- 🚧 Phase 4 operation sequencing started

### November 2025
- ✅ Phase 5 enrollment plugin released
- ✅ 50+ automated tests added
- ✅ CI/CD integration completed

### October 2025
- ✅ Phase 3 webhook publisher completed
- ✅ SIEM integration tested
- ✅ Campaign management CLI completed

### September 2025
- ✅ Phase 1-3 initial release
- ✅ Core orchestration platform launched

---

**Version**: 1.0  
**Document Owner**: Triskele Labs  
**Review Cycle**: Monthly during active development
