using FoodManagementAPI.DTOs;
using FoodManagementAPI.Models;
using FoodManagementAPI.Repositories;

namespace FoodManagementAPI.Services;

public class FoodService : IFoodService
{
    private readonly IFoodRepository foodRepository;

    public FoodService(IFoodRepository foodRepository)
    {
        this.foodRepository = foodRepository;
    }

    public List<FoodResponseDto> GetAllFoods()
    {
        return foodRepository.GetAllFoods()
            .Select(f => new FoodResponseDto
            {
                FoodId = f.FoodId,
                FoodName = f.FoodName,
                Price = f.Price,
                Quantity = f.Quantity,
                IsAvailable = f.IsAvailable,
                CategoryName = f.Category!.CategoryName
            })
            .ToList();
    }

    public FoodResponseDto? GetFoodById(int id)
    {
        var food = foodRepository.GetFoodById(id);

        if (food == null)
            return null;

        return new FoodResponseDto
        {
            FoodId = food.FoodId,
            FoodName = food.FoodName,
            Price = food.Price,
            Quantity = food.Quantity,
            IsAvailable = food.IsAvailable,
            CategoryName = food.Category!.CategoryName
        };
    }

    public void AddFood(FoodCreateDto dto)
    {
        var food = new Food
        {
            FoodName = dto.FoodName,
            Price = dto.Price,
            Quantity = dto.Quantity,
            CategoryId = dto.CategoryId,
            IsAvailable = dto.Quantity > 0
        };

        foodRepository.AddFood(food);
    }

    public bool UpdateFood(int id, FoodCreateDto dto)
    {
        var food = foodRepository.GetFoodById(id);

        if (food == null)
            return false;

        food.FoodName = dto.FoodName;
        food.Price = dto.Price;
        food.Quantity = dto.Quantity;
        food.CategoryId = dto.CategoryId;
        food.IsAvailable = dto.Quantity > 0;

        foodRepository.UpdateFood(food);
        return true;
    }

    public bool DeleteFood(int id)
    {
        var food = foodRepository.GetFoodById(id);

        if (food == null)
            return false;

        foodRepository.DeleteFood(food);
        return true;
    }
}