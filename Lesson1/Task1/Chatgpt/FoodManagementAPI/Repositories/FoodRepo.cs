using FoodManagementAPI.Data;
using FoodManagementAPI.Models;
using Microsoft.EntityFrameworkCore;

namespace FoodManagementAPI.Repositories;

public class FoodRepository : IFoodRepository
{
    private readonly FoodDbContext context;

    public FoodRepository(FoodDbContext context)
    {
        this.context = context;
    }

    public List<Food> GetAllFoods()
    {
        return context.Foods
            .Include(f => f.Category)
            .ToList();
    }

    public Food? GetFoodById(int id)
    {
        return context.Foods
            .Include(f => f.Category)
            .FirstOrDefault(f => f.FoodId == id);
    }

    public void AddFood(Food food)
    {
        context.Foods.Add(food);
        context.SaveChanges();
    }

    public void UpdateFood(Food food)
    {
        context.Foods.Update(food);
        context.SaveChanges();
    }

    public void DeleteFood(Food food)
    {
        context.Foods.Remove(food);
        context.SaveChanges();
    }
}