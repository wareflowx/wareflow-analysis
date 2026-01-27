# Update and Migration Mechanism

## Overview

The update mechanism ensures seamless updates of the SaaS application while preserving user data and maintaining system integrity.

## Update Strategy

### Desktop Application Updates (Electron)

```typescript
interface UpdateStrategy {
  // Check for updates
  check(): Promise<UpdateInfo>

  // Download update
  download(updateInfo: UpdateInfo): Promise<void>

  // Apply update
  apply(): Promise<void>

  // Rollback if needed
  rollback(): Promise<void>
}
```

### Update Flow

```
┌─────────────────────────────────────────────────────────────┐
│  1. CHECK FOR UPDATES                                        │
│     • Check version against remote                          │
│     • Compare current and latest versions                   │
│     • Notify user if update available                       │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  2. DOWNLOAD UPDATE                                         │
│     • Download update package                               │
│     • Verify checksum/signature                             │
│     • Show progress to user                                 │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  3. PREPARE UPDATE                                          │
│     • Backup current version                                │
│     • Backup database schema                                │
│     • Prepare migration scripts                             │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  4. DATABASE MIGRATION                                      │
│     • Run migration scripts                                 │
│     • Validate migrated data                                │
│     • Create data version snapshots                         │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  5. APPLY UPDATE                                            │
│     • Install new version                                   │
│     • Update templates and analyses                         │
│     • Verify installation                                   │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  6. POST-UPDATE VERIFICATION                               │
│     • Run smoke tests                                       │
│     • Verify data integrity                                 │
│     • Test critical features                                │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  7. COMPLETE                                                │
│     Clean up backups and finalize                           │
└─────────────────────────────────────────────────────────────┘
```

## Version Management

### Semantic Versioning

```
MAJOR.MINOR.PATCH

Examples:
  1.0.0 → Initial release
  1.1.0 → New features (backward compatible)
  1.1.1 → Bug fix
  2.0.0 → Breaking changes
```

### Version Information

```typescript
interface AppVersion {
  major: number
  minor: number
  patch: number
  preRelease?: string
  buildMetadata?: string

  toString(): string
  compare(other: AppVersion): number
}

interface UpdateInfo {
  version: AppVersion
  releaseDate: Date
  downloadUrl: string
  checksum: string
  signature: string
  size: number

  // Release notes
  releaseNotes: {
    features: string[]
  improvements: string[]
    bugFixes: string[]
    breakingChanges?: string[]
  }

  // Migration info
  requiresMigration: boolean
  migrationVersion?: string
  estimatedTime: number  // seconds
}
```

## Database Migration

### Migration System

```typescript
interface Migration {
  // Version this migrates from
  from: string

  // Version this migrates to
  to: string

  // Migration type
  type: 'schema' | 'data' | 'template' | 'analysis'

  // Upgrade script
  up: (db: Database) => Promise<void>

  // Downgrade script (for rollback)
  down: (db: Database) => Promise<void>

  // Validation
  validate?: (db: Database) => Promise<boolean>

  // Safety checks
  safe: boolean  // Can be rolled back
  estimatedTime: number  // seconds
}

class MigrationRunner {
  async runMigration(migration: Migration): Promise<void> {
    // 1. Backup database
    await this.createBackup()

    try {
      // 2. Run migration
      await migration.up(this.db)

      // 3. Validate if check exists
      if (migration.validate) {
        const valid = await migration.validate(this.db)
        if (!valid) {
          throw new Error('Migration validation failed')
        }
      }

      // 4. Record migration
      await this.recordMigration(migration)

      // 5. Clean up old backups if successful
      await this.cleanupOldBackups()

    } catch (error) {
      // Rollback on error
      await this.rollbackMigration(migration)
      throw error
    }
  }

  async rollbackMigration(migration: Migration): Promise<void> {
    if (!migration.safe) {
      throw new Error('Cannot rollback unsafe migration')
    }

    // Restore from backup or run down script
    await migration.down(this.db)

    // Remove migration record
    await this.removeMigrationRecord(migration)
  }
}
```

### Migration Examples

#### Example 1: Add New Column

```typescript
const addProductCategory: Migration = {
  from: '1.0.0',
  to: '1.1.0',
  type: 'schema',
  safe: true,
  estimatedTime: 5,

  up: async (db) => {
    await db.schema.alterTable('produits')
      .addColumn('category_level_4', 'text')
      .execute()
  },

  down: async (db) => {
    await db.schema.alterTable('produits')
      .dropColumn('category_level_4')
      .execute()
  }
}
```

#### Example 2: Data Migration

