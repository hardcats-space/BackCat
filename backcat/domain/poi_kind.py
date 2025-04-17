from enum import StrEnum


class POIKind(StrEnum):
    GENERAL = "general"  # general poi, displayed as (!)

    # natural features
    BEACH = "beach"
    LAKE = "lake"
    RIVER = "river"
    WATERFALL = "waterfall"
    VIEWPOINT = "viewpoint"
    CANYON = "canyon"
    CAVE = "cave"

    # facilities
    CAMPFIRE = "campfire"  # Campfire ring/Fire pit
    PICNIC = "picnic"  # Picnic area/Tables
    RESTROOM = "restroom"  # Restrooms/Bathroom facilities
    WATER = "water"  # Water source/Spigot
    FOOD = "food"  # Foodcourt or cafes
    TRASH = "trash"  # Trash-bin
    PIER = "pier"  # Fishing pier
    DOCK = "dock"  # Boat launch/Dock
    PARKING = "parking"  # Parking
    INFO = "info"  # Information center

    # activities
    SWIM = "swim"
    FISH = "fish"
    BOAT = "boat"
    CLIMBING = "climbing"  # Rock climbing
    PLAYGROUND = "playground"  # Children playground
