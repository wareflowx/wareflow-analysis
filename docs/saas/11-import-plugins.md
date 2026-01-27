# Import Plugin System

## Overview

The Import Plugin System is the **bridge between external WMS formats and the normalized Wareflow data model**. Developers write plugins to understand specific WMS export formats and transform them into the constant, clean Wareflow format.

## Architecture Philosophy

```
┌─────────────────────────────────────────────────────────────────┐
│                   EXTERNAL WMS SYSTEMS                          │
├─────────────────────────────────────────────────────────────────┤
│  WMS A          WMS B          WMS C          Custom WMS       │
│  (SAP)         (Manhattan)    (HighJump)     (Homegrown)      │
└─────────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│                    IMPORT PLUGINS LAYER                         │
├─────────────────────────────────────────────────────────────────┤
│  Plugin A       Plugin B       Plugin C       Plugin D         │
│  (reads SAP)    (Manhattan)    (HighJump)     (Custom)         │
│  ↓              ↓              ↓              ↓                 │
│  Transform      Transform      Transform      Transform        │
│  ↓              ↓              ↓              ↓                 │
│  Normalized     Normalized     Normalized     Normalized       │
└─────────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│                 NORMALIZED WAREFLOW FORMAT                      │
├─────────────────────────────────────────────────────────────────┤
│  Constant schema, clean data, full traceability                │
│  • Orders with picking lines                                   │
│  • Replenishment lines                                         │
│  • Receipts                                                    │
│  • Returns                                                     │
│  • Movements                                                   │
└─────────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│                   WAREFLOW ANALYSIS ENGINE                      │
└─────────────────────────────────────────────────────────────────┘
```

## Plugin Structure

### Plugin Definition

```typescript
interface ImportPlugin {
  // Plugin metadata
  id: string
  name: string
  version: string
  description: string
  author: string
  wmsSystem: string  // e.g., "SAP EWM", "Manhattan", "Custom"

  // Supported file formats
  supportedFormats: string[]  // e.g., ['xlsx', 'csv', 'xml', 'json']

  // Input schema - what this plugin expects from the WMS
  inputSchema: WMSInputSchema

  // Transform function - converts WMS format → Wareflow format
  transform: (input: WMSInputData, context: TransformContext) => Promise<WareflowData>

  // Validation - verifies input data can be processed
  validate: (input: WMSInputData) => ValidationResult[]

  // Configuration - plugin-specific settings
  configSchema?: z.ZodType<any>
  defaultConfig?: any

  // Lifecycle hooks
  beforeTransform?: (input: WMSInputData) => Promise<WMSInputData>
  afterTransform?: (output: WareflowData) => Promise<WareflowData>
  onError?: (error: TransformError) => Promise<void>
}
```

### Input Schema Definition

Each plugin defines what it expects from the WMS:

```typescript
interface WMSInputSchema {
  // Files/tables expected from WMS
  files: {
    name: string
    required: boolean
    description: string
    columns: WMSColumn[]
  }[]

  // Reference data (lookups, mappings)
  references?: {
    name: string
    type: 'lookup' | 'mapping' | 'static'
    description: string
  }[]
}

interface WMSColumn {
  name: string
  type: 'string' | 'number' | 'date' | 'boolean'
  required: boolean
  description: string
  // Example values for documentation
  examples?: any[]
}
```

## Normalized Wareflow Format

### Core Entities

```typescript
interface WareflowData {
  // Metadata
  metadata: {
    importDate: Date
    pluginId: string
    pluginVersion: string
    wmsSystem: string
    warehouseId: string
  }

  // Master data
  products: Product[]
  locations: Location[]
  users: User[]

  // Operational data
  orders: Order[]                           // Headers
  pickingLines: PickingLine[]               // Order line details
  replenishments: Replenishment[]           // Stock movements
  receipts: Receipt[]                       // Supplier receipts
  returns: Return[]                         // Customer returns
  inventoryAdjustments: InventoryAdjustment[] // Manual adjustments

  // Reference data
  suppliers: Supplier[]
  carriers: Carrier[]
  zones: Zone[]
}
```