```typescript
const normalizeUserNames: Migration = {
  from: '1.0.0',
  to: '1.1.0',
  type: 'data',
  safe: false,  // Cannot rollback data changes
  estimatedTime: 60,

  up: async (db) => {
    // Normalize user names to title case
    await db
      .updateTable('mouvements')
      .set({
        usager: sql`UPPER(SUBSTRING(${sql.ref('usager')}, 1, 1)) || LOWER(SUBSTRING(${sql.ref('usager')}, 2))`
      })
      .execute()
  },

  down: async (db) => {
    // Cannot rollback - user must restore from backup
    throw new Error('Data migration cannot be rolled back automatically')
  }
}
```

#### Example 3: Template Migration

```typescript
const updateBasicWarehouseTemplate: Migration = {
  from: '1.0.0',
  to: '1.1.0',
  type: 'template',
  safe: true,
  estimatedTime: 10,

  up: async (db) => {
    // Update template version
    await db
      .updateTable('templates')
      .set({ version: '1.1.0' })
      .where('id', '=', 'basic-warehouse')
      .execute()

    // Add new column mappings
    await db
      .insertInto('column_mappings')
      .values([
        {
          template_id: 'basic-warehouse',
          source_pattern: 'product_category',
          target_column: 'categorie_1',
          confidence: 0.9
        }
      ])
      .execute()
  },

  down: async (db) => {
    // Revert template version
    await db
      .updateTable('templates')
      .set({ version: '1.0.0' })
      .where('id', '=', 'basic-warehouse')
      .execute()

    // Remove new mappings
    await db
      .deleteFrom('column_mappings')
      .where('template_id', '=', 'basic-warehouse')
      .where('source_pattern', '=', 'product_category')
      .execute()
  }
}
```

## Template Versioning

### Template Migration Strategy

```typescript
interface TemplateMigration {
  templateId: string
  fromVersion: string
  toVersion: string

  // Migrate data to new template format
  migrateData: (data: DataSet) => Promise<DataSet>

  // Update column mappings
  updateMappings: (mappings: ColumnMapping[]) => ColumnMapping[]

  // Validate migrated data
  validate?: (data: DataSet) => Promise<ValidationResult[]>
}
```

### Data Version Snapshots

```sql
-- Data version tracking
CREATE TABLE data_versions (
  id SERIAL PRIMARY KEY,
  version VARCHAR(14) NOT NULL,  -- YYYYMMDDHHMMSS
  template_id VARCHAR(255),
  applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  description TEXT,

  -- Snapshot metadata
  tables_imported INTEGER[],
  row_counts JSONB,
  data_quality_score DECIMAL(3,2)
);

-- Rollback capability
CREATE TABLE data_snapshots (
  id SERIAL PRIMARY KEY,
  version VARCHAR(14) NOT NULL,
  table_name TEXT NOT NULL,
  snapshot_data BYTEA,  -- Compressed table data
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Analysis Updates

### Hot-Reloading Analyses

```typescript
class AnalysisUpdater {
  /**
   * Update analysis without restarting app
   */
  async updateAnalysis(analysisId: string, newDefinition: AnalysisDefinition): Promise<void> {
    // 1. Unregister old version
    this.engine.unregister(analysisId)

    // 2. Validate new definition
    this.validateAnalysis(newDefinition)

    // 3. Register new version
    this.engine.register(newDefinition)

    // 4. Notify UI
    this.notifyAnalysisUpdated(analysisId)
  }

  /**
   * Update all analyses from remote
   */
  async syncAnalyses(): Promise<void> {
    // Fetch latest analyses from server
    const latestAnalyses = await this.fetchRemoteAnalyses()

    // Update each analysis
    for (const analysis of latestAnalyses) {
      await this.updateAnalysis(analysis.id, analysis)
    }
  }
}
```

## Update Safety

### Pre-Update Checks

```typescript
interface PreUpdateCheck {
  name: string
  description: string

  // Check function
  check: () => Promise<boolean>

  // Error message if check fails
  errorMessage: string

  // Can update proceed if this fails?
  optional: boolean
}

const preUpdateChecks: PreUpdateCheck[] = [
  {
    name: 'disk-space',
    description: 'Sufficient disk space',
    check: async () => {
      const requiredSpace = 500 * 1024 * 1024  // 500MB
      const freeSpace = await getFreeDiskSpace()
      return freeSpace >= requiredSpace
    },
    errorMessage: 'Insufficient disk space. Need at least 500MB free.',
    optional: false
  },
  {
    name: 'data-backup',
    description: 'Database backup exists',
    check: async () => {
      return await hasRecentBackup()
    },
    errorMessage: 'No recent backup found. Please create a backup first.',
    optional: false
  },
  {
    name: 'critical-jobs',
    description: 'No critical jobs running',
    check: async () => {
      const runningJobs = await getRunningJobs()
      return runningJobs.filter(j => j.critical).length === 0
    },
    errorMessage: 'Critical jobs are running. Wait for completion or cancel jobs.',
    optional: false
  }
]
```

### Rollback Strategy

```typescript
class UpdateRollback {
  /**
   * Rollback update if verification fails
   */
  async rollback(updateInfo: UpdateInfo): Promise<void> {
    // 1. Stop new version
    await this.stopApplication()

    // 2. Restore previous version
    await this.restorePreviousVersion()

    // 3. Rollback database migrations
    await this.rollbackMigrations(updateInfo)

    // 4. Verify rollback
    const valid = await this.verifyRollback()

    if (!valid) {
      throw new Error('Rollback verification failed')
    }

    // 5. Start application
    await this.startApplication()
  }

