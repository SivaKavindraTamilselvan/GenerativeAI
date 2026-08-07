// ============================================================
//  DATA ACCESS LAYER — Npgsql + Dapper (PostgreSQL)
// ============================================================
using System;
using System.Collections.Generic;
using System.Data;
using System.Linq;
using System.Threading.Tasks;
using Dapper;
using FoodManagementAPI.DTOs;
using FoodManagementAPI.Models;
using Microsoft.Extensions.Configuration;
using Npgsql;

namespace FoodManagementAPI.Data
{
    // ──────────────────────────────────────────────────────────
    //  AppDbContext — opens Npgsql connections
    // ──────────────────────────────────────────────────────────
    public class AppDbContext
    {
        private readonly string _connectionString;

        public AppDbContext(IConfiguration configuration)
        {
            _connectionString = configuration.GetConnectionString("DefaultConnection")
                ?? throw new InvalidOperationException("Connection string 'DefaultConnection' not found.");
        }

        public IDbConnection CreateConnection() => new NpgsqlConnection(_connectionString);
    }

    // ──────────────────────────────────────────────────────────
    //  FoodRepository — all database operations via PostgreSQL functions
    // ──────────────────────────────────────────────────────────
    public class FoodRepository
    {
        private readonly AppDbContext _db;
        public FoodRepository(AppDbContext db) => _db = db;

        // ─────────────── CATEGORIES ───────────────

        public async Task<IEnumerable<Category>> GetAllCategoriesAsync()
        {
            using var conn = _db.CreateConnection();
            return await conn.QueryAsync<Category>(
                "SELECT category_id, name, description, created_at, updated_at, is_active " +
                "FROM categories WHERE is_active = TRUE ORDER BY name");
        }

        public async Task<Category?> GetCategoryByIdAsync(int id)
        {
            using var conn = _db.CreateConnection();
            return await conn.QueryFirstOrDefaultAsync<Category>(
                "SELECT * FROM categories WHERE category_id = @Id AND is_active = TRUE",
                new { Id = id });
        }

        public async Task<int> CreateCategoryAsync(CreateCategoryDto dto)
        {
            using var conn = _db.CreateConnection();
            return await conn.ExecuteScalarAsync<int>(
                "INSERT INTO categories (name, description) VALUES (@Name, @Description) RETURNING category_id",
                new { dto.Name, dto.Description });
        }

        public async Task<bool> UpdateCategoryAsync(int id, UpdateCategoryDto dto)
        {
            using var conn = _db.CreateConnection();
            var rows = await conn.ExecuteAsync(
                "UPDATE categories SET name = @Name, description = @Description WHERE category_id = @Id",
                new { dto.Name, dto.Description, Id = id });
            return rows > 0;
        }

        public async Task<bool> DeleteCategoryAsync(int id)
        {
            using var conn = _db.CreateConnection();
            var rows = await conn.ExecuteAsync(
                "UPDATE categories SET is_active = FALSE WHERE category_id = @Id",
                new { Id = id });
            return rows > 0;
        }

        // ─────────────── SUPPLIERS ───────────────

        public async Task<IEnumerable<Supplier>> GetAllSuppliersAsync()
        {
            using var conn = _db.CreateConnection();
            return await conn.QueryAsync<Supplier>(
                "SELECT * FROM suppliers WHERE is_active = TRUE ORDER BY name");
        }

        public async Task<Supplier?> GetSupplierByIdAsync(int id)
        {
            using var conn = _db.CreateConnection();
            return await conn.QueryFirstOrDefaultAsync<Supplier>(
                "SELECT * FROM suppliers WHERE supplier_id = @Id AND is_active = TRUE",
                new { Id = id });
        }

        public async Task<int> CreateSupplierAsync(CreateSupplierDto dto)
        {
            using var conn = _db.CreateConnection();
            return await conn.ExecuteScalarAsync<int>(@"
                INSERT INTO suppliers (name, contact_name, email, phone, address)
                VALUES (@Name, @ContactName, @Email, @Phone, @Address)
                RETURNING supplier_id",
                new { dto.Name, dto.ContactName, dto.Email, dto.Phone, dto.Address });
        }

        public async Task<bool> UpdateSupplierAsync(int id, UpdateSupplierDto dto)
        {
            using var conn = _db.CreateConnection();
            var rows = await conn.ExecuteAsync(@"
                UPDATE suppliers SET name = @Name, contact_name = @ContactName,
                    email = @Email, phone = @Phone, address = @Address
                WHERE supplier_id = @Id",
                new { dto.Name, dto.ContactName, dto.Email, dto.Phone, dto.Address, Id = id });
            return rows > 0;
        }

