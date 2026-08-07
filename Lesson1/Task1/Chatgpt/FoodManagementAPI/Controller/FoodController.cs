using FoodManagementAPI.DTOs;
using FoodManagementAPI.Services;
using Microsoft.AspNetCore.Mvc;

namespace FoodManagementAPI.Controllers;

[Route("api/[controller]")]
[ApiController]
public class FoodsController : ControllerBase
{
    private readonly IFoodService foodService;

    public FoodsController(IFoodService foodService)
    {
        this.foodService = foodService;
    }

    [HttpGet]
    public ActionResult<List<FoodResponseDto>> GetAllFoods()
    {
        return Ok(foodService.GetAllFoods());
    }

    [HttpGet("{id}")]
    public ActionResult<FoodResponseDto> GetFoodById(int id)
    {
        var food = foodService.GetFoodById(id);

        if (food == null)
            return NotFound("Food not found");

        return Ok(food);
    }

    [HttpPost]
    public IActionResult AddFood(FoodCreateDto dto)
    {
        foodService.AddFood(dto);
        return Ok("Food added successfully");
    }

    [HttpPut("{id}")]
    public IActionResult UpdateFood(int id, FoodCreateDto dto)
    {
        var result = foodService.UpdateFood(id, dto);

        if (!result)
            return NotFound("Food not found");

        return Ok("Food updated successfully");
    }

    [HttpDelete("{id}")]
    public IActionResult DeleteFood(int id)
    {
        var result = foodService.DeleteFood(id);

        if (!result)
            return NotFound("Food not found");

        return Ok("Food deleted successfully");
    }
}