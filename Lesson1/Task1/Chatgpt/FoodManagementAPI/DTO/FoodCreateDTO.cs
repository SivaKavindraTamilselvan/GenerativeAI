using System.ComponentModel.DataAnnotations;

namespace FoodManagementAPI.DTOs;

public class FoodCreateDto
{
    [Required]
    public string FoodName { get; set; } = string.Empty;

    [Range(1, 100000)]
    public decimal Price { get; set; }

    [Range(0, 10000)]
    public int Quantity { get; set; }

    [Required]
    public int CategoryId { get; set; }
}