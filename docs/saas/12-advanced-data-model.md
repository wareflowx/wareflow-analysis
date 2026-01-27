# Advanced Data Model - Warehouse Operations

## Overview

This document defines the **normalized data model** that all import plugins must produce. This model is designed to capture the complexity of real warehouse operations with full traceability.

## Core Philosophy

```
Every movement must be traceable:
  → WHO did it
  → WHAT they moved
  → FROM where
  → TO where
  → WHEN they did it
  → WHY (if applicable)
```

## Entity Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         MASTER DATA                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │   Products   │    │  Locations   │    │    Users     │      │
│  │              │    │              │    │              │      │
│  │ • productId  │    │ • locationId │    │ • userId     │      │
│  │ • code       │    │ • zone       │    │ • name       │      │
│  │ • description│    │ • aisle      │    │ • team       │      │
│  │ • batch/lot  │    │ • bay        │    │ • role       │      │
│  │ • categories │    │ • level      │    │ • active     │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    OPERATIONAL DATA                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐                                              │
│  │    Orders    │                                              │
│  │              │                                              │
│  │ • orderId    │──┐                                           │
│  │ • type       │  │                                           │
│  │ • status     │  │                                           │
│  │ • priority   │  │                                           │
│  │ • dates      │  │                                           │
│  └──────────────┘  │                                           │
│         │          │                                           │
│         └──────────┼───┐                                       │
│                    │   │                                       │
│         ┌──────────▼───▼─────────┐                            │
│         │   Picking Lines        │                            │
│         │                        │                            │
│         │ • lineId               │                            │
│         │ • productId            │                            │
│         │ • quantity             │                            │
│         │ • sourceLocation       │←──┐                         │
│         │ • destLocation         │   │                         │
│         │ • pickerId ────────────┼───┼───┐                    │
│         │ • pickStartTime        │   │   │                    │
│         │ • pickEndTime          │   │   │                    │
│         │ • duration             │   │   │                    │
│         └────────────────────────┘   │   │                    │
│                                     │   │                    │
│         ┌───────────────────────────┘   │                    │
│         │                               │                    │
│  ┌──────────────┐               ┌──────────────┐            │
│  │Replenishments│               │   Receipts   │            │
│  │              │               │              │            │
│  │ • replenId   │               │ • receiptId  │            │
│  │ • sourceLoc  │               │ • supplierId │            │
│  │ • destLoc    │               │ • lines      │            │
│  │ • productId  │               │ • receivedBy │            │
│  │ • movedBy    │               │ • date       │            │
│  │ • dates      │               │ • status     │            │
│  └──────────────┘               └──────────────┘            │
│                                                              │
│  ┌──────────────┐               ┌──────────────┐            │
│  │   Returns    │               │  Adjustments │            │
│  │              │               │              │            │
│  │ • returnId   │               │ • adjId      │            │
│  │ • customerId │               │ • productId  │            │
│  │ • reason     │               │ • quantity   │            │
│  │ • lines      │               │ • reason     │            │
│  │ • processedBy│               │ • adjustedBy │            │
│  └──────────────┘               └──────────────┘            │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

## Entity Definitions

### Product (Master Data)

```typescript
interface Product {
  // Identification
  productId: string                  // Internal unique ID
  productCode: string                // SKU/EAN/UPC
  alternateCodes?: string[]          // Other codes (EAN, UPC, etc.)
  description: string
  extendedDescription?: string

  // Classification
  category: ProductCategory
  productFamily?: string
  productGroup?: string
  commodityCode?: string

  // Physical characteristics
  unitOfMeasure: string              // EA, CS, PAL, etc.
  weight?: {
    gross: number                    // With packaging
    net: number                      // Product only
    uom: string                      // KG, LB
  }
  dimensions?: {
    length: number
    width: number
    height: number
    uom: string                      // CM, IN
  }
  volume?: number                    // Cubic units

  // Handling
  handlingCodes?: string[]           // Hazardous, fragile, etc.
  storageConditions?: StorageCondition[]
  stackingInfo?: {
    maxStackHeight: number
    stackable: boolean
    rotate: boolean                  // Can rotate for stacking
  }

  // Inventory
  inventoryStatus: InventoryStatus
  lotControl: boolean               // Requires lot tracking
  expirationControl: boolean         // Requires expiration tracking
  serialControl: boolean             // Requires serial tracking

  // Cost
  unitCost?: number
  averageCost?: number
  lastCost?: number

  // Supplier
  primarySupplierId?: string
  suppliers?: ProductSupplier[]

  // Metadata
  createdDate: Date
  modifiedDate: Date
  status: ProductStatus

  // Source tracking
  source: {
    wmsSystem: string
    externalProductId: string
    importBatch: string
  }
}

interface ProductCategory {
  level1: string                    // Required
  level2?: string
  level3?: string
  level4?: string
}

interface StorageCondition {
  type: 'temperature' | 'humidity' | 'security' | 'other'
  requirement: string
  min?: number
  max?: number
  uom?: string
}

interface ProductSupplier {
  supplierId: string
  supplierProductCode: string
  leadTimeDays: number
  minimumOrderQuantity: number
  preferred: boolean
}

type InventoryStatus =
  | 'active'
  | 'inactive'
  | 'discontinued'
  | 'obsolete'

type ProductStatus =
  | 'draft'
  | 'active'
  | 'pending-approval'
  | 'blocked'
```

