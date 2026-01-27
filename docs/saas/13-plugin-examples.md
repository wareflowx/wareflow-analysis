# Import Plugin Examples - Real World Scenarios

## Overview

This document provides concrete examples of import plugins for different WMS systems, showing how they transform WMS-specific data into the normalized Wareflow format.

## Example 1: Movement-Based WMS

### Scenario
A legacy WMS where **everything is a movement**. The system doesn't have explicit "picking lines" or "replenishments" - just movement records with different types.

### WMS Export Structure

```excel
/Movements sheet:
┌──────────┬───────────┬───────────┬──────────┬──────────┬─────────┬────────┬───────────┐
│ MovID    │ MovType   │ Product   │ BinFrom  │ BinTo    │ Qty     │ UserID │ Timestamp  │
├──────────┼───────────┼───────────┼──────────┼──────────┼─────────┼────────┼───────────┤
│ 1001     │ PICK      │ PROD-001  │ A-01-01  │ SHIP-01  │ 10      │ U001   │ 2025-01-26 │
│ 1002     │ PUTAWAY   │ PROD-002  │ RECEIPT  │ B-05-03  │ 50      │ U002   │ 2025-01-26 │
│ 1003     │ REPL      │ PROD-003  │ BULK-01  │ PICK-01  │ 100     │ U001   │ 2025-01-26 │
│ 1004     │ RECEIPT   │ PROD-004  │ DOCK-01  │ BULK-02  │ 200     │ U003   │ 2025-01-26 │
│ 1005     │ ADJUST    │ PROD-005  │ A-03-04  │ ADJUST   │ -5      │ U004   │ 2025-01-26 │
└──────────┴───────────┴───────────┴──────────┴──────────┴─────────┴────────┴───────────┘

/Orders sheet (minimal):
┌──────────┬───────────┬────────────┬───────────┐
│ OrderID  │ OrderType │ CustomerID │ ShipDest  │
├──────────┼───────────┼────────────┼───────────┤
│ ORD-001  │ SALES     │ CUST-001   │ SHIP-01   │
│ ORD-002  │ TRANSFER  │ WH-002     │ SHIP-02   │
└──────────┴───────────┴────────────┴───────────┘
```

### Plugin Implementation

