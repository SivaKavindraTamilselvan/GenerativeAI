using FoodManagementAPI.DTOs;

namespace FoodManagementAPI.Services;

public interface IFoodService
{
    List<FoodResponseDto> GetAllFoods();
    FoodResponseDto? GetFoodById(int id);
    void AddFood(FoodCreateDto dto);
    bool UpdateFood(int id, FoodCreateDto dto);
    bool DeleteFood(int id);
}