### Location (Master Data)

```typescript
interface Location {
  // Identification
  locationId: string                // Unique location code
  barcode?: string

  // Hierarchy
  warehouse: string                 // Warehouse code
  zone: string                      // Zone code (e.g., "PICK-A", "RESERVE-B")
  aisle?: string                    // Aisle number
  bay?: string                      // Bay number
  level?: string                    // Level number
  position?: string                 // Position within level

  // Full location path
  locationPath: string              // e.g., "WH01/ZONE-PICK-AISLE01-BAY03-LVL02-POS01"

  // Type
  locationType: LocationType
  locationUsage: LocationUsage

  // Characteristics
  capacityInfo?: {
    volume: number                  // Cubic units
    weight: number                  // Max weight
    uom: string
  }

  // Constraints
  constraints?: {
    allowedProductTypes?: string[]  // Product categories allowed
    forbiddenProductTypes?: string[] // Product categories forbidden
    mixedProducts: boolean          // Can store multiple products
  }

  // Equipment
  equipmentRequired?: string[]      // Forklift, cherry picker, etc.

  // Status
  status: LocationStatus
  occupancy: LocationOccupancy

  // Metadata
  source: {
    wmsSystem: string
    externalLocationId: string
  }
}

type LocationType =
  | 'floor'           // Floor storage
  | 'racked'          // Rack storage
  | 'shelf'           // Shelf storage
  | 'bin'             // Bin storage
  | 'bulk'            // Bulk storage
  | 'mezzanine'       // Mezzanine
  | 'container'       // Container/storage container
  | 'vehicle'         // Truck/trailer

type LocationUsage =
  | 'receiving'       // Receiving area
  | 'shipping'        // Shipping area
  | 'picking'         // Primary picking
  | 'reserve'         // Reserve storage
  | 'bulk'            // Bulk storage
  | 'cross-dock'      // Cross-docking
  | 'quality'         // Quality inspection
  | 'quarantine'      // Quarantine area
  | 'damage'          // Damaged goods
  | 'staging'         // Staging area
  | 'packing'         // Packing station

type LocationStatus =
  | 'active'
  | 'inactive'
  | 'blocked'
  | 'under-maintenance'

type LocationOccupancy =
  | 'empty'
  | 'partial'
  | 'full'
  | 'reserved'
```

### User (Master Data)

```typescript
interface User {
  // Identification
  userId: string
  employeeId?: string
  username: string
  firstName: string
  lastName: string
  fullName: string

  // Contact
  email?: string
  phone?: string

  // Organization
  team?: string
  department?: string
  manager?: string                   // userId of manager
  directReports?: string[]           // userIds of direct reports

  // Role
  role: UserRole
  permissions?: string[]

  // Capabilities
  equipment?: {
    forklift: boolean
    cherryPicker: boolean
    palletJack: boolean
    other?: string[]
  }

  // Performance
  hireDate: Date
  status: UserStatus
  active: boolean

  // Metadata
  source: {
    wmsSystem: string
    externalUserId: string
  }
}

type UserRole =
  | 'picker'
  | 'packer'
  | 'receiver'
  | 'shipper'
  | 'forklift-operator'
  | 'inventory-specialist'
  | 'supervisor'
  | 'manager'
  | 'admin'

type UserStatus =
  | 'active'
  | 'on-leave'
  | 'terminated'
  | 'suspended'
```