```typescript
const movementBasedWMSPlugin: ImportPlugin = {
  id: 'movement-based-wms',
  name: 'Movement-Based WMS Plugin',
  version: '1.0.0',
  wmsSystem: 'Legacy Movement-Based WMS',

  supportedFormats: ['xlsx', 'csv'],

  inputSchema: {
    files: [
      {
        name: 'Movements',
        required: true,
        description: 'All warehouse movements',
        columns: [
          { name: 'MovID', type: 'string', required: true },
          { name: 'MovType', type: 'string', required: true },
          { name: 'Product', type: 'string', required: true },
          { name: 'BinFrom', type: 'string', required: true },
          { name: 'BinTo', type: 'string', required: true },
          { name: 'Qty', type: 'number', required: true },
          { name: 'UserID', type: 'string', required: true },
          { name: 'Timestamp', type: 'date', required: true }
        ]
      },
      {
        name: 'Orders',
        required: false,
        description: 'Order headers (if available)',
        columns: [
          { name: 'OrderID', type: 'string', required: true },
          { name: 'OrderType', type: 'string', required: true },
          { name: 'CustomerID', type: 'string', required: true },
          { name: 'ShipDest', type: 'string', required: true }
        ]
      }
    ]
  },

  transform: async (input: WMSInputData, context: TransformContext) => {
    const movements = input.files['Movements']
    const orders = input.files['Orders'] || []

    const result: WareflowData = {
      metadata: {
        importDate: new Date(),
        pluginId: 'movement-based-wms',
        pluginVersion: '1.0.0',
        wmsSystem: 'Movement-Based WMS',
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

    // Parse orders if available
    const orderMap = new Map()
    for (const order of orders) {
      const wfOrder: Order = {
        orderId: order.OrderID,
        externalOrderId: order.OrderID,
        orderType: mapOrderType(order.OrderType),
        orderStatus: 'confirmed',
        orderDate: new Date(),  // Not provided in minimal export
        requestedDate: new Date(),
        customer: {
          customerId: order.CustomerID,
          customerName: order.CustomerID
        },
        shippingAddress: {
          locationId: order.ShipDest
        },
        shippingPriority: 'medium',
        totalLines: 0,
        totalQuantity: 0,
        pickingStatus: 'not-started',
        summary: {
          totalLines: 0,
          totalQuantity: 0
        },
        progress: {
          linesPicked: 0,
          linesConfirmed: 0,
          linesShipped: 0
        },
        metadata: {
          sourceWarehouse: context.config.warehouseId,
          sourceWMS: 'Movement-Based WMS',
          importBatch: context.batchId
        }
      }
      orderMap.set(order.OrderID, wfOrder)
      result.orders.push(wfOrder)
    }

    // Current order being built
    let currentOrder: Order | null = null
    let currentOrderLines: PickingLine[] = []
    let lineCounter = 0

    // Transform movements to appropriate entities
    for (const movement of movements) {
      switch (movement.MovType) {
        case 'PICK':
          // This is a picking line
          const pickLine: PickingLine = {
            lineId: `PICK-${movement.MovID}`,
            orderId: currentOrder?.orderId || `AUTO-${movement.Timestamp.toISOString().split('T')[0]}`,
            lineNumber: lineCounter++,
            productId: movement.Product,
            productCode: movement.Product,
            quantities: {
              ordered: movement.Qty,
              allocated: movement.Qty,
              picked: movement.Qty,
              confirmed: movement.Qty,
              cancelled: 0,
              short: 0,
              damaged: 0
            },
            locations: {
              source: movement.BinFrom,
              destination: movement.BinTo
            },
            dates: {
              allocatedDate: movement.Timestamp,
              pickStartDate: movement.Timestamp,
              pickEndDate: movement.Timestamp
            },
            people: {
              pickerId: movement.UserID
            },
            timing: {
              actualDuration: 0  // Not provided
            },
            status: 'confirmed',
            allocationStatus: 'allocated',
            priority: 'medium',
            metadata: {
              sourceWMS: 'Movement-Based WMS',
              originalData: movement
            }
          }
          result.pickingLines.push(pickLine)

          // Link to order if exists
          if (currentOrder) {
            currentOrder.totalLines++
            currentOrder.totalQuantity += movement.Qty
            currentOrder.progress.linesPicked++
            currentOrder.progress.linesConfirmed++
          }
          break

        case 'REPL':
          // This is a replenishment
          const repl: Replenishment = {
            replenishmentId: `REPL-${movement.MovID}`,
            externalReplenishmentId: movement.MovID,
            type: 'dynamic',
            triggerReason: 'System-generated',
            movement: {
              productId: movement.Product,
              productCode: movement.Product,
              sourceLocation: movement.BinFrom,
              destinationLocation: movement.BinTo
            },
            quantities: {
              requested: movement.Qty,
              moved: movement.Qty,
              remaining: 0
            },
            people: {
              movedBy: movement.UserID
            },
            dates: {
              requestDate: movement.Timestamp,
              startDate: movement.Timestamp,
              completedDate: movement.Timestamp
            },
            timing: {
              actualDuration: 0
            },
            priority: 'medium',
            status: 'completed',
            metadata: {
              warehouse: context.config.warehouseId,
              zone: extractZone(movement.BinTo),
              sourceWMS: 'Movement-Based WMS',
              originalData: movement
            }
          }
          result.replenishments.push(repl)
          break

        case 'PUTAWAY':
        case 'RECEIPT':
          // This is a receipt
          // Find existing receipt or create new
          const receipt: Receipt = {
            receiptId: `RCPT-${movement.Timestamp.getTime()}-${movement.BinTo}`,
            receiptNumber: movement.MovID,
            receiptType: 'purchase',
            supplier: {
              supplierId: 'UNKNOWN',
              supplierCode: 'UNKNOWN',
              supplierName: 'Unknown Supplier'
            },
            dates: {
              expectedDate: movement.Timestamp,
              actualDate: movement.Timestamp
            },
            receivingLocation: {
              door: movement.BinFrom,
              locationId: movement.BinTo
            },
            lines: [{
              lineId: `RCPT-LINE-${movement.MovID}`,
              receiptId: `RCPT-${movement.Timestamp.getTime()}-${movement.BinTo}`,
              lineNumber: 1,
              product: {
                productId: movement.Product,
                productCode: movement.Product
              },
              quantities: {
                ordered: movement.Qty,
                expected: movement.Qty,
                received: movement.Qty,
                accepted: movement.Qty,
                rejected: 0,
                damaged: 0
              },
              locations: {
                temporary: movement.BinFrom,
                final: movement.BinTo
              },
              dates: {
                receivedDate: movement.Timestamp,
                putawayDate: movement.Timestamp
              },
              people: {
                receivedBy: movement.UserID,
                putawayBy: movement.UserID
              },
              cost: {
                unitCost: 0,
                totalCost: 0,
                currency: 'USD'
              },
              quality: {
                status: 'approved'
              },
              metadata: {
                sourceWMS: 'Movement-Based WMS',
                originalData: movement
              }
            }],
            status: 'posted',
            people: {
              receivedBy: movement.UserID
            },
            summary: {
              totalLines: 1,
              totalQuantity: movement.Qty
            },
            qualityControl: {
              required: false,
              completed: false,
              passed: true,
              quarantineCount: 0
            },
            metadata: {
              warehouse: context.config.warehouseId,
              sourceWMS: 'Movement-Based WMS',
              originalData: movement
            }
          }
          result.receipts.push(receipt)
          break

        case 'ADJUST':
          // This is an inventory adjustment
          const adj: InventoryAdjustment = {
            adjustmentId: `ADJ-${movement.MovID}`,
            externalAdjustmentId: movement.MovID,
            adjustmentNumber: movement.MovID,
            type: 'correction',
            reason: {
              code: 'CORR',
              description: 'System correction'
            },
            product: {
              productId: movement.Product,
              productCode: movement.Product
            },
            location: movement.BinFrom,
            quantities: {
              expected: movement.Qty < 0 ? Math.abs(movement.Qty) : 0,
              actual: movement.Qty < 0 ? 0 : movement.Qty,
              adjustment: movement.Qty
            },
            value: {
              unitCost: 0,
              totalCost: 0,
              currency: 'USD'
            },
            dates: {
              requestDate: movement.Timestamp,
              countDate: movement.Timestamp,
              postedDate: movement.Timestamp
            },
            approval: {
              requestedBy: movement.UserID,
              status: 'approved'
            },
            status: 'posted',
            people: {
              adjustedBy: movement.UserID
            },
            accounting: {
              postedToGL: false
            },
            metadata: {
              warehouse: context.config.warehouseId,
              sourceWMS: 'Movement-Based WMS',
              originalData: movement
            }
          }
          result.inventoryAdjustments.push(adj)
          break
      }
    }

    // Extract master data
    // Products, locations, users are extracted from movements
    const productSet = new Set<string>()
    const locationSet = new Set<string>()
    const userSet = new Set<string>()

    for (const mov of movements) {
      productSet.add(mov.Product)
      if (mov.BinFrom && mov.BinFrom !== 'RECEIPT' && mov.BinFrom !== 'ADJUST' && mov.BinFrom !== 'SHIP-01') {
        locationSet.add(mov.BinFrom)
      }
      if (mov.BinTo) {
        locationSet.add(mov.BinTo)
      }
      userSet.add(mov.UserID)
    }

    // Create products
    for (const productId of productSet) {
      result.products.push({
        productId,
        productCode: productId,
        description: productId,
        category: { level1: 'UNCATEGORIZED' },
        unitOfMeasure: 'EA',
        inventoryStatus: 'active',
        lotControl: false,
        expirationControl: false,
        serialControl: false,
        createdDate: new Date(),
        modifiedDate: new Date(),
        status: 'active',
        source: {
          wmsSystem: 'Movement-Based WMS',
          externalProductId: productId,
          importBatch: context.batchId
        }
      })
    }

    // Create locations
    for (const locationId of locationSet) {
      result.locations.push(createLocationFromCode(locationId, context))
    }

    // Create users
    for (const userId of userSet) {
      result.users.push({
        userId,
        username: userId,
        firstName: userId,
        lastName: userId,
        fullName: userId,
        role: 'picker',
        status: 'active',
        active: true,
        hireDate: new Date(),
        source: {
          wmsSystem: 'Movement-Based WMS',
          externalUserId: userId
        }
      })
    }

    return result
  }
}

// Helper functions
function mapOrderType(type: string): OrderType {
  const mapping: Record<string, OrderType> = {
    'SALES': 'sales-order',
    'TRANSFER': 'transfer-order',
    'RETURN': 'return-order'
  }
  return mapping[type] || 'sales-order'
}

function createLocationFromCode(code: string, context: TransformContext): Location {
  // Parse location code
  const parts = code.split('-')

  return {
    locationId: code,
    locationPath: `${context.config.warehouseId}/${code}`,
    warehouse: context.config.warehouseId,
    zone: parts[0] || 'UNKNOWN',
    aisle: parts[1],
    bay: parts[2],
    level: parts[3],
    locationType: 'racked',
    locationUsage: determineUsage(parts[0]),
    status: 'active',
    occupancy: 'partial',
    source: {
      wmsSystem: 'Movement-Based WMS',
      externalLocationId: code
    }
  }
}

function determineUsage(zone: string): LocationUsage {
  if (zone.startsWith('PICK')) return 'picking'
  if (zone.startsWith('BULK') || zone.startsWith('RESERVE')) return 'reserve'
  if (zone.startsWith('SHIP')) return 'shipping'
  if (zone.startsWith('RECEIPT') || zone.startsWith('DOCK')) return 'receiving'
  return 'picking'
}
```