### Order Entity (Enriched)

```typescript
interface Order {
  // Identification
  orderId: string                  // Unique order ID
  externalOrderId?: string         // WMS order ID
  orderType: OrderType
  orderStatus: OrderStatus

  // Dates
  createdAt: Date
  requestedDate: Date
  promisedDate?: Date
  shippedDate?: Date
  completedDate?: Date
  cancelledDate?: Date

  // Parties
  customer: CustomerInfo
  shippingAddress: Address
  billingAddress?: Address

  // Shipping
  carrier?: string
  serviceLevel?: string
  shippingPriority: Priority

  // Totals
  totalLines: number
  totalQuantity: number
  totalWeight?: number
  totalValue?: number

  // Picking
  pickingStatus: PickingStatus
  pickStartDate?: Date
  pickCompletedDate?: Date
  pickerId?: string

  // Metadata
  metadata: {
    sourceWarehouse: string
    sourceWMS: string
    importBatch: string
  }
}

interface PickingLine {
  // Identification
  lineId: string                    // Unique line ID
  orderId: string                   // FK to Order

  // Product
  productId: string
  productCode: string
  productDescription?: string
  batchLot?: string

  // Quantities
  orderedQuantity: number
  pickedQuantity: number
  confirmedQuantity: number
  cancelledQuantity?: number

  // Locations
  sourceLocation: string
  destinationLocation?: string     // Usually shipping/packing

  // Picking details
  pickerId?: string                 // WHO picked this line
  pickStartTime?: Date              // WHEN pick started
  pickEndTime?: Date                // WHEN pick completed
  pickDuration?: number             // Seconds

  // Status
  lineStatus: PickingLineStatus
  allocationStatus: AllocationStatus

  // Priority
  priority: Priority

  // Metadata
  metadata?: {
    serialNumbers?: string[]
    expirationDate?: Date
    qualityStatus?: string
  }
}

type OrderType =
  | 'sales'           // Customer order
  | 'transfer'        // Warehouse transfer
  | 'return'          // Customer return
  | 'replenishment'   // Stock replenishment
  | 'adjustment'      // Inventory adjustment

type OrderStatus =
  | 'draft'
  | 'confirmed'
  | 'released'
  | 'picking'
  | 'picked'
  | 'packed'
  | 'shipped'
  | 'completed'
  | 'cancelled'

type PickingStatus =
  | 'not-started'
  | 'in-progress'
  | 'completed'
  | 'partial'

type PickingLineStatus =
  | 'pending'
  | 'allocated'
  | 'picking'
  | 'picked'
  | 'confirmed'
  | 'cancelled'

type Priority = 'low' | 'medium' | 'high' | 'urgent'
```

### Replenishment Entity

```typescript
interface Replenishment {
  // Identification
  replenishmentId: string
  externalId?: string

  // Type
  replenishmentType: ReplenishmentType
  triggerReason: string

  // Movement
  sourceLocation: string           // FROM where
  destinationLocation: string      // TO where

  // Product
  productId: string
  productCode: string
  batchLot?: string

  // Quantities
  requestedQuantity: number
  movedQuantity: number

  // People
  requestedBy?: string             // WHO requested
  movedBy?: string                 // WHO moved

  // Dates
  requestDate: Date
  scheduledDate?: Date
  startDate?: Date                 // WHEN movement started
  completedDate?: Date             // WHEN completed

  // Status
  status: ReplenishmentStatus

  // Timing
  estimatedDuration?: number       // Seconds
  actualDuration?: number          // Seconds

  // Metadata
  metadata: {
    warehouse: string
    zone?: string
    priority: Priority
  }
}

type ReplenishmentType =
  | 'dynamic'         // Automatic based on min/max
  | 'manual'          // User-initiated
  | 'wave'            // Wave-based replenishment
  | 'forward'         // Pick-face replenishment

type ReplenishmentStatus =
  | 'pending'
  | 'scheduled'
  | 'in-progress'
  | 'completed'
  | 'cancelled'
```

### Receipt Entity

