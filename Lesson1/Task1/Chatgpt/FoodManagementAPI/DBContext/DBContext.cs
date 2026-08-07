using FoodManagementAPI.Models;
using Microsoft.EntityFrameworkCore;

namespace FoodManagementAPI.Data;

public class FoodDbContext : DbContext
{
    public FoodDbContext(DbContextOptions<FoodDbContext> options) : base(options)
    {
    }

    public DbSet<Food> Foods { get; set; }
    public DbSet<Category> Categories { get; set; }
}