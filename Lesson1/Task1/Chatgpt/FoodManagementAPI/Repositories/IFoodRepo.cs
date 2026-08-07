using FoodManagementAPI.Models;

namespace FoodManagementAPI.Repositories;

public interface IFoodRepository
{
    List<Food> GetAllFoods();
    Food? GetFoodById(int id);
    void AddFood(Food food);
    void UpdateFood(Food food);
    void DeleteFood(Food food);
}