### Order (Operational)

```typescript
interface Order {
  // Identification
  orderId: string                   // Unique internal ID
  externalOrderId: string           // WMS order ID (preserve!)
  orderNumber: string               // Human-readable order number

  // Type and classification
  orderType: OrderType
  orderCategory: OrderCategory
  priority: OrderPriority

  // Status
  orderStatus: OrderStatus
  waveId?: string                   // If part of wave

  // Dates
  orderDate: Date                   // When order was created
  requestedDate: Date               // Requested delivery date
  promisedDate: Date                // Promised delivery date
  scheduledDate?: Date              // Scheduled processing date
  startDate?: Date                  // When processing started
  completedDate?: Date              // When completed
  cancelledDate?: Date              // If cancelled

  // Parties
  customer: {
    customerId: string
    customerName: string
    customerCode?: string
  }
  shipTo: {
    locationId: string
    name: string
    address: Address
  }
  billTo?: {
    locationId: string
    name: string
    address: Address
  }

  // Shipping
  shipping: {
    carrier?: string
    serviceLevel?: string           // Ground, Next Day, etc.
    shippingTerms?: string          // FOB, etc.
    trackingNumber?: string
  }

  // Picking
  picking: {
    status: PickingStatus
    startDate?: Date
    completedDate?: Date
    pickerId?: string
    pickZone?: string
  }

  // Totals
  summary: {
    totalLines: number
    totalQuantity: number
    totalWeight?: number
    totalVolume?: number
    totalValue?: number
  }

  // Progress
  progress: {
    linesPicked: number
    linesConfirmed: number
    linesShipped: number
  }

  // Holds
  holds?: OrderHold[]

  // Metadata
  metadata: {
    sourceWarehouse: string
    sourceWMS: string
    importBatch: string
    externalData?: any              // Preserve original WMS data
  }
}

interface Address {
  line1: string
  line2?: string
  city: string
  state: string
  postalCode: string
  country: string
}

interface OrderHold {
  holdCode: string
  holdReason: string
  holdDate: Date
  releasedDate?: Date
  releasedBy?: string
}

type OrderType =
  | 'sales-order'      // Customer order (outbound)
  | 'transfer-order'   // Warehouse transfer
  | 'return-order'     // Customer return
  | 'replenishment'    // Replenishment order
  | 'adjustment'       // Inventory adjustment
  | 'assembly'         // Kit assembly

type OrderCategory =
  | 'regular'
  | 'emergency'
  | 'backorder'
  | 'future'
  | 'blanket'
  | 'standing'

type OrderPriority =
  | 'critical'
  | 'urgent'
  | 'high'
  | 'medium'
  | 'low'
  | 'deferred'

type OrderStatus =
  | 'draft'
  | 'submitted'
  | 'confirmed'
  | 'released'
  | 'in-progress'
  | 'completed'
  | 'cancelled'
  | 'on-hold'

type PickingStatus =
  | 'not-started'
  | 'in-progress'
  | 'completed'
  | 'partial'
```

### Picking Line (Operational)

