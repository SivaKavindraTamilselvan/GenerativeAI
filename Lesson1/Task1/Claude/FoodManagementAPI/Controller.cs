// ============================================================
//  CONTROLLERS — ASP.NET Core Web API Endpoints
// ============================================================
using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using FoodManagementAPI.Data;
using FoodManagementAPI.DTOs;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using Microsoft.Extensions.Logging;

namespace FoodManagementAPI.Controllers
{
    // ════════════════════════════════════════════
    //  DASHBOARD
    // ════════════════════════════════════════════
    [ApiController]
    [Route("api/[controller]")]
    [Produces("application/json")]
    public class DashboardController : ControllerBase
    {
        private readonly FoodRepository _repo;
        public DashboardController(FoodRepository repo) => _repo = repo;

        /// <summary>Returns KPI summary for the dashboard.</summary>
        [HttpGet]
        [ProducesResponseType(StatusCodes.Status200OK)]
        public async Task<IActionResult> GetSummary()
        {
            var summary = await _repo.GetDashboardSummaryAsync();
            return Ok(ApiResponse<object>.Ok(summary, "Dashboard summary loaded."));
        }
    }

    // ════════════════════════════════════════════
    //  CATEGORIES
    // ════════════════════════════════════════════
    [ApiController]
    [Route("api/[controller]")]
    [Produces("application/json")]
    public class CategoriesController : ControllerBase
    {
        private readonly FoodRepository _repo;
        private readonly ILogger<CategoriesController> _log;
        public CategoriesController(FoodRepository repo, ILogger<CategoriesController> log)
            => (_repo, _log) = (repo, log);

        /// <summary>Get all active categories.</summary>
        [HttpGet]
        public async Task<IActionResult> GetAll()
        {
            var data = await _repo.GetAllCategoriesAsync();
            return Ok(ApiResponse<object>.Ok(data));
        }

        /// <summary>Get category by ID.</summary>
        [HttpGet("{id:int}")]
        [ProducesResponseType(StatusCodes.Status200OK)]
        [ProducesResponseType(StatusCodes.Status404NotFound)]
        public async Task<IActionResult> GetById(int id)
        {
            var item = await _repo.GetCategoryByIdAsync(id);
            if (item is null) return NotFound(ApiResponse<object>.Fail($"Category {id} not found."));
            return Ok(ApiResponse<object>.Ok(item));
        }

        /// <summary>Create a new category.</summary>
        [HttpPost]
        [ProducesResponseType(StatusCodes.Status201Created)]
        [ProducesResponseType(StatusCodes.Status400BadRequest)]
        public async Task<IActionResult> Create([FromBody] CreateCategoryDto dto)
        {
            if (!ModelState.IsValid) return BadRequest(ApiResponse<object>.Fail("Validation failed.", ModelState));
            var id = await _repo.CreateCategoryAsync(dto);
            return CreatedAtAction(nameof(GetById), new { id },
                ApiResponse<object>.Ok(new { CategoryId = id }, "Category created."));
        }

        /// <summary>Update a category.</summary>
        [HttpPut("{id:int}")]
        [ProducesResponseType(StatusCodes.Status200OK)]
        [ProducesResponseType(StatusCodes.Status404NotFound)]
        public async Task<IActionResult> Update(int id, [FromBody] UpdateCategoryDto dto)
        {
            if (!ModelState.IsValid) return BadRequest(ApiResponse<object>.Fail("Validation failed.", ModelState));
            var ok = await _repo.UpdateCategoryAsync(id, dto);
            if (!ok) return NotFound(ApiResponse<object>.Fail($"Category {id} not found."));
            return Ok(ApiResponse<object>.Ok(null, "Category updated."));
        }

        /// <summary>Soft-delete a category.</summary>
        [HttpDelete("{id:int}")]
        [ProducesResponseType(StatusCodes.Status200OK)]
        [ProducesResponseType(StatusCodes.Status404NotFound)]
        public async Task<IActionResult> Delete(int id)
        {
            var ok = await _repo.DeleteCategoryAsync(id);
            if (!ok) return NotFound(ApiResponse<object>.Fail($"Category {id} not found."));
            return Ok(ApiResponse<object>.Ok(null, "Category deleted."));
        }
    }

