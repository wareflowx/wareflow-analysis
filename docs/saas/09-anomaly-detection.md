# Anomaly Detection and Notifications

## Overview

Anomaly detection identifies unusual patterns, errors, or potential issues in warehouse data. This system provides real-time alerts and notifications to help users address problems quickly.

**Note**: This is a **Phase 2 feature**. The core system focuses on data access and basic analyses. Anomaly detection will be added after the foundation is stable.

## Anomaly Categories

1. **Data Quality Anomalies**: Issues with data integrity, completeness, or consistency
2. **Operational Anomalies**: Unusual operational patterns or performance issues
3. **Inventory Anomalies**: Stock-related issues (overstock, stockouts, dead stock)
4. **Performance Anomalies**: Unusual productivity or efficiency patterns
5. **Business Rule Violations**: Violations of defined business rules or constraints

## Anomaly Detection Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Anomaly Detection Engine                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  Detectors   │→│   Scoring    │→│  Filtering   │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  Aggregation │→│  Alerting    │→│  Notifying   │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    Notification Channels                     │
├─────────────────────────────────────────────────────────────┤
│  In-App  │  Email  │  Desktop  │  Webhook  │  Dashboard    │
└─────────────────────────────────────────────────────────────┘
```

## Detector Interface

### Core Detector Definition

```typescript
interface AnomalyDetector {
  // Identification
  id: string
  name: string
  description: string
  version: string
  category: AnomalyCategory

  // Configuration
  configSchema: z.ZodType<any>

  // Detection
  detect(
    data: DataSet,
    config: any,
    context: DetectionContext
  ): Promise<Anomaly[]> | Anomaly[]

  // Scoring
  score(anomaly: Anomaly): number  // 0-100 severity score

  // Metadata
  metadata: {
    frequency: 'real-time' | 'batch' | 'on-demand'
    estimatedDuration: number  // milliseconds
    requiresHistoricalData: boolean
    historicalDataDays?: number
  }
}

type AnomalyCategory =
  | 'data-quality'
  | 'operational'
  | 'inventory'
  | 'performance'
  | 'business-rule'
```

### Anomaly Structure

```typescript
interface Anomaly {
  // Identification
  id: string
  detectorId: string
  category: AnomalyCategory

  // Severity
  severity: 'low' | 'medium' | 'high' | 'critical'
  score: number  // 0-100

  // Description
  title: string
  description: string
  impact: string

  // Location
  location: {
    table?: string
    rowIds?: string[]
    columns?: string[]
    timestamp?: Date
  }

  // Context
  context: {
    actualValue: any
    expectedValue: any
    threshold: any
    variance: any
  }

  // Recommendations
  recommendations: string[]

  // Metadata
  detectedAt: Date
  status: 'active' | 'acknowledged' | 'resolved' | 'ignored'

