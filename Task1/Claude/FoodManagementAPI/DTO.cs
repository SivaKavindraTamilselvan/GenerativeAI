// ============================================================
//  DTOs — Data Transfer Objects (Request & Response shapes)
// ============================================================
using System;
using System.Collections.Generic;
using System.ComponentModel.DataAnnotations;

namespace FoodManagementAPI.DTOs
{
    // ────────────── Category DTOs ──────────────
    public class CreateCategoryDto
    {
        [Required, MaxLength(100)]
        public string Name { get; set; } = string.Empty;
        [MaxLength(500)]
        public string? Description { get; set; }
    }

    public class UpdateCategoryDto : CreateCategoryDto { }

    // ────────────── Supplier DTOs ──────────────
    public class CreateSupplierDto
    {
        [Required, MaxLength(150)]
        public string Name        { get; set; } = string.Empty;
        [MaxLength(100)]
        public string? ContactName { get; set; }
        [EmailAddress, MaxLength(200)]
        public string? Email       { get; set; }
        [Phone, MaxLength(20)]
        public string? Phone       { get; set; }
        [MaxLength(500)]
        public string? Address     { get; set; }
    }

    public class UpdateSupplierDto : CreateSupplierDto { }

    // ────────────── FoodItem DTOs ──────────────
    public class CreateFoodItemDto
    {
        [Required, MaxLength(150)]
        public string  Name            { get; set; } = string.Empty;
        [MaxLength(500)]
        public string? Description     { get; set; }
        [Required, Range(1, int.MaxValue)]
        public int     CategoryId      { get; set; }
        public int?    SupplierId      { get; set; }
        [Required, MaxLength(50)]
        public string  Unit            { get; set; } = string.Empty;
        [Required, Range(0.01, double.MaxValue)]
        public decimal PricePerUnit    { get; set; }
        [Range(0, 10000)]
        public int?    CaloriesPerUnit { get; set; }
        public bool    IsPerishable    { get; set; }
        [MaxLength(500)]
        public string? ImageUrl        { get; set; }
    }

    public class UpdateFoodItemDto : CreateFoodItemDto { }

    public class FoodItemResponseDto
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
        public InventoryDto? Inventory  { get; set; }
    }

    // ────────────── Inventory DTOs ──────────────
    public class InventoryDto
    {
        public decimal   QuantityAvailable { get; set; }
        public decimal   MinimumThreshold  { get; set; }
        public DateTime? ExpiryDate        { get; set; }
        public string?   StorageLocation   { get; set; }
        public DateTime? LastRestockedAt   { get; set; }
        public bool      IsLowStock        { get; set; }
    }

    public class UpdateInventoryDto
    {
        [Required, Range(0, double.MaxValue)]
        public decimal   QuantityAvailable { get; set; }
        [Required, Range(0, double.MaxValue)]
        public decimal   MinimumThreshold  { get; set; }
        public DateTime? ExpiryDate        { get; set; }
        [MaxLength(100)]
        public string?   StorageLocation   { get; set; }
    }

    // ────────────── Stock Adjustment DTOs ──────────────
    public class StockAdjustmentDto
    {
        [Required]
        [RegularExpression("^(IN|OUT|ADJUSTMENT|WASTE)$",
            ErrorMessage = "MovementType must be IN, OUT, ADJUSTMENT, or WASTE.")]
        public string  MovementType { get; set; } = string.Empty;
        [Required, Range(0.01, double.MaxValue)]
        public decimal Quantity     { get; set; }
        [MaxLength(500)]
        public string? Reason       { get; set; }
        public int?    ReferenceId  { get; set; }
        [MaxLength(100)]
        public string? CreatedBy    { get; set; }
    }

    // ────────────── Order DTOs ──────────────
    public class CreateOrderDto
    {
        [MaxLength(1000)]
        public string?               Notes { get; set; }
        [Required, MinLength(1)]
        public List<CreateOrderItemDto> Items { get; set; } = new();
    }

    public class CreateOrderItemDto
    {
        [Required, Range(1, int.MaxValue)]
        public int     FoodItemId { get; set; }
        [Required, Range(0.01, double.MaxValue)]
        public decimal Quantity   { get; set; }
    }

    public class UpdateOrderStatusDto
    {
        [Required]
        [RegularExpression("^(Pending|Confirmed|Delivered|Cancelled)$",
            ErrorMessage = "Status must be Pending, Confirmed, Delivered, or Cancelled.")]
        public string Status { get; set; } = string.Empty;
    }

    // ────────────── Generic API Response ──────────────
    public class ApiResponse<T>
    {
        public bool    Success { get; set; }
        public string  Message { get; set; } = string.Empty;
        public T?      Data    { get; set; }
        public object? Errors  { get; set; }

        public static ApiResponse<T> Ok(T data, string message = "Success")
            => new() { Success = true, Message = message, Data = data };

        public static ApiResponse<T> Fail(string message, object? errors = null)
            => new() { Success = false, Message = message, Errors = errors };
    }
}