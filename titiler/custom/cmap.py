"""
Titiler Custom colormaps.

Custom colormaps needs to be register in titiler/api/deps.py
e.g `cmap.register("above", custom_colormap.above_cmap)`

"""

# colors from https://daac.ornl.gov/ABOVE/guides/Annual_Landcover_ABoVE.html
above_cmap = {
    1: [58, 102, 24, 255],  # Evergreen Forest
    2: [100, 177, 41, 255],  # Deciduous Forest
    3: [177, 177, 41, 255],  # Shrubland
    4: [221, 203, 154, 255],  # Herbaceous
    5: [218, 203, 47, 255],  # Sparely Vegetated
    6: [177, 177, 177, 255],  # Barren
    7: [175, 255, 205, 255],  # Fen
    8: [239, 255, 192, 255],  # Bog
    9: [144, 255, 255, 255],  # Shallows/Littoral
    10: [29, 0, 250, 255],  # Water
}