  // History
  history?: {
    firstDetected: Date
    lastDetected: Date
    occurrenceCount: number
  }
}
```

## Built-in Detectors

### 1. Dead Stock Detector

**ID**: `dead-stock`
**Category**: `inventory`
**Severity**: `medium`

Detects products that haven't had any movement in a specified period.

```typescript
const deadStockDetector: AnomalyDetector = {
  id: 'dead-stock',
  name: 'Dead Stock Detection',
  description: 'Identify products without movements in specified period',
  category: 'inventory',

  configSchema: z.object({
    daysWithoutMovement: z.number().min(30).default(90),
    excludeInactive: z.boolean().default(true),
    minStockValue: z.number().optional()
  }),

  detect: async (data, config) => {
    const { daysWithoutMovement, excludeInactive, minStockValue } = config

    // Find products without movements
    const deadProducts = await data.query
      .from('produits')
      .leftJoin('mouvements', 'no_produit')
      .groupBy('produits.no_produit')
      .having('MAX(mouvements.date_heure)', '<', daysAgo(daysWithoutMovement))
      .findMany()

    return deadProducts.map(product => ({
      id: generateId(),
      detectorId: 'dead-stock',
      category: 'inventory',
      severity: 'medium',
      score: calculateDeadStockScore(product, daysWithoutMovement),
      title: `Dead stock: ${product.nom_produit}`,
      description: `No movements in ${daysWithoutMovement} days`,
      impact: `Capital tied up in non-moving inventory`,
      location: {
        table: 'produits',
        rowIds: [product.no_produit]
      },
      context: {
        actualValue: `${daysWithoutMovement}+ days`,
        expectedValue: `< ${daysWithoutMovement} days`,
        threshold: daysWithoutMovement
      },
      recommendations: [
        'Review product relevance',
        'Consider discounting to clear stock',
        'Evaluate product discontinuation',
        'Review future demand forecasts'
      ],
      detectedAt: new Date(),
      status: 'active'
    }))
  },

  score: (anomaly) => {
    // Score based on days without movement
    const days = anomaly.context.threshold
    if (days > 365) return 90  // Critical: > 1 year
    if (days > 180) return 70  // High: > 6 months
    if (days > 90) return 50   // Medium: > 3 months
    return 30                  // Low: < 3 months
  },

  metadata: {
    frequency: 'batch',
    estimatedDuration: 2000,
    requiresHistoricalData: true,
    historicalDataDays: 365
  }
}
```

---

### 2. Sudden Volume Spike Detector

**ID**: `sudden-spike`
**Category**: `operational`
**Severity**: `high` / `medium` (based on magnitude)

Detects unusual spikes in movement volume that may indicate data errors or actual operational anomalies.

```typescript
const suddenSpikeDetector: AnomalyDetector = {
  id: 'sudden-spike',
  name: 'Sudden Volume Spike Detection',
  description: 'Detect unusual spikes in movement volume',
  category: 'operational',

  configSchema: z.object({
    windowSize: z.number().default(7),      // Days for baseline
    spikeThreshold: z.number().default(3),  // Standard deviations
    minVolume: z.number().default(100)      // Minimum daily volume
  }),

  detect: async (data, config) => {
    const { windowSize, spikeThreshold, minVolume } = config

    // Get daily movement counts
    const dailyMovements = await data.query
      .from('mouvements')
      .select([
        'DATE(date_heure) as date',
        'COUNT(*) as count',
        'SUM(quantite) as volume'
      ])
      .groupBy('DATE(date_heure)')
      .orderBy('date', 'desc')
      .limit(windowSize + 1)
      .findMany()

    // Calculate mean and std dev for baseline
    const baseline = dailyMovements.slice(1)
    const mean = baseline.reduce((sum, d) => sum + d.volume, 0) / baseline.length
    const stdDev = Math.sqrt(
      baseline.reduce((sum, d) => sum + Math.pow(d.volume - mean, 2), 0) / baseline.length
    )

    // Check latest day for spike
    const latest = dailyMovements[0]
    const zScore = (latest.volume - mean) / stdDev

    if (zScore > spikeThreshold && latest.volume > minVolume) {
      return [{
        id: generateId(),
        detectorId: 'sudden-spike',
        category: 'operational',
        severity: zScore > 5 ? 'critical' : 'high',
        score: Math.min(zScore * 10, 100),
        title: `Unusual volume spike on ${formatDate(latest.date)}`,
        description: `Volume is ${zScore.toFixed(1)}σ above normal`,
        impact: `Potential data error or actual surge in activity`,
        location: {
          table: 'mouvements',
          timestamp: new Date(latest.date)
        },
        context: {
          actualValue: latest.volume,
          expectedValue: Math.round(mean),
          threshold: spikeThreshold,
          variance: `${((zScore - 1) * 100).toFixed(0)}% above normal`
        },
        recommendations: [
          'Verify data accuracy for this date',
          'Check for duplicate entries',
          'Investigate if actual operational event occurred',
          'Review with operations team'
        ],
        detectedAt: new Date(),
        status: 'active'
      }]
    }

    return []
  },

  score: (anomaly) => {
    const zScore = anomaly.context.variance
    if (zScore > 5) return 95   // Critical
    if (zScore > 4) return 80   // High
    if (zScore > 3) return 60   // Medium
    return 40                   // Low
  },

  metadata: {
    frequency: 'batch',
    estimatedDuration: 3000,
    requiresHistoricalData: true,
    historicalDataDays: 30
  }
}
```

---

### 3. Data Quality Detector

**ID**: `data-quality`
**Category**: `data-quality`
**Severity**: `medium` / `low`

Detects data quality issues such as missing values, invalid formats, and referential integrity violations.

```typescript
const dataQualityDetector: AnomalyDetector = {
  id: 'data-quality',
  name: 'Data Quality Issues Detection',
  description: 'Detect data quality problems',
  category: 'data-quality',

  configSchema: z.object({
    checks: z.array(z.enum([
      'missing-values',
      'invalid-dates',
      'negative-quantities',
      'orphaned-records',
      'duplicate-keys'
    ])).default([
      'missing-values',
      'invalid-dates',
      'negative-quantities'
    ])
  }),

  detect: async (data, config) => {
    const anomalies: Anomaly[] = []

    for (const check of config.checks) {
      switch (check) {
        case 'missing-values':
          anomalies.push(...await checkMissingValues(data))
          break
        case 'invalid-dates':
          anomalies.push(...await checkInvalidDates(data))
          break
        case 'negative-quantities':
          anomalies.push(...await checkNegativeQuantities(data))
          break
        case 'orphaned-records':
          anomalies.push(...await checkOrphanedRecords(data))
          break
        case 'duplicate-keys':
          anomalies.push(...await checkDuplicateKeys(data))
          break
      }
    }

    return anomalies
  },

  score: (anomaly) => {
    // Score based on impact and prevalence
    const severityMap = { critical: 90, high: 70, medium: 50, low: 30 }
    return severityMap[anomaly.severity] || 50
  },

  metadata: {
    frequency: 'batch',
    estimatedDuration: 5000,
    requiresHistoricalData: false
  }
}