```typescript
interface Receipt {
  // Identification
  receiptId: string
  externalReceiptId?: string
  receiptNumber: string

  // Supplier
  supplierId: string
  supplierCode: string
  supplierName: string

  // Dates
  receiptDate: Date
  expectedDate?: Date
  postedDate?: Date

  // Delivery
  deliveryNote?: string
  carrier?: string
  vehicle?: string

  // Lines
  lines: ReceiptLine[]

  // Status
  receiptStatus: ReceiptStatus

  // People
  receivedBy?: string              // WHO received

  // Totals
  totalLines: number
  totalQuantity: number

  // Metadata
  metadata: {
    warehouse: string
    door?: string
    qualityControl?: boolean
  }
}

interface ReceiptLine {
  // Identification
  lineId: string
  receiptId: string

  // Product
  productId: string
  productCode: string
  batchLot: string

  // Quantities
  orderedQuantity: number          // From PO
  expectedQuantity: number         // Expected delivery
  receivedQuantity: number         // Actually received
  acceptedQuantity: number         // After QC
  rejectedQuantity?: number        // QC rejected

  // Locations
  destinationLocation: string      // Put-away location

  // Dates
  productionDate?: Date
  expirationDate?: Date
  receivedDate: Date

  // Quality
  qualityStatus: QualityStatus
  rejectionReasons?: string[]

  // Cost
  unitCost?: number
  totalCost?: number

  // People
  receivedBy?: string
  qualityCheckedBy?: string

  // Metadata
  metadata: {
    serialNumbers?: string[]
    palletNumber?: string
  }
}

type ReceiptStatus =
  | 'expected'
  | 'received'
  | 'posted'
  | 'cancelled'

type QualityStatus =
  | 'pending'
  | 'approved'
  | 'quarantine'
  | 'rejected'
```

### Return Entity

```typescript
interface Return {
  // Identification
  returnId: string
  externalReturnId?: string
  returnNumber: string

  // Type
  returnType: ReturnType

  // Customer
  customerId?: string
  customerName?: string

  // Reference
  originalOrderId?: string
  originalOrderDate?: Date

  // Reason
  returnReason: string
  returnReasonCode?: string

  // Dates
  returnDate: Date
  receivedDate?: Date
  processedDate?: Date

  // Lines
  lines: ReturnLine[]

  // Status
  returnStatus: ReturnStatus

  // People
  processedBy?: string

  // Totals
  totalLines: number
  totalQuantity: number
  totalValue?: number

  // Metadata
  metadata: {
    warehouse: string
    restockable: boolean
    creditIssued: boolean
  }
}

interface ReturnLine {
  // Identification
  lineId: string
  returnId: string

  // Product
  productId: string
  productCode: string
  batchLot?: string

  // Quantities
  returnedQuantity: number
  restockableQuantity: number
  damagedQuantity: number

  // Reason
  returnReason: string
  condition: ReturnCondition

  // Location
  returnLocation: string
  restockLocation?: string

  // Resolution
  resolution: ReturnResolution

  // Dates
  receivedDate: Date
  processedDate?: Date

  // People
  processedBy?: string

  // Metadata
  metadata: {
    serialNumbers?: string[]
    customerComments?: string
  }
}

type ReturnType =
  | 'customer-return'
  | 'rtv'             // Return to vendor
  | 'internal'        // Internal return

type ReturnStatus =
  | 'pending'
  | 'received'
  | 'inspected'
  | 'processed'
  | 'closed'
  | 'cancelled'

type ReturnCondition =
  | 'new'
  | 'opened'
  | 'damaged'
  | 'defective'
  | 'wrong-item'

type ReturnResolution =
  | 'restock'
  | 'scrap'
  | 'return-to-vendor'
  | 'refurbish'
  | 'quarantine'
```

## Plugin Implementation Example

### Example: SAP EWM Plugin