    // ════════════════════════════════════════════
    //  SUPPLIERS
    // ════════════════════════════════════════════
    [ApiController]
    [Route("api/[controller]")]
    [Produces("application/json")]
    public class SuppliersController : ControllerBase
    {
        private readonly FoodRepository _repo;
        public SuppliersController(FoodRepository repo) => _repo = repo;

        [HttpGet]
        public async Task<IActionResult> GetAll()
            => Ok(ApiResponse<object>.Ok(await _repo.GetAllSuppliersAsync()));

        [HttpGet("{id:int}")]
        public async Task<IActionResult> GetById(int id)
        {
            var item = await _repo.GetSupplierByIdAsync(id);
            if (item is null) return NotFound(ApiResponse<object>.Fail($"Supplier {id} not found."));
            return Ok(ApiResponse<object>.Ok(item));
        }

        [HttpPost]
        public async Task<IActionResult> Create([FromBody] CreateSupplierDto dto)
        {
            if (!ModelState.IsValid) return BadRequest(ApiResponse<object>.Fail("Validation failed.", ModelState));
            var id = await _repo.CreateSupplierAsync(dto);
            return CreatedAtAction(nameof(GetById), new { id },
                ApiResponse<object>.Ok(new { SupplierId = id }, "Supplier created."));
        }

        [HttpPut("{id:int}")]
        public async Task<IActionResult> Update(int id, [FromBody] UpdateSupplierDto dto)
        {
            if (!ModelState.IsValid) return BadRequest(ApiResponse<object>.Fail("Validation failed.", ModelState));
            var ok = await _repo.UpdateSupplierAsync(id, dto);
            if (!ok) return NotFound(ApiResponse<object>.Fail($"Supplier {id} not found."));
            return Ok(ApiResponse<object>.Ok(null, "Supplier updated."));
        }

        [HttpDelete("{id:int}")]
        public async Task<IActionResult> Delete(int id)
        {
            var ok = await _repo.DeleteSupplierAsync(id);
            if (!ok) return NotFound(ApiResponse<object>.Fail($"Supplier {id} not found."));
            return Ok(ApiResponse<object>.Ok(null, "Supplier deleted."));
        }
    }

    // ════════════════════════════════════════════
    //  FOOD ITEMS
    // ════════════════════════════════════════════
    [ApiController]
    [Route("api/[controller]")]
    [Produces("application/json")]
    public class FoodItemsController : ControllerBase
    {
        private readonly FoodRepository _repo;
        private readonly ILogger<FoodItemsController> _log;
        public FoodItemsController(FoodRepository repo, ILogger<FoodItemsController> log)
            => (_repo, _log) = (repo, log);

        /// <summary>Get all active food items with inventory data.</summary>
        [HttpGet]
        public async Task<IActionResult> GetAll()
            => Ok(ApiResponse<object>.Ok(await _repo.GetAllFoodItemsAsync()));

        /// <summary>Get a specific food item by ID.</summary>
        [HttpGet("{id:int}")]
        public async Task<IActionResult> GetById(int id)
        {
            var item = await _repo.GetFoodItemByIdAsync(id);
            if (item is null) return NotFound(ApiResponse<object>.Fail($"Food item {id} not found."));
            return Ok(ApiResponse<object>.Ok(item));
        }

        /// <summary>Get food items that are below minimum stock threshold.</summary>
        [HttpGet("low-stock")]
        public async Task<IActionResult> GetLowStock()
            => Ok(ApiResponse<object>.Ok(await _repo.GetLowStockItemsAsync(), "Low stock items retrieved."));

        /// <summary>Get perishable items expiring within N days (default 7).</summary>
        [HttpGet("expiring")]
        public async Task<IActionResult> GetExpiring([FromQuery] int days = 7)
            => Ok(ApiResponse<object>.Ok(await _repo.GetExpiringItemsAsync(days), $"Items expiring in {days} days."));

        /// <summary>Create a new food item (auto-creates a blank inventory record).</summary>
        [HttpPost]
        public async Task<IActionResult> Create([FromBody] CreateFoodItemDto dto)
        {
            if (!ModelState.IsValid) return BadRequest(ApiResponse<object>.Fail("Validation failed.", ModelState));
            var id = await _repo.CreateFoodItemAsync(dto);
            return CreatedAtAction(nameof(GetById), new { id },
                ApiResponse<object>.Ok(new { FoodItemId = id }, "Food item created."));
        }