// Helper functions for data quality checks
async function checkMissingValues(data: DataSet): Promise<Anomaly[]> {
  const issues = []

  // Check for null values in critical columns
  const criticalColumns = [
    { table: 'produits', column: 'no_produit' },
    { table: 'produits', column: 'nom_produit' },
    { table: 'mouvements', column: 'quantite' },
    { table: 'mouvements', column: 'date_heure' }
  ]

  for (const { table, column } of criticalColumns) {
    const nullCount = await data.query
      .from(table)
      .where(column, 'IS', null)
      .count()

    if (nullCount > 0) {
      issues.push({
        id: generateId(),
        detectorId: 'data-quality',
        category: 'data-quality',
        severity: nullCount > 100 ? 'high' : 'medium',
        score: Math.min(nullCount, 100),
        title: `Missing values in ${table}.${column}`,
        description: `${nullCount} rows have missing values`,
        impact: 'May affect analysis accuracy',
        location: { table, columns: [column] },
        context: { actualValue: nullCount, expectedValue: 0 },
        recommendations: [
          'Review source data',
          'Update missing values',
          'Set default values if appropriate'
        ],
        detectedAt: new Date(),
        status: 'active'
      })
    }
  }

  return issues
}
```

---

## Notification System

### Notification Channels

```typescript
interface NotificationChannel {
  id: string
  name: string
  type: NotificationType

  // Send notification
  send(anomalies: Anomaly[], recipient: NotificationRecipient): Promise<void>

  // Configuration
  configSchema: z.ZodType<any>
}

type NotificationType =
  | 'in-app'      // Show in app notification center
  | 'email'       // Send email
  | 'desktop'     // Desktop notification
  | 'webhook'     // HTTP webhook
  | 'dashboard'   // Show on dashboard widget
```

### In-App Notifications

```typescript
class InAppNotificationChannel implements NotificationChannel {
  id = 'in-app'
  name = 'In-App Notifications'
  type = 'in-app'

  async send(anomalies: Anomaly[], recipient: NotificationRecipient): Promise<void> {
    // Store in notification database
    for (const anomaly of anomalies) {
      await db.notifications.insert({
        user_id: recipient.userId,
        anomaly_id: anomaly.id,
        title: anomaly.title,
        description: anomaly.description,
        severity: anomaly.severity,
        read: false,
        created_at: new Date()
      })
    }

    // Emit real-time event
    websocket.emit('notifications:new', {
      userId: recipient.userId,
      count: anomalies.length
    })
  }
}
```

### Email Notifications

```typescript
class EmailNotificationChannel implements NotificationChannel {
  id = 'email'
  name = 'Email Notifications'
  type = 'email'

  configSchema = z.object({
    template: z.enum(['summary', 'detailed']),
    frequency: z.enum(['immediate', 'hourly', 'daily'])
  })

  async send(anomalies: Anomaly[], recipient: NotificationRecipient): Promise<void> {
    const email = this.buildEmail(anomalies, recipient)

    await emailService.send({
      to: recipient.email,
      subject: email.subject,
      html: email.html,
      text: email.text
    })
  }