        public async Task<bool> DeleteSupplierAsync(int id)
        {
            using var conn = _db.CreateConnection();
            var rows = await conn.ExecuteAsync(
                "UPDATE suppliers SET is_active = FALSE WHERE supplier_id = @Id",
                new { Id = id });
            return rows > 0;
        }

        // ─────────────── FOOD ITEMS ───────────────

        public async Task<IEnumerable<FoodItemResponseDto>> GetAllFoodItemsAsync()
        {
            using var conn = _db.CreateConnection();
            // Call PostgreSQL function — returns typed rows
            var rows = await conn.QueryAsync<dynamic>("SELECT * FROM fn_get_all_food_items()");
            return rows.Select(MapToFoodItemResponse);
        }

        public async Task<FoodItemResponseDto?> GetFoodItemByIdAsync(int id)
        {
            using var conn = _db.CreateConnection();
            var row = await conn.QueryFirstOrDefaultAsync<dynamic>(
                "SELECT * FROM fn_get_food_item_by_id(@FoodItemId)",
                new { FoodItemId = id });
            return row is null ? null : MapToFoodItemResponse(row);
        }

        public async Task<int> CreateFoodItemAsync(CreateFoodItemDto dto)
        {
            using var conn = _db.CreateConnection();
            return await conn.ExecuteScalarAsync<int>(@"
                SELECT fn_create_food_item(
                    @Name, @Description, @CategoryId, @SupplierId,
                    @Unit, @PricePerUnit, @CaloriesPerUnit, @IsPerishable, @ImageUrl)",
                new {
                    dto.Name, dto.Description, dto.CategoryId, dto.SupplierId,
                    dto.Unit, dto.PricePerUnit, dto.CaloriesPerUnit, dto.IsPerishable, dto.ImageUrl
                });
        }

        public async Task UpdateFoodItemAsync(int id, UpdateFoodItemDto dto)
        {
            using var conn = _db.CreateConnection();
            await conn.ExecuteAsync(@"
                SELECT fn_update_food_item(
                    @FoodItemId, @Name, @Description, @CategoryId, @SupplierId,
                    @Unit, @PricePerUnit, @CaloriesPerUnit, @IsPerishable, @ImageUrl)",
                new {
                    FoodItemId = id, dto.Name, dto.Description, dto.CategoryId, dto.SupplierId,
                    dto.Unit, dto.PricePerUnit, dto.CaloriesPerUnit, dto.IsPerishable, dto.ImageUrl
                });
        }

        public async Task DeleteFoodItemAsync(int id)
        {
            using var conn = _db.CreateConnection();
            await conn.ExecuteAsync(
                "SELECT fn_delete_food_item(@FoodItemId)", new { FoodItemId = id });
        }

        public async Task<IEnumerable<FoodItemResponseDto>> GetLowStockItemsAsync()
        {
            using var conn = _db.CreateConnection();
            var rows = await conn.QueryAsync<dynamic>("SELECT * FROM fn_get_low_stock_items()");
            return rows.Select(MapToFoodItemResponse);
        }

        public async Task<IEnumerable<FoodItemResponseDto>> GetExpiringItemsAsync(int daysAhead = 7)
        {
            using var conn = _db.CreateConnection();
            var rows = await conn.QueryAsync<dynamic>(
                "SELECT * FROM fn_get_expiring_items(@DaysAhead)", new { DaysAhead = daysAhead });
            return rows.Select(MapToFoodItemResponse);
        }

        // ─────────────── INVENTORY ───────────────

        public async Task UpdateInventoryAsync(int foodItemId, UpdateInventoryDto dto)
        {
            using var conn = _db.CreateConnection();
            await conn.ExecuteAsync(@"
                SELECT fn_update_inventory(
                    @FoodItemId, @QuantityAvailable, @MinimumThreshold,
                    @ExpiryDate, @StorageLocation)",
                new {
                    FoodItemId = foodItemId, dto.QuantityAvailable,
                    dto.MinimumThreshold, dto.ExpiryDate, dto.StorageLocation
                });
        }

        public async Task AdjustStockAsync(int foodItemId, StockAdjustmentDto dto)
        {
            using var conn = _db.CreateConnection();
            await conn.ExecuteAsync(@"
                SELECT fn_adjust_stock(
                    @FoodItemId, @MovementType, @Quantity,
                    @Reason, @ReferenceId, @CreatedBy)",
                new {
                    FoodItemId = foodItemId, dto.MovementType, dto.Quantity,
                    dto.Reason, dto.ReferenceId, dto.CreatedBy
                });
        }