        /// <summary>Update an existing food item.</summary>
        [HttpPut("{id:int}")]
        public async Task<IActionResult> Update(int id, [FromBody] UpdateFoodItemDto dto)
        {
            if (!ModelState.IsValid) return BadRequest(ApiResponse<object>.Fail("Validation failed.", ModelState));
            await _repo.UpdateFoodItemAsync(id, dto);
            return Ok(ApiResponse<object>.Ok(null, "Food item updated."));
        }

        /// <summary>Soft-delete a food item.</summary>
        [HttpDelete("{id:int}")]
        public async Task<IActionResult> Delete(int id)
        {
            await _repo.DeleteFoodItemAsync(id);
            return Ok(ApiResponse<object>.Ok(null, "Food item deleted."));
        }

        // ── Inventory sub-resource ──

        /// <summary>Update inventory details for a food item.</summary>
        [HttpPut("{id:int}/inventory")]
        public async Task<IActionResult> UpdateInventory(int id, [FromBody] UpdateInventoryDto dto)
        {
            if (!ModelState.IsValid) return BadRequest(ApiResponse<object>.Fail("Validation failed.", ModelState));
            await _repo.UpdateInventoryAsync(id, dto);
            return Ok(ApiResponse<object>.Ok(null, "Inventory updated."));
        }

        /// <summary>Adjust stock level (IN / OUT / ADJUSTMENT / WASTE).</summary>
        [HttpPost("{id:int}/stock-adjust")]
        public async Task<IActionResult> AdjustStock(int id, [FromBody] StockAdjustmentDto dto)
        {
            if (!ModelState.IsValid) return BadRequest(ApiResponse<object>.Fail("Validation failed.", ModelState));
            await _repo.AdjustStockAsync(id, dto);
            return Ok(ApiResponse<object>.Ok(null, "Stock adjusted."));
        }

        /// <summary>Get stock movement history for a food item.</summary>
        [HttpGet("{id:int}/stock-movements")]
        public async Task<IActionResult> GetStockMovements(int id)
            => Ok(ApiResponse<object>.Ok(await _repo.GetStockMovementsAsync(id)));
    }

    // ════════════════════════════════════════════
    //  ORDERS
    // ════════════════════════════════════════════
    [ApiController]
    [Route("api/[controller]")]
    [Produces("application/json")]
    public class OrdersController : ControllerBase
    {
        private readonly FoodRepository _repo;
        private readonly ILogger<OrdersController> _log;
        public OrdersController(FoodRepository repo, ILogger<OrdersController> log)
            => (_repo, _log) = (repo, log);

        /// <summary>Get all orders (summary view).</summary>
        [HttpGet]
        public async Task<IActionResult> GetAll()
            => Ok(ApiResponse<object>.Ok(await _repo.GetAllOrdersAsync()));

        /// <summary>Get a specific order with all line items.</summary>
        [HttpGet("{id:int}")]
        public async Task<IActionResult> GetById(int id)
        {
            var order = await _repo.GetOrderByIdAsync(id);
            if (order is null) return NotFound(ApiResponse<object>.Fail($"Order {id} not found."));
            return Ok(ApiResponse<object>.Ok(order));
        }

        /// <summary>Create a new order and its line items (transactional).</summary>
        [HttpPost]
        public async Task<IActionResult> Create([FromBody] CreateOrderDto dto)
        {
            if (!ModelState.IsValid) return BadRequest(ApiResponse<object>.Fail("Validation failed.", ModelState));
            var (orderId, orderNumber) = await _repo.CreateOrderAsync(dto);
            return CreatedAtAction(nameof(GetById), new { id = orderId },
                ApiResponse<object>.Ok(new { OrderId = orderId, OrderNumber = orderNumber }, "Order created."));
        }

        /// <summary>Update the status of an order (Pending → Confirmed → Delivered / Cancelled).</summary>
        [HttpPatch("{id:int}/status")]
        public async Task<IActionResult> UpdateStatus(int id, [FromBody] UpdateOrderStatusDto dto)
        {
            if (!ModelState.IsValid) return BadRequest(ApiResponse<object>.Fail("Validation failed.", ModelState));
            await _repo.UpdateOrderStatusAsync(id, dto.Status);
            return Ok(ApiResponse<object>.Ok(null, $"Order status updated to {dto.Status}."));
        }
    }
}