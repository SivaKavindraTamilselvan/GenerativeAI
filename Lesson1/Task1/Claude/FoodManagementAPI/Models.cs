// ============================================================
//  MODELS — Domain entities matching the SQL tables
// ============================================================
using System;
using System.Collections.Generic;

namespace FoodManagementAPI.Models
{
    // ──────────────────── Category ────────────────────
    public class Category
    {
        public int    CategoryId  { get; set; }
        public string Name        { get; set; } = string.Empty;
        public string? Description { get; set; }
        public DateTime CreatedAt { get; set; }
        public DateTime UpdatedAt { get; set; }
        public bool   IsActive    { get; set; } = true;
    }

    // ──────────────────── Supplier ────────────────────
    public class Supplier
    {
        public int    SupplierId  { get; set; }
        public string Name        { get; set; } = string.Empty;
        public string? ContactName { get; set; }
        public string? Email       { get; set; }
        public string? Phone       { get; set; }
        public string? Address     { get; set; }
        public DateTime CreatedAt  { get; set; }
        public bool   IsActive     { get; set; } = true;
    }

    // ──────────────────── FoodItem ────────────────────
    public class FoodItem
    {
        public int      FoodItemId      { get; set; }
        public string   Name            { get; set; } = string.Empty;
        public string?  Description     { get; set; }
        public int      CategoryId      { get; set; }
        public string   CategoryName    { get; set; } = string.Empty;
        public int?     SupplierId      { get; set; }
        public string?  SupplierName    { get; set; }
        public string   Unit            { get; set; } = string.Empty;
        public decimal  PricePerUnit    { get; set; }
        public int?     CaloriesPerUnit { get; set; }
        public bool     IsPerishable    { get; set; }
        public string?  ImageUrl        { get; set; }
        public DateTime CreatedAt       { get; set; }
        public DateTime UpdatedAt       { get; set; }
        public bool     IsActive        { get; set; } = true;
        public Inventory? Inventory     { get; set; }
    }

    // ──────────────────── Inventory ───────────────────
    public class Inventory
    {
        public int      InventoryId        { get; set; }
        public int      FoodItemId         { get; set; }
        public decimal  QuantityAvailable  { get; set; }
        public decimal  MinimumThreshold   { get; set; }
        public DateTime? ExpiryDate        { get; set; }
        public string?  StorageLocation    { get; set; }
        public DateTime? LastRestockedAt   { get; set; }
        public DateTime UpdatedAt          { get; set; }
        public bool     IsLowStock         => QuantityAvailable <= MinimumThreshold;
    }

    // ──────────────────── Order ───────────────────────
    public class Order
    {
        public int       OrderId     { get; set; }
        public string    OrderNumber { get; set; } = string.Empty;
        public DateTime  OrderDate   { get; set; }
        public string    Status      { get; set; } = "Pending";
        public decimal   TotalAmount { get; set; }
        public string?   Notes       { get; set; }
        public DateTime  CreatedAt   { get; set; }
        public DateTime  UpdatedAt   { get; set; }
        public List<OrderItem> Items { get; set; } = new();
    }

    // ──────────────────── OrderItem ───────────────────
    public class OrderItem
    {
        public int     OrderItemId  { get; set; }
        public int     OrderId      { get; set; }
        public int     FoodItemId   { get; set; }
        public string  FoodItemName { get; set; } = string.Empty;
        public decimal Quantity     { get; set; }
        public decimal UnitPrice    { get; set; }
        public decimal TotalPrice   { get; set; }
    }

    // ──────────────────── StockMovement ───────────────
    public class StockMovement
    {
        public int     MovementId   { get; set; }
        public int     FoodItemId   { get; set; }
        public string  MovementType { get; set; } = string.Empty;  // IN/OUT/ADJUSTMENT/WASTE
        public decimal Quantity     { get; set; }
        public string? Reason       { get; set; }
        public int?    ReferenceId  { get; set; }
        public DateTime MovedAt     { get; set; }
        public string? CreatedBy    { get; set; }
    }

    // ──────────────────── Dashboard ───────────────────
    public class DashboardSummary
    {
        public int     TotalFoodItems  { get; set; }
        public int     TotalCategories { get; set; }
        public int     TotalSuppliers  { get; set; }
        public int     PendingOrders   { get; set; }
        public int     TodayOrders     { get; set; }
        public decimal TotalRevenue    { get; set; }
        public int     LowStockCount   { get; set; }
        public int     ExpiringCount   { get; set; }
    }
}