```typescript
interface PickingLine {
  // Identification
  lineId: string                    // Unique line ID
  orderId: string                   // FK to Order
  externalLineId?: string           // WMS line ID
  lineNumber: number                // Line number on order

  // Product
  productId: string
  productCode: string
  productDescription?: string

  // Batch/Lot
  batchLot?: string
  serialNumbers?: string[]

  // Quantities
  quantities: {
    ordered: number                 // Original order qty
    allocated: number               // Allocated to pick
    picked: number                  // Actually picked
    confirmed: number               // Confirmed/shipped
    cancelled: number               // Cancelled
    short: number                   // Short quantity
    damaged: number                 // Damaged quantity
  }

  // Locations
  locations: {
    source: string                  // Pick location
    destination: string             // Usually shipping/packing
    current?: string                // Current location (if in transit)
  }

  // Dates
  dates: {
    allocatedDate?: Date
    pickStartDate?: Date            // WHEN picker started
    pickEndDate?: Date              // WHEN picker finished
    confirmedDate?: Date
  }

  // People
  people: {
    allocatedBy?: string            // WHO allocated
    pickerId?: string               // WHO picked
    confirmedBy?: string            // WHO confirmed
  }

  // Duration
  timing: {
    estimatedDuration?: number      // Estimated seconds
    actualDuration?: number         // Actual seconds
    variance?: number               // Difference (+/-)
  }

  // Status
  status: PickingLineStatus
  allocationStatus: AllocationStatus

  // Priority
  priority: OrderPriority
  sequence?: number                 // Pick sequence number

  // Conditions
  conditions?: {
    frozen: boolean
  hazardous: boolean
  fragile: boolean
  controlled: boolean               // Controlled substance
  qualityHold: boolean
  requiresVerification: boolean
  requiresDoubleCheck: boolean
  specialInstructions?: string
  }

  // Cost
  cost?: {
    unitCost: number
    extendedCost: number
  }

  // Metadata
  metadata: {
    sourceWMS: string
    originalData?: any
  }
}

type PickingLineStatus =
  | 'pending'
  | 'allocated'
  | 'in-progress'
  | 'picked'
  | 'confirmed'
  | 'short'
  | 'damaged'
  | 'cancelled'
  | 'verified'

type AllocationStatus =
  | 'not-allocated'
  | 'allocated'
  | 'depleted'
  | 'reallocated'
```

### Replenishment (Operational)

```typescript
interface Replenishment {
  // Identification
  replenishmentId: string
  externalReplenishmentId?: string

  // Type
  type: ReplenishmentType
  triggerReason: string
  triggerReasonCode?: string

  // Movement
  movement: {
    productId: string
    productCode: string
    sourceLocation: string          // FROM (bulk/reserve)
    destinationLocation: string     // TO (pick face)
  }

  // Quantities
  quantities: {
    requested: number               // Needed
    moved: number                   // Actually moved
    remaining: number               // Still to move
  }

  // People
  people: {
    requestedBy?: string            // WHO requested
    movedBy?: string                // WHO moved
    confirmedBy?: string
  }

  // Dates
  dates: {
    requestDate: Date
    scheduledDate?: Date
    startDate?: Date
    completedDate?: Date
    cancelledDate?: Date
  }

  // Duration
  timing: {
    estimatedDuration?: number      // Seconds
    actualDuration?: number         // Seconds
    cycleTime?: number              // From request to complete
  }

  // Priority
  priority: OrderPriority

  // Status
  status: ReplenishmentStatus

  // Wave/Batch
  waveId?: string
  batchId?: string

  // Metadata
  metadata: {
    warehouse: string
    zone: string
    sourceWMS: string
    originalData?: any
  }
}

type ReplenishmentType =
  | 'dynamic'         // Auto-triggered by min/max
  | 'manual'          // User-initiated
  | 'wave'            // Wave-based
  | 'forward'         // Forward pick area
  | 'emergency'       // Emergency refill
  | 'cycle-count'     // During cycle count

type ReplenishmentStatus =
  | 'pending'
  | 'scheduled'
  | 'in-progress'
  | 'completed'
  | 'partial'
  | 'cancelled'
  | 'on-hold'
```

### Receipt (Operational)