  private buildEmail(anomalies: Anomaly[], recipient: NotificationRecipient): Email {
    const critical = anomalies.filter(a => a.severity === 'critical')
    const high = anomalies.filter(a => a.severity === 'high')

    return {
      subject: `Anomaly Alert: ${critical.length} critical, ${high.length} high`,
      html: this.renderHtmlEmail(anomalies),
      text: this.renderTextEmail(anomalies)
    }
  }
}
```

### Webhook Notifications

```typescript
class WebhookNotificationChannel implements NotificationChannel {
  id = 'webhook'
  name = 'Webhook Notifications'
  type = 'webhook'

  configSchema = z.object({
    url: z.string().url(),
    method: z.enum(['POST', 'PUT']).default('POST'),
    headers: z.record(z.string()).optional()
  })

  async send(anomalies: Anomaly[], recipient: NotificationRecipient): Promise<void> {
    const payload = {
      anomalies,
      recipient,
      timestamp: new Date().toISOString()
    }

    await fetch(recipient.webhookUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...recipient.headers
      },
      body: JSON.stringify(payload)
    })
  }
}
```

## Alert Rules

### Rule Configuration

```typescript
interface AlertRule {
  id: string
  name: string
  description: string

  // Trigger conditions
  trigger: {
    detectorId: string
    severity?: AnomalySeverity
    scoreThreshold?: number  // Minimum score to trigger
    countThreshold?: number  // Minimum anomalies to trigger
  }

  // Notification settings
  notifications: {
    channels: NotificationChannel[]
    recipients: NotificationRecipient[]
    throttle: {
      maxNotifications: number  // Max notifications per period
      period: number            // Period in seconds
    }
  }

  // Schedule
  schedule?: {
    enabled: boolean
    timezone: string
    hours: number[]  // Hours when notifications allowed
  }

  // Status
  enabled: boolean
  createdAt: Date
  lastTriggered?: Date
}
```

### Example Alert Rules

```typescript
const alertRules: AlertRule[] = [
  {
    id: 'critical-stockouts',
    name: 'Critical Stockout Alerts',
    description: 'Alert immediately for critical stock issues',
    trigger: {
      detectorId: 'stockout',
      severity: 'critical',
      countThreshold: 1
    },
    notifications: {
      channels: ['in-app', 'email', 'desktop'],
      recipients: [
        { userId: 'warehouse-manager' },
        { userId: 'inventory-team-lead' }
      ],
      throttle: {
        maxNotifications: 10,
        period: 3600  // Max 10 per hour
      }
    },
    schedule: {
      enabled: true,
      timezone: 'UTC',
      hours: [6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18]  // 6am-6pm
    },
    enabled: true
  },

  {
    id: 'daily-quality-summary',
    name: 'Daily Data Quality Summary',
    description: 'Daily summary of data quality issues',
    trigger: {
      detectorId: 'data-quality',
      scoreThreshold: 30  // Any severity
    },
    notifications: {
      channels: ['email'],
      recipients: [{ userId: 'data-quality-team' }],
      throttle: {
        maxNotifications: 1,
        period: 86400  // Once per day
      }
    },
    schedule: {
      enabled: true,
      timezone: 'UTC',
      hours: [9]  // 9am daily
    },
    enabled: true
  }
]
```

## Anomaly Dashboard

### Dashboard Widgets

```typescript
interface AnomalyDashboard {
  widgets: DashboardWidget[]

  layout: {
    columns: number
    rows: number
  }
}

type DashboardWidget =
  | ActiveAnomaliesWidget
  | AnomalyTrendWidget
  | SeverityBreakdownWidget
  | CategoryBreakdownWidget
  | RecentAlertsWidget

// Active anomalies widget
interface ActiveAnomaliesWidget {
  type: 'active-anomalies'
  title: string
  config: {
    maxItems: number
    groupBy: 'severity' | 'category' | 'detector'
  }
}

// Anomaly trend widget
interface AnomalyTrendWidget {
  type: 'anomaly-trend'
  title: string
  config: {
    period: '7d' | '30d' | '90d'
    groupBy: 'day' | 'week' | 'month'
  }
}
```

## Implementation Timeline

**Phase 2** (after MVP is stable):

1. **Month 1-2**: Core detector framework + 3 basic detectors
2. **Month 3**: Notification channels (in-app, email)
3. **Month 4**: Alert rules engine + dashboard
4. **Month 5-6**: Advanced detectors + customization

---

**Version**: 1.0.0
**Last Updated**: 2025-01-26
**Status**: Draft - Planned for Phase 2