```typescript
import { z } from 'zod'

const sapEWMPlugin: ImportPlugin = {
  id: 'sap-ewm-import',
  name: 'SAP EWM Import Plugin',
  version: '1.0.0',
  description: 'Import data from SAP Extended Warehouse Management',
  author: 'Wareflow Team',
  wmsSystem: 'SAP EWM 9.5+',

  supportedFormats: ['xlsx', 'csv'],

  // What we expect from SAP EWM
  inputSchema: {
    files: [
      {
        name: '/EWM/Orders',
        required: true,
        description: 'Order headers from SAP EWM',
        columns: [
          { name: 'DOC_ID', type: 'string', required: true, description: 'Document ID' },
          { name: 'DOC_CAT', type: 'string', required: true, description: 'Document category (OUT, TRS, etc.)' },
          { name: 'LGTYP_DST', type: 'string', required: true, description: 'Destination storage type' },
          { name: 'LGTYP_SRC', type: 'string', required: false, description: 'Source storage type' },
          { name: 'USR_ID', type: 'string', required: true, description: 'User ID' },
          { name: 'CRDAT', type: 'date', required: true, description: 'Creation date' },
          { name: 'CRtim', type: 'string', required: true, description: 'Creation time' }
        ]
      },
      {
        name: '/EWM/OrderItems',
        required: true,
        description: 'Order line items',
        columns: [
          { name: 'DOC_ID', type: 'string', required: true, description: 'Document ID' },
          { name: 'ITM_ID', type: 'number', required: true, description: 'Item number' },
          { name: 'MATNR', type: 'string', required: true, description: 'Material number' },
          { name: 'MATNR_DOC', type: 'string', required: true, description: 'Product description' },
          { name: 'QUAN_BFR', type: 'number', required: true, description: 'Quantity before' },
          { name: 'QUANT', type: 'number', required: true, description: 'Quantity' },
          { name: 'UNIT', type: 'string', required: true, description: 'Unit of measure' },
          { name: 'LGTYP_SRC', type: 'string', required: true, description: 'Source bin' },
          { name: 'LGPLA_SRC', type: 'string', required: true, description: 'Source location' }
        ]
      },
      {
        name: '/EWM/WhoseWho',
        required: true,
        description: 'User activity log (who did what when)',
        columns: [
          { name: 'DOC_ID', type: 'string', required: true, description: 'Document ID' },
          { name: 'ITM_ID', type: 'number', required: false, description: 'Item number' },
          { name: 'USR_ID', type: 'string', required: true, description: 'User ID' },
          { name: 'ACTIVITY', type: 'string', required: true, description: 'Activity code (CONF, PICK, etc.)' },
          { name: 'ACT_TIM', type: 'date', required: true, description: 'Activity timestamp' }
        ]
      }
    ]
  },

  // Validate input
  validate: (input: WMSInputData) => {
    const errors: ValidationResult[] = []

    // Check required files
    if (!input.files['/EWM/Orders']) {
      errors.push({
        file: '/EWM/Orders',
        error: 'Missing required file',
        suggestion: 'Export order headers from /EWM/Orders transaction'
      })
    }

    // Check data consistency
    if (input.files['/EWM/Orders'] && input.files['/EWM/OrderItems']) {
      const orderIds = new Set(input.files['/EWM/Orders'].map(row => row.DOC_ID))
      const itemOrderIds = new Set(input.files['/EWM/OrderItems'].map(row => row.DOC_ID))

      // Find orders without items
      for (const orderId of orderIds) {
        if (!itemOrderIds.has(orderId)) {
          errors.push({
            file: '/EWM/OrderItems',
            error: `Order ${orderId} has no items`,
            suggestion: 'Verify all orders have line items'
          })
        }
      }
    }

    return errors
  },

  // Transform SAP format → Wareflow format
  transform: async (input: WMSInputData, context: TransformContext) => {
    const orders = input.files['/EWM/Orders']
    const items = input.files['/EWM/OrderItems']
    const activities = input.files['/EWM/WhoseWho']

    const result: WareflowData = {
      metadata: {
        importDate: new Date(),
        pluginId: 'sap-ewm-import',
        pluginVersion: '1.0.0',
        wmsSystem: 'SAP EWM',
        warehouseId: context.config.warehouseId
      },
      products: [],
      locations: [],
      users: [],
      orders: [],
      pickingLines: [],
      replenishments: [],
      receipts: [],
      returns: [],
      inventoryAdjustments: []
    }

    // Transform orders
    const orderMap = new Map<string, Order>()

    for (const order of orders) {
      const orderType = mapSAPDocTypeToOrderType(order.DOC_CAT)

      const wfOrder: Order = {
        orderId: order.DOC_ID,
        externalOrderId: order.DOC_ID,
        orderType,
        orderStatus: determineOrderStatus(order),
        createdAt: combineDateTime(order.CRDAT, order.CRTim),
        requestedDate: combineDateTime(order.CRDAT, order.CRTim),
        customer: {
          customerId: order.CUSTOMER_ID || 'UNKNOWN',
          customerName: order.CUSTOMER_NAME || 'Unknown'
        },
        shippingAddress: {
          location: order.LGTYP_DST
        },
        shippingPriority: determinePriority(order),
        totalLines: 0,  // Will be updated
        totalQuantity: 0,
        pickingStatus: 'not-started',
        metadata: {
          sourceWarehouse: context.config.warehouseId,
          sourceWMS: 'SAP EWM',
          importBatch: context.batchId
        }
      }

      orderMap.set(order.DOC_ID, wfOrder)
      result.orders.push(wfOrder)
    }

    // Transform picking lines
    const lineIdCounter = 1

    for (const item of items) {
      const order = orderMap.get(item.DOC_ID)
      if (!order) continue

      // Find who picked this line and when
      const lineActivities = activities.filter(a =>
        a.DOC_ID === item.DOC_ID &&
        a.ITM_ID === item.ITM_ID
      )

      const pickActivity = lineActivities.find(a => a.ACTIVITY === 'PICK')
      const confirmActivity = lineActivities.find(a => a.ACTIVITY === 'CONF')

      const pickingLine: PickingLine = {
        lineId: `${item.DOC_ID}-${item.ITM_ID}`,
        orderId: item.DOC_ID,
        productId: item.MATNR,
        productCode: item.MATNR,
        productDescription: item.MATNR_DOC,
        orderedQuantity: item.QUANT,
        pickedQuantity: item.QUAN_BFR - item.QUANT,
        confirmedQuantity: item.QUANT,
        sourceLocation: `${item.LGTYP_SRC}/${item.LGPLA_SRC}`,
        destinationLocation: order.orderType === 'sales' ? 'SHIPPING' : order.LGTYP_DST,
        pickerId: pickActivity?.USR_ID,
        pickStartTime: pickActivity?.ACT_TIM,
        pickEndTime: confirmActivity?.ACT_TIM,
        pickDuration: calculateDuration(pickActivity?.ACT_TIM, confirmActivity?.ACT_TIM),
        lineStatus: confirmActivity ? 'confirmed' : 'pending',
        allocationStatus: pickActivity ? 'allocated' : 'pending',
        priority: order.shippingPriority
      }

      result.pickingLines.push(pickingLine)
      order.totalLines++
    }

    return result
  },

  configSchema: z.object({
    warehouseId: z.string(),
    dateFormat: z.string().default('YYYYMMDD'),
    timeFormat: z.string().default('HHmmss')
  }),

  defaultConfig: {
    warehouseId: 'WH01',
    dateFormat: 'YYYYMMDD',
    timeFormat: 'HHmmss'
  }
}

// Helper functions
function mapSAPDocTypeToOrderType(docCat: string): OrderType {
  const mapping = {
    'OUT': 'sales',
    'TRS': 'transfer',
    'RET': 'return',
    'RPL': 'replenishment',
    'ADJ': 'adjustment'
  }
  return mapping[docCat] || 'sales'
}

function determineOrderStatus(order: any): OrderStatus {
  // Business logic to determine order status
  // Based on SAP EWM status codes
  return 'confirmed'
}

function determinePriority(order: any): Priority {
  // Business logic to determine priority
  // Based on SAP EWM priority codes
  return 'medium'
}

function combineDateTime(dateStr: string, timeStr: string): Date {
  // Parse SAP date/time format
  // Example: 20250126 + 143000 → Date
  return new Date()
}

function calculateDuration(start?: Date, end?: Date): number | undefined {
  if (!start || !end) return undefined
  return (end.getTime() - start.getTime()) / 1000
}
```

