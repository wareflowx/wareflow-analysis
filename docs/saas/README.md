# Wareflow SaaS - Product Requirements Documentation

## Overview

This documentation defines the requirements and architecture for **Wareflow SaaS 1.0.0**, a native warehouse analysis system designed for data import, analysis, and reporting.

## Vision Statement

Build a **data-first, extensible warehouse analysis SaaS** that allows users to:
1. Import raw Excel files with flexible mapping
2. Automatically enable analyses based on data templates
3. Access and query base data immediately
4. Extend functionality with new analyses over time
5. Export clean, formatted Excel reports

## Core Principles

### 1. Data-First Architecture
- Raw imported data must be immediately accessible
- Search, filter, sort capabilities from day one
- Programmatic access to all data
- Base queries available before any analysis

### 2. Extensible Analysis Engine
- Pure TypeScript analysis framework
- Plugin system for adding new analyses
- No code recompilation required for extensions
- Analyses are loosely coupled from data layer

### 3. Template-Driven Workflows
- Data templates determine available analyses
- Automatic analysis unlocking based on imported data
- Versioned templates with migrations
- Custom templates per organization

### 4. Seamless Updates
- Automatic updates for SaaS
- Safe data migrations between versions
- Rollback capabilities
- Zero-downtime updates

## Documentation Structure

```
docs/saas/
├── README.md                          # This file
├── 01-overview.md                     # Product overview and goals
├── 02-technical-architecture.md       # Technical stack and architecture
├── 03-data-models.md                  # Data schemas and import system
├── 04-analysis-engine.md              # Extensible analysis framework
├── 05-template-system.md              # Template-driven workflows
├── 06-import-export.md                # Import and export workflows
├── 07-update-mechanism.md             # Update and migration system
├── 08-analyses-catalog.md             # Available analyses catalog
├── 09-anomaly-detection.md            # Anomaly detection and notifications
├── 10-mvp-roadmap.md                  # MVP scope and roadmap
├── 11-import-plugins.md               # WMS import plugin system (NEW)
└── 12-advanced-data-model.md          # Rich warehouse operations data model (NEW)
```

## Quick Reference

### Primary Workflows

```
1. DATA IMPORT (via Plugin)
   WMS Export → Plugin Transform → Normalized Data → Database

2. ANALYSIS
   Normalized Data → Analysis Engine → Results → Export

3. EXTENSION
   New WMS Plugin → Transform Logic → Register → Auto-available
```

### Key Components

| Component | Description | Status |
|-----------|-------------|--------|
| **Import Plugin System** | WMS-specific data transformation plugins | Planned |
| **Normalized Data Model** | Rich warehouse operations data structure | Planned |
| **Database Layer** | PostgreSQL/SQLite with Prisma ORM | Planned |
| **Analysis Engine** | Extensible TypeScript framework | Planned |
| **Export Engine** | Formatted Excel generation | Planned |
| **Update Manager** | Auto-updates with migrations | Planned |
| **Notification System** | Anomaly alerts (Phase 2) | Planned |

## Technology Stack

### Frontend
- **Framework**: React 18+ with TypeScript
- **Build Tool**: Vite
- **State Management**: Zustand + TanStack Query
- **UI Components**: shadcn/ui + Radix UI
- **Data Visualization**: Recharts / Plotly
- **Tables**: TanStack Table (virtualization)

### Backend
- **Runtime**: Node.js 20+ with TypeScript
- **Framework**: Fastify
- **Database**: PostgreSQL (prod) / SQLite (dev)
- **ORM**: Prisma
- **Queue**: BullMQ
- **Cache**: Redis

### Desktop Packaging
- **Framework**: Electron
- **Updater**: electron-updater
- **Builder**: electron-builder

## Current Status

- [x] Requirements analysis
- [ ] Technical architecture finalized
- [ ] Data models designed
- [ ] Analysis engine implemented
- [ ] MVP developed
- [ ] Beta testing

## Contributing

This documentation is a living document. As requirements evolve, update the relevant documents and increment the version number at the bottom of each document.

---

**Version**: 1.0.0
**Last Updated**: 2025-01-26
**Status**: Draft - Requirements Gathering