        public async Task<IEnumerable<StockMovement>> GetStockMovementsAsync(int foodItemId)
        {
            using var conn = _db.CreateConnection();
            return await conn.QueryAsync<StockMovement>(
                "SELECT * FROM stock_movements WHERE food_item_id = @FoodItemId ORDER BY moved_at DESC",
                new { FoodItemId = foodItemId });
        }

        // ─────────────── ORDERS ───────────────

        public async Task<IEnumerable<Order>> GetAllOrdersAsync()
        {
            using var conn = _db.CreateConnection();
            return await conn.QueryAsync<Order>(
                "SELECT * FROM vw_order_summary ORDER BY order_date DESC");
        }

        public async Task<Order?> GetOrderByIdAsync(int id)
        {
            using var conn = _db.CreateConnection();
            const string sql = @"
                SELECT o.order_id, o.order_number, o.order_date, o.status, o.total_amount, o.notes,
                       oi.order_item_id, oi.food_item_id, f.name AS food_item_name,
                       oi.quantity, oi.unit_price, oi.total_price
                FROM   orders o
                LEFT JOIN order_items oi ON oi.order_id = o.order_id
                LEFT JOIN food_items  f  ON f.food_item_id = oi.food_item_id
                WHERE  o.order_id = @OrderId";

            var orderDict = new Dictionary<int, Order>();
            await conn.QueryAsync<Order, OrderItem, Order>(sql,
                (order, item) =>
                {
                    if (!orderDict.TryGetValue(order.OrderId, out var cached))
                        orderDict[order.OrderId] = cached = order;
                    if (item?.OrderItemId > 0) cached.Items.Add(item);
                    return cached;
                },
                new { OrderId = id }, splitOn: "order_item_id");

            return orderDict.Values.FirstOrDefault();
        }

        public async Task<(int orderId, string orderNumber)> CreateOrderAsync(CreateOrderDto dto)
        {
            using var conn = _db.CreateConnection();
            conn.Open();
            using var tx = conn.BeginTransaction();
            try
            {
                var result = await conn.QueryFirstAsync<dynamic>(
                    "SELECT * FROM fn_create_order(@Notes)", new { dto.Notes }, tx);

                int orderId       = (int)result.new_order_id;
                string orderNumber = (string)result.order_number;

                foreach (var item in dto.Items)
                    await conn.ExecuteAsync(
                        "SELECT fn_add_order_item(@OrderId, @FoodItemId, @Quantity)",
                        new { OrderId = orderId, item.FoodItemId, item.Quantity }, tx);

                tx.Commit();
                return (orderId, orderNumber);
            }
            catch
            {
                tx.Rollback();
                throw;
            }
        }

        public async Task UpdateOrderStatusAsync(int orderId, string status)
        {
            using var conn = _db.CreateConnection();
            await conn.ExecuteAsync(
                "SELECT fn_update_order_status(@OrderId, @Status)",
                new { OrderId = orderId, Status = status });
        }

        // ─────────────── DASHBOARD ───────────────

        public async Task<DashboardSummary> GetDashboardSummaryAsync()
        {
            using var conn = _db.CreateConnection();
            return await conn.QueryFirstAsync<DashboardSummary>(
                "SELECT * FROM fn_get_dashboard_summary()");
        }

        // ─────────────── PRIVATE HELPERS ───────────────

        private static FoodItemResponseDto MapToFoodItemResponse(dynamic r)
        {
            var dto = new FoodItemResponseDto
            {
                FoodItemId      = (int)r.food_item_id,
                Name            = (string)r.name,
                Description     = r.description != null ? (string)r.description : null,
                CategoryId      = (int)r.category_id,
                CategoryName    = (string)r.category_name,
                Unit            = (string)r.unit,
                PricePerUnit    = (decimal)r.price_per_unit,
                IsPerishable    = (bool)r.is_perishable,
                ImageUrl        = r.image_url != null ? (string)r.image_url : null,
            };

            if (r.supplier_id != null) dto.SupplierId = (int)r.supplier_id;
            if (r.supplier_name != null) dto.SupplierName = (string)r.supplier_name;
            if (r.calories_per_unit != null) dto.CaloriesPerUnit = (int)r.calories_per_unit;

            // Inventory sub-object (may not be present in all function results)
            try
            {
                dto.Inventory = new InventoryDto
                {
                    QuantityAvailable = (decimal)r.quantity_available,
                    MinimumThreshold  = (decimal)r.minimum_threshold,
                    ExpiryDate        = r.expiry_date != null ? (DateTime?)r.expiry_date : null,
                    StorageLocation   = r.storage_location != null ? (string)r.storage_location : null,
                    IsLowStock        = (decimal)r.quantity_available <= (decimal)r.minimum_threshold
                };
            }
            catch { /* some query results don't include inventory columns */ }

            return dto;
        }
    }
}