```typescript
interface Receipt {
  // Identification
  receiptId: string
  externalReceiptId?: string
  receiptNumber: string

  // Type
  receiptType: ReceiptType

  // Supplier
  supplier: {
    supplierId: string
    supplierCode: string
    supplierName: string
  }

  // Reference
  purchaseOrderNumber?: string
  supplierInvoiceNumber?: string
  deliveryNoteNumber?: string

  // Dates
  dates: {
    orderDate?: Date               // PO date
    expectedDate: Date              // Expected delivery
    actualDate: Date                // Actual receipt date
    postedDate?: Date               // Posted to inventory
  }

  // Delivery
  delivery: {
    carrier?: string
    vehicleRegistration?: string
    driverName?: string
    sealNumber?: string
    deliveryNotes?: string
  }

  // Location
  receivingLocation: {
    door: string
    locationId: string
  }

  // Lines
  lines: ReceiptLine[]

  // Status
  status: ReceiptStatus

  // People
  people: {
    receivedBy?: string
    verifiedBy?: string
    postedBy?: string
  }

  // Totals
  summary: {
    totalLines: number
    totalQuantity: number
    totalValue?: number
  }

  // Quality
  qualityControl: {
    required: boolean
    completed: boolean
    passed: boolean
    quarantineCount: number
  }

  // Metadata
  metadata: {
    warehouse: string
    sourceWMS: string
    originalData?: any
  }
}

interface ReceiptLine {
  // Identification
  lineId: string
  receiptId: string
  lineNumber: number

  // Product
  product: {
    productId: string
    productCode: string
    description?: string
  }

  // Batch/Lot
  batchLot: string
  expirationDate?: Date
  productionDate?: Date
  serialNumbers?: string[]

  // Quantities
  quantities: {
    ordered: number                 // On PO
    expected: number                // Expected delivery
    received: number                // Actually received
    accepted: number                // After QC
    rejected: number                // QC rejected
    damaged: number                 // Damaged on receipt
  }

  // Location
  locations: {
    temporary: string               // Receiving location
    final: string                   // Put-away location
  }

  // Dates
  dates: {
    receivedDate: Date
    inspectedDate?: Date
    putawayDate?: Date
  }

  // Cost
  cost: {
    unitCost: number
    totalCost: number
    currency: string
  }

  // Quality
  quality: {
    status: QualityStatus
    inspectedBy?: string
    inspectionDate?: Date
    rejectionReasons?: string[]
    quarantineUntil?: Date
  }

  // People
  people: {
    receivedBy?: string
    inspectedBy?: string
    putawayBy?: string
  }

  // Metadata
  metadata: {
    sourceWMS: string
    originalData?: any
  }
}

type ReceiptType =
  | 'purchase'         // From supplier
  | 'transfer'         // From another warehouse
  | 'return'           // Customer return
  | 'manufacture'      // From production
  | 'consignment'      // Consignment stock

type ReceiptStatus =
  | 'expected'
  | 'in-transit'
  | 'received'
  | 'inspected'
  | 'posted'
  | 'cancelled'

type QualityStatus =
  | 'pending'
  | 'approved'
  | 'quarantine'
  | 'rejected'
  | 'requires-inspection'
```

### Return (Operational)

```typescript
interface Return {
  // Identification
  returnId: string
  externalReturnId?: string
  returnNumber: string
  authorizationNumber?: string     // RMA number

  // Type
  returnType: ReturnType

  // Customer
  customer: {
    customerId: string
    customerName: string
    customerCode?: string
  }

  // Reference
  originalOrderId?: string
  originalOrderDate?: Date

  // Reason
  reason: {
    code: string
    description: string
    detail?: string
  }

  // Dates
  dates: {
    requestDate: Date
    approvedDate?: Date
    receivedDate?: Date
    processedDate?: Date
    completedDate?: Date
  }

  // Resolution
  resolution: {
    type: ReturnResolution
    creditIssued: boolean
    creditAmount?: number
    replacementSent: boolean
    replacementOrderId?: string
  }

  // Lines
  lines: ReturnLine[]

  // Status
  status: ReturnStatus

  // People
  people: {
    processedBy?: string
    approvedBy?: string
  }

  // Totals
  summary: {
    totalLines: number
    totalQuantity: number
    totalValue: number
  }

  // Shipping (for returns to vendor)
  shipping?: {
    carrier?: string
    trackingNumber?: string
    shipDate?: Date
  }

  // Metadata
  metadata: {
    warehouse: string
    sourceWMS: string
    originalData?: any
  }
}

interface ReturnLine {
  // Identification
  lineId: string
  returnId: string
  lineNumber: number

  // Reference
  originalOrderLineId?: string

  // Product
  product: {
    productId: string
    productCode: string
    description?: string
  }

  // Batch/Lot
  batchLot?: string
  serialNumbers?: string[]

  // Quantities
  quantities: {
    returned: number                // Quantity returned
    restockable: number             // Can be restocked
    damaged: number                 // Damaged
    defective: number               // Defective
    wrongItem: number               // Wrong item sent
  }

  // Condition
  condition: ReturnCondition
  conditionNotes?: string

  // Location
  locations: {
    returnLocation: string
    restockLocation?: string
    quarantineLocation?: string
    scrapLocation?: string
  }

  // Dates
  dates: {
    receivedDate: Date
    processedDate?: Date
  }

  // Resolution
  resolution: {
    action: ReturnResolution
    restocked: boolean
    credited: boolean
    replaced: boolean
  }

  // Cost
  cost: {
    unitCost: number
    totalCost: number
    restockValue: number
    scrapValue: number
  }

  // People
  people: {
    processedBy?: string
    inspectedBy?: string
  }

  // Customer feedback
  customerFeedback?: {
    reason: string
    detail?: string
    photos?: string[]
  }

  // Metadata
  metadata: {
    sourceWMS: string
    originalData?: any
  }
}

type ReturnType =
  | 'customer-return'
  | 'rtv'             // Return to vendor
  | 'field-return'    // Field return
  | 'recall'          // Product recall
  | 'internal'

type ReturnStatus =
  | 'requested'
  | 'approved'
  | 'pending-receipt'
  | 'received'
  | 'inspected'
  | 'processed'
  | 'completed'
  | 'rejected'
  | 'cancelled'

type ReturnCondition =
  | 'new'             // Unopened
  | 'opened'          // Opened box
  | 'damaged'         // Damaged in transit
  | 'defective'       // Product defective
  | 'wrong-item'      // Wrong item sent
  | 'incomplete'      // Missing parts
  | 'expired'         // Past expiration
  | 'no-receipt'

type ReturnResolution =
  | 'restock'         // Return to inventory
  | 'scrap'           // Scrap/write-off
  | 'return-to-vendor' // Send back to supplier
  - 'refurbish'       // Refurbish
  | 'quarantine'      // Hold for inspection
  | 'credit-only'     // Credit only, no return
```