---

## Example 2: Order-Based WMS

### Scenario
A modern WMS with explicit order headers and lines, plus movement tracking.

### WMS Export Structure

```sql
-- Order Headers
ORDERS table:
┌────────────┬───────────┬────────────┬──────────────┬──────────┬─────────────┬─────────────┐
│ ORDER_ID   │ ORDER_NUM │ ORDER_TYPE │ CUSTOMER_ID  │ PRIORITY │ REQUEST_DT  │ PROMISE_DT  │
├────────────┼───────────┼────────────┼──────────────┼──────────┼─────────────┼─────────────┤
│ 10001      │ SO-5001   │ SALES      │ C-001        │ HIGH     │ 2025-01-20  │ 2025-01-27  │
│ 10002      │ SO-5002   │ SALES      │ C-002        │ MED      │ 2025-01-21  │ 2025-01-28  │
└────────────┴───────────┴────────────┴──────────────┴──────────┴─────────────┴─────────────┘

-- Order Lines
ORDER_LINES table:
┌──────────┬───────────┬───────────┬───────────┬───────────┬────────────┬────────────┐
│ LINE_ID  │ ORDER_ID  │ PRODUCT   │ QTY_ORDER │ QTY_PICK  │ PICK_LOC    │ PICKER_ID  │
├──────────┼───────────┼───────────┼───────────┼───────────┼────────────┼────────────┤
│ 50001    │ 10001     │ PROD-001  │ 10        │ 10        │ A-01-01     │ U-001      │
│ 50002    │ 10001     │ PROD-002  │ 20        │ 18        │ A-02-03     │ U-001      │
│ 50003    │ 10002     │ PROD-003  │ 50        │ 0         │ B-05-01     │ NULL       │
└──────────┴───────────┴───────────┴───────────┴───────────┴────────────┴────────────┘

-- Pick Events (timestamps)
PICK_EVENTS table:
┌──────────┬───────────┬───────────┬─────────────┬─────────────┐
│ EVENT_ID │ LINE_ID   │ EVENT_CD  │ TIMESTAMP    │ USER_ID     │
├──────────┼───────────┼───────────┼─────────────┼─────────────┤
│ 90001    │ 50001     │ START     │ 2025-01-26  │ U-001       │
│ 90002    │ 50001     │ COMPLETE  │ 2025-01-26  │ U-001       │
│ 90003    │ 50002     │ START     │ 2025-01-26  │ U-001       │
│ 90004    │ 50002     │ SHORT     │ 2025-01-26  │ U-001       │
│ 90005    │ 50002     │ COMPLETE  │ 2025-01-26  │ U-001       │
└──────────┴───────────┴───────────┴─────────────┴─────────────┘
```