## Plugin Development Workflow

### 1. Analyze WMS Export

Developer analyzes the WMS export format:
- What tables/files are exported?
- What columns exist?
- What relationships exist?
- What business logic is encoded?

### 2. Create Input Schema

Define what the plugin expects:
```typescript
const inputSchema = {
  files: [
    { name: 'Orders', required: true, columns: [...] },
    { name: 'OrderLines', required: true, columns: [...] }
  ]
}
```

### 3. Implement Transform Logic

Write transformation code:
```typescript
async transform(input: WMSInputData): Promise<WareflowData> {
  // 1. Read WMS data
  const wmsOrders = input.files['Orders']

  // 2. Transform to Wareflow format
  const orders = wmsOrders.map(wmsOrder => ({
    orderId: wmsOrder.Order_ID,
    orderType: mapOrderType(wmsOrder.Type),
    // ... more mappings
  }))

  // 3. Return normalized data
  return { orders, pickingLines, ... }
}
```

### 4. Test Plugin

```typescript
// Test with sample data
const sampleData = loadSampleData('sap-ewm-sample.xlsx')
const plugin = loadPlugin('sap-ewm-import')

const result = await plugin.transform(sampleData, testContext)

// Validate output
assert(result.orders.length > 0)
assert(result.pickingLines.every(line => line.orderId))
```