### Inventory Adjustment (Operational)

```typescript
interface InventoryAdjustment {
  // Identification
  adjustmentId: string
  externalAdjustmentId?: string
  adjustmentNumber: string

  // Type
  type: AdjustmentType

  // Reason
  reason: {
    code: string
    description: string
    detail?: string
  }

  // Product
  product: {
    productId: string
    productCode: string
    description?: string
  }

  // Batch/Lot
  batchLot?: string

  // Location
  location: string

  // Quantities
  quantities: {
    expected: number                 // System expected
    actual: number                   // Physical count
    adjustment: number               // Difference (actual - expected)
  }

  // Value
  value: {
    unitCost: number
    totalCost: number
    currency: string
  }

  // Dates
  dates: {
    requestDate: Date
    countDate: Date
    approvedDate?: Date
    postedDate?: Date
  }

  // Approval
  approval: {
    requestedBy: string
    approvedBy?: string
    approvalDate?: Date
    status: ApprovalStatus
  }

  // Status
  status: AdjustmentStatus

  // People
  people: {
    countedBy?: string
    adjustedBy?: string
    verifiedBy?: string
  }

  // Accounting
  accounting: {
    glAccount?: string
    costCenter?: string
    postedToGL: boolean
    postingDate?: Date
  }

  // Metadata
  metadata: {
    warehouse: string
    zone?: string
    sourceWMS: string
    originalData?: any
  }
}

type AdjustmentType =
  | 'cycle-count'      // Cycle count adjustment
  | 'physical-inventory' // Annual physical inventory
  | 'damage'           // Damaged goods
  | 'loss'             // Shrinkage/loss
  | 'found'            // Found goods (positive adjustment)
  | 'expiration'       // Expired goods
  | 'recall'           // Product recall
  | 'transfer'         // Transfer adjustment
  | 'correction'       // System correction

type ApprovalStatus =
  | 'pending'
  | 'approved'
  | 'rejected'
  | 'escalated'

type AdjustmentStatus =
  | 'pending'
  | 'approved'
  | 'posted'
  | 'rejected'
  | 'cancelled'
```

## Data Quality Rules

### Required Fields

Every entity MUST have:
- ✅ Unique identifier
- ✅ External identifier (from WMS)
- ✅ Timestamps (created, modified)
- ✅ Source system tracking
- ✅ Status

### Traceability Requirements

Every operation MUST record:
- ✅ WHO performed it (userId)
- ✅ WHAT was affected (productId, locationId)
- ✅ WHEN it happened (timestamp)
- ✅ WHERE it happened (location)
- ✅ WHY (reason, if applicable)

### Data Consistency

- ✅ All foreign keys must reference existing entities
- ✅ Quantities must be >= 0
- ✅ Dates must be logical (end >= start)
- ✅ Status transitions must be valid

---

**Version**: 1.0.0
**Last Updated**: 2025-01-26
**Status**: Draft