### Plugin Implementation

```typescript
const orderBasedWMSPlugin: ImportPlugin = {
  id: 'order-based-wms',
  name: 'Order-Based WMS Plugin',
  version: '1.0.0',
  wmsSystem: 'Modern Order-Based WMS',

  supportedFormats: ['xlsx', 'csv'],

  inputSchema: {
    files: [
      {
        name: 'ORDERS',
        required: true,
        description: 'Order headers',
        columns: [
          { name: 'ORDER_ID', type: 'string', required: true },
          { name: 'ORDER_NUM', type: 'string', required: true },
          { name: 'ORDER_TYPE', type: 'string', required: true },
          { name: 'CUSTOMER_ID', type: 'string', required: true },
          { name: 'PRIORITY', type: 'string', required: true },
          { name: 'REQUEST_DT', type: 'date', required: true },
          { name: 'PROMISE_DT', type: 'date', required: true }
        ]
      },
      {
        name: 'ORDER_LINES',
        required: true,
        description: 'Order line items',
        columns: [
          { name: 'LINE_ID', type: 'string', required: true },
          { name: 'ORDER_ID', type: 'string', required: true },
          { name: 'PRODUCT', type: 'string', required: true },
          { name: 'QTY_ORDER', type: 'number', required: true },
          { name: 'QTY_PICK', type: 'number', required: true },
          { name: 'PICK_LOC', type: 'string', required: true },
          { name: 'PICKER_ID', type: 'string', required: false }
        ]
      },
      {
        name: 'PICK_EVENTS',
        required: true,
        description: 'Pick event timestamps',
        columns: [
          { name: 'EVENT_ID', type: 'string', required: true },
          { name: 'LINE_ID', type: 'string', required: true },
          { name: 'EVENT_CD', type: 'string', required: true },
          { name: 'TIMESTAMP', type: 'date', required: true },
          { name: 'USER_ID', type: 'string', required: true }
        ]
      }
    ]
  },

  transform: async (input: WMSInputData, context: TransformContext) => {
    const orders = input.files['ORDERS']
    const lines = input.files['ORDER_LINES']
    const events = input.files['PICK_EVENTS']

    const result: WareflowData = {
      metadata: {
        importDate: new Date(),
        pluginId: 'order-based-wms',
        wmsSystem: 'Order-Based WMS',
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
      const wfOrder: Order = {
        orderId: order.ORDER_ID,
        externalOrderId: order.ORDER_ID,
        orderNumber: order.ORDER_NUM,
        orderType: mapOrderType(order.ORDER_TYPE),
        orderCategory: 'regular',
        priority: mapPriority(order.PRIORITY),
        orderStatus: 'confirmed',
        orderDate: order.REQUEST_DT,
        requestedDate: order.REQUEST_DT,
        promisedDate: order.PROMISE_DT,
        customer: {
          customerId: order.CUSTOMER_ID,
          customerName: order.CUSTOMER_ID
        },
        shippingAddress: {
          locationId: 'SHIPPING'
        },
        picking: {
          status: 'not-started'
        },
        summary: {
          totalLines: 0,
          totalQuantity: 0
        },
        progress: {
          linesPicked: 0,
          linesConfirmed: 0,
          linesShipped: 0
        },
        metadata: {
          sourceWarehouse: context.config.warehouseId,
          sourceWMS: 'Order-Based WMS',
          importBatch: context.batchId
        }
      }

      orderMap.set(order.ORDER_ID, wfOrder)
      result.orders.push(wfOrder)
    }

    // Transform picking lines
    const lineEventMap = new Map<string, typeof events>()

    for (const line of lines) {
      // Gather events for this line
      const lineEvents = events.filter(e => e.LINE_ID === line.LINE_ID)

      const startEvent = lineEvents.find(e => e.EVENT_CD === 'START')
      const completeEvent = lineEvents.find(e => e.EVENT_CD === 'COMPLETE')
      const shortEvent = lineEvents.find(e => e.EVENT_CD === 'SHORT')

      const pickLine: PickingLine = {
        lineId: line.LINE_ID,
        orderId: line.ORDER_ID,
        lineNumber: parseInt(line.LINE_ID.split('-')[1]),
        productId: line.PRODUCT,
        productCode: line.PRODUCT,
        quantities: {
          ordered: line.QTY_ORDER,
          allocated: line.QTY_PICK,
          picked: line.QTY_PICK,
          confirmed: shortEvent ? line.QTY_PICK : line.QTY_ORDER,
          cancelled: 0,
          short: shortEvent ? line.QTY_ORDER - line.QTY_PICK : 0,
          damaged: 0
        },
        locations: {
          source: line.PICK_LOC,
          destination: 'SHIPPING'
        },
        dates: {
          allocatedDate: startEvent?.TIMESTAMP,
          pickStartDate: startEvent?.TIMESTAMP,
          pickEndDate: completeEvent?.TIMESTAMP,
          confirmedDate: completeEvent?.TIMESTAMP
        },
        people: {
          pickerId: line.PICKER_ID
        },
        timing: {
          actualDuration: startEvent && completeEvent
            ? (completeEvent.TIMESTAMP.getTime() - startEvent.TIMESTAMP.getTime()) / 1000
            : undefined
        },
        status: completeEvent ? 'confirmed' : (shortEvent ? 'short' : 'pending'),
        allocationStatus: line.QTY_PICK > 0 ? 'allocated' : 'not-allocated',
        priority: orderMap.get(line.ORDER_ID)?.priority || 'medium',
        metadata: {
          sourceWMS: 'Order-Based WMS',
          originalData: { line, events: lineEvents }
        }
      }

      result.pickingLines.push(pickLine)

      // Update order summary
      const order = orderMap.get(line.ORDER_ID)
      if (order) {
        order.summary.totalLines++
        order.summary.totalQuantity += line.QTY_ORDER
        if (completeEvent) {
          order.progress.linesPicked++
          order.progress.linesConfirmed++
        }
      }
    }

    return result
  }
}

function mapPriority(priority: string): OrderPriority {
  const mapping: Record<string, OrderPriority> = {
    'CRITICAL': 'critical',
    'HIGH': 'high',
    'MED': 'medium',
    'LOW': 'low'
  }
  return mapping[priority] || 'medium'
}
```