### 5. Deploy Plugin

```bash
# Package plugin
npm run build:plugin -- plugin=sap-ewm-import

# Publish to plugin registry
npm publish wareflow-plugin-sap-ewm

# Install in Wareflow
wareflow plugins:install wareflow-plugin-sap-ewm
```

## Plugin Registry

```typescript
interface PluginRegistry {
  // List available plugins
  listPlugins(): ImportPlugin[]

  // Get plugin by ID
  getPlugin(pluginId: string): ImportPlugin | undefined

  // Register plugin
  registerPlugin(plugin: ImportPlugin): void

  // Unregister plugin
  unregisterPlugin(pluginId: string): void

  // Auto-detect plugin from file
  detectPlugin(file: File): ImportPlugin | undefined
}
```

## Best Practices

### 1. Preserve Data Fidelity

```typescript
// ✅ GOOD - Keep original data
const order: Order = {
  orderId: wmsOrder.Order_ID,
  externalOrderId: wmsOrder.Order_ID,  // Preserve WMS ID
  metadata: {
    sourceWMS: 'SAP EWM',
    originalData: wmsOrder  // Keep raw data for debugging
  }
}

// ❌ BAD - Lose original data
const order: Order = {
  orderId: generateNewId(),  // Lost connection to WMS!
  // No way to trace back
}
```

### 2. Handle Missing Data Gracefully

```typescript
// ✅ GOOD - Graceful handling
const pickerId = activity.USR_ID || 'UNKNOWN'
const pickTime = activity.ACT_TIM || order.createdAt

// ❌ BAD - Crashes on missing data
const pickerId = activity.USR_ID  // Crashes if undefined
```

### 3. Use Type Guards

```typescript
// ✅ GOOD - Type-safe
function isSAPOrder(order: any): order is SAPOrder {
  return order.DOC_ID && order.DOC_CAT && order.CRDAT
}

if (isSAPOrder(rawOrder)) {
  const order = transformOrder(rawOrder)
}

// ❌ BAD - Unsafe
const order = transformOrder(rawOrder)  // May crash if wrong format
```

### 4. Log Transformations

```typescript
// ✅ GOOD - Log what you do
context.logger.info('Transforming order', {
  orderId: wmsOrder.DOC_ID,
  orderType: wmsOrder.DOC_CAT,
  result: order.orderId
})

// ❌ BAD - Silent failures
const order = transformOrder(wmsOrder)  // Did it work? Who knows
```

---

**Version**: 1.0.0
**Last Updated**: 2025-01-26
**Status**: Draft
