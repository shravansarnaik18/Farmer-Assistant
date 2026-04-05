def get_crop_suggestions(season, soil):
    
    data = {
        ("Kharif", "Black Soil"): ["Cotton", "Soybean", "Tur"],
        ("Kharif", "Loamy Soil"): ["Rice", "Maize", "Groundnut"],
        ("Kharif", "Clay Soil"): ["Rice", "Sugarcane"],

        ("Rabi", "Black Soil"): ["Wheat", "Gram", "Sunflower"],
        ("Rabi", "Loamy Soil"): ["Wheat", "Mustard", "Barley"],
        ("Rabi", "Clay Soil"): ["Wheat", "Peas"],

        ("Zaid", "Black Soil"): ["Watermelon", "Cucumber"],
        ("Zaid", "Loamy Soil"): ["Muskmelon", "Vegetables"],
        ("Zaid", "Clay Soil"): ["Fodder crops"]
    }

    return data.get((season, soil), [])