  /**
   * Verify update was successful
   */
  async verifyUpdate(): Promise<boolean> {
    const checks = [
      this.checkApplicationStarts,
      this.checkDatabaseConnects,
      this.checkCriticalFeatures,
      this.checkDataIntegrity
    ]

    for (const check of checks) {
      const result = await check()
      if (!result.success) {
        this.logError(result.message)
        return false
      }
    }

    return true
  }
}
```

## Update Notifications

### User Notification Flow

```typescript
interface UpdateNotification {
  available: boolean
  currentVersion: AppVersion
  latestVersion: AppVersion

  // Urgency
  urgency: 'low' | 'medium' | 'high' | 'critical'

  // What's new
  releaseNotes: string

  // Actions
  actions: {
    updateNow: () => Promise<void>
    scheduleUpdate: (time: Date) => Promise<void>
    skipVersion: () => Promise<void>
    remindLater: () => Promise<void>
  }
}

class UpdateNotifier {
  async notifyUpdateAvailable(updateInfo: UpdateInfo): Promise<void> {
    // Determine urgency
    const urgency = this.calculateUrgency(updateInfo)

    // Show appropriate notification
    switch (urgency) {
      case 'critical':
        await this.showCriticalUpdateNotification(updateInfo)
        break
      case 'high':
        await this.showHighPriorityNotification(updateInfo)
        break
      case 'medium':
        await this.showStandardNotification(updateInfo)
        break
      case 'low':
        await this.showBackgroundNotification(updateInfo)
        break
    }
  }

  private calculateUrgency(updateInfo: UpdateInfo): UpdateUrgency {
    // Critical: Security fixes
    if (updateInfo.releaseNotes.bugFixes.some(fix =>
      fix.toLowerCase().includes('security')
    )) {
      return 'critical'
    }

    // High: Breaking changes
    if (updateInfo.releaseNotes.breakingChanges?.length > 0) {
      return 'high'
    }

    // Medium: Major version bump
    if (updateInfo.version.major > this.currentVersion.major) {
      return 'medium'
    }

    // Low: Minor version bump
    return 'low'
  }
}
```

## Scheduled Updates

### Auto-Update Configuration

```typescript
interface UpdateSchedule {
  enabled: boolean
  frequency: 'daily' | 'weekly' | 'monthly'
  dayOfWeek?: number  // 0-6 for weekly
  time?: string  // HH:MM format
  timezone: string

  // Behavior
  downloadOnly: boolean  // Download but don't install
  requireConfirmation: boolean
  allowCriticalUpdates: boolean  // Bypass schedule for critical updates
}

class UpdateScheduler {
  async scheduleUpdates(config: UpdateSchedule): Promise<void> {
    if (!config.enabled) {
      return
    }

    // Calculate next update time
    const nextUpdate = this.calculateNextUpdateTime(config)

    // Schedule update check
    this.scheduleTask(nextUpdate, async () => {
      const updateInfo = await this.checkForUpdates()

      if (updateInfo.available) {
        if (config.allowCriticalUpdates && this.isCritical(updateInfo)) {
          // Install immediately
          await this.installUpdate(updateInfo)
        } else if (config.requireConfirmation) {
          // Notify user
          await this.notifyUser(updateInfo)
        } else if (!config.downloadOnly) {
          // Install automatically
          await this.installUpdate(updateInfo)
        } else {
          // Download only
          await this.downloadUpdate(updateInfo)
        }
      }
    })
  }
}
```

## Update Server

### Version Metadata API

```typescript
// GET /api/updates/check
interface UpdateCheckResponse {
  updateAvailable: boolean
  latestVersion: AppVersion
  currentVersion: AppVersion
  downloadUrl?: string
  checksum?: string
  signature?: string
  releaseNotes: ReleaseNotes
  requiresMigration: boolean
  estimatedTime: number
}

// GET /api/updates/migrations/:version
interface MigrationResponse {
  migrations: Migration[]
  instructions: string
  warnings: string[]
}
```

---

**Version**: 1.0.0
**Last Updated**: 2025-01-26
**Status**: Draft