---

## Example 3: Creating a Custom Plugin

### Scenario
A homegrown WMS with a completely custom format. This example shows the development workflow.

### Step 1: Analyze the Export

```python
# Sample export from custom WMS
{
  "warehouse_operations": {
    "date": "2025-01-26",
    "shift": "MORNING",
    "operations": [
      {
        "op_type": "picking",
        "op_id": "OP-001",
        "product": "PROD123",
        "from_loc": "ZONE-A-SHELF-01",
        "to_loc": "PACK-STATION-03",
        "qty": 25,
        "operator": "JOHN DOE",
        "time_start": "08:15:30",
        "time_end": "08:17:45",
        "order_ref": "ORD-2025-0126-001"
      },
      {
        "op_type": "replenishment",
        "op_id": "OP-002",
        "product": "PROD456",
        "from_loc": "BACK-ROOM-BIN-12",
        "to_loc": "ZONE-A-SHELF-02",
        "qty": 100,
        "operator": "JANE SMITH",
        "time_start": "08:20:00",
        "time_end": "08:25:30",
        "reason": "LOW_STOCK"
      }
    ]
  }
}
```

### Step 2: Create the Plugin

```typescript
const customWMSPlugin: ImportPlugin = {
  id: 'custom-json-wms',
  name: 'Custom JSON WMS Plugin',
  version: '1.0.0',
  wmsSystem: 'Custom Homegrown WMS',

  supportedFormats: ['json'],

  inputSchema: {
    files: [
      {
        name: 'warehouse_operations',
        required: true,
        description: 'JSON export of warehouse operations',
        columns: []  // JSON structure, not columns
      }
    ]
  },

  validate: (input: WMSInputData) => {
    const errors: ValidationResult[] = []

    const data = input.files['warehouse_operations']
    if (!data) {
      errors.push({
        file: 'warehouse_operations',
        error: 'Missing warehouse_operations file',
        suggestion: 'Export the JSON file from your WMS'
      })
      return errors
    }

    if (!data.operations || !Array.isArray(data.operations)) {
      errors.push({
        file: 'warehouse_operations',
        error: 'Invalid JSON structure',
        suggestion: 'Ensure "operations" array exists in JSON'
      })
    }

    return errors
  },

  transform: async (input: WMSInputData, context: TransformContext) => {
    const data = input.files['warehouse_operations']

    const result: WareflowData = {
      metadata: {
        importDate: new Date(),
        pluginId: 'custom-json-wms',
        wmsSystem: 'Custom WMS',
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

    // Parse date and shift
    const operationDate = parseDate(data.date)
    const shift = data.shift

    // Group operations by order
    const orderGroups = new Map<string, any[]>()

    for (const op of data.operations) {
      if (op.op_type === 'picking' && op.order_ref) {
        if (!orderGroups.has(op.order_ref)) {
          orderGroups.set(op.order_ref, [])
        }
        orderGroups.get(op.order_ref)!.push(op)
      }
    }

    // Create orders from picking operations
    for (const [orderRef, operations] of orderGroups) {
      const firstOp = operations[0]

      const order: Order = {
        orderId: orderRef,
        externalOrderId: orderRef,
        orderNumber: orderRef,
        orderType: 'sales-order',
        orderStatus: 'completed',
        orderDate: operationDate,
        requestedDate: operationDate,
        customer: {
          customerId: 'UNKNOWN',
          customerName: 'Unknown'
        },
        shippingAddress: {
          locationId: operations[0].to_loc
        },
        picking: {
          status: 'completed',
          pickerId: operations[0].operator
        },
        summary: {
          totalLines: operations.length,
          totalQuantity: operations.reduce((sum, op) => sum + op.qty, 0)
        },
        progress: {
          linesPicked: operations.length,
          linesConfirmed: operations.length,
          linesShipped: 0
        },
        metadata: {
          sourceWarehouse: context.config.warehouseId,
          sourceWMS: 'Custom WMS',
          shift,
          importBatch: context.batchId
        }
      }

      result.orders.push(order)

      // Create picking lines
      for (const op of operations) {
        const timeStart = parseTime(op.time_start, operationDate)
        const timeEnd = parseTime(op.time_end, operationDate)

        const pickLine: PickingLine = {
          lineId: op.op_id,
          orderId: orderRef,
          lineNumber: operations.indexOf(op) + 1,
          productId: op.product,
          productCode: op.product,
          quantities: {
            ordered: op.qty,
            allocated: op.qty,
            picked: op.qty,
            confirmed: op.qty,
            cancelled: 0,
            short: 0,
            damaged: 0
          },
          locations: {
            source: op.from_loc,
            destination: op.to_loc
          },
          dates: {
            allocatedDate: timeStart,
            pickStartDate: timeStart,
            pickEndDate: timeEnd,
            confirmedDate: timeEnd
          },
          people: {
            pickerId: op.operator
          },
          timing: {
            actualDuration: (timeEnd.getTime() - timeStart.getTime()) / 1000
          },
          status: 'confirmed',
          allocationStatus: 'allocated',
          priority: 'medium',
          metadata: {
            sourceWMS: 'Custom WMS',
            originalData: op
          }
        }

        result.pickingLines.push(pickLine)
      }
    }

    // Process replenishments
    for (const op of data.operations) {
      if (op.op_type === 'replenishment') {
        const timeStart = parseTime(op.time_start, operationDate)
        const timeEnd = parseTime(op.time_end, operationDate)

        const repl: Replenishment = {
          replenishmentId: op.op_id,
          externalReplenishmentId: op.op_id,
          type: 'manual',
          triggerReason: op.reason,
          movement: {
            productId: op.product,
            productCode: op.product,
            sourceLocation: op.from_loc,
            destinationLocation: op.to_loc
          },
          quantities: {
            requested: op.qty,
            moved: op.qty,
            remaining: 0
          },
          people: {
            movedBy: op.operator
          },
          dates: {
            requestDate: timeStart,
            startDate: timeStart,
            completedDate: timeEnd
          },
          timing: {
            actualDuration: (timeEnd.getTime() - timeStart.getTime()) / 1000
          },
          priority: 'medium',
          status: 'completed',
          metadata: {
            warehouse: context.config.warehouseId,
            zone: extractZone(op.to_loc),
            sourceWMS: 'Custom WMS',
            shift,
            originalData: op
          }
        }

        result.replenishments.push(repl)
      }
    }

    // Extract master data
    const products = new Set<string>()
    const locations = new Set<string>()
    const users = new Set<string>()

    for (const op of data.operations) {
      products.add(op.product)
      locations.add(op.from_loc)
      locations.add(op.to_loc)
      users.add(op.operator)
    }

    // Create products, locations, users
    // ... (same as previous examples)

    return result
  }
}

// Helper functions
function parseDate(dateStr: string): Date {
  // Parse YYYY-MM-DD
  const [year, month, day] = dateStr.split('-').map(Number)
  return new Date(year, month - 1, day)
}

function parseTime(timeStr: string, date: Date): Date {
  // Parse HH:MM:SS and combine with date
  const [hours, minutes, seconds] = timeStr.split(':').map(Number)
  const result = new Date(date)
  result.setHours(hours, minutes, seconds, 0)
  return result
}

function extractZone(location: string): string {
  // Extract zone from location code
  // "ZONE-A-SHELF-01" → "ZONE-A"
  const parts = location.split('-')
  return `${parts[0]}-${parts[1]}`
}
```

---

## Plugin Testing Checklist

Before deploying a plugin, verify:

- [ ] All required fields are mapped
- [ ] External IDs are preserved
- [ ] Dates are correctly parsed
- [ ] Quantities are accurate
- [ ] User IDs are captured
- [ ] Locations are properly structured
- [ ] Status logic is correct
- [ ] Original data is preserved in metadata
- [ ] Edge cases are handled (missing data, null values, etc.)
- [ ] Performance is acceptable (test with large datasets)

---

**Version**: 1.0.0
**Last Updated**: 2025-01-26
**Status**: Draft
