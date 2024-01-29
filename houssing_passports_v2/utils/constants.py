from utils.utils import dic2d2dict

BUILDING_PROPERTIES_BOX_CVAT = [
    "box_attr_building_condition",
    "box_attr_building_material",
    "box_attr_building_use",
    "box_attr_building_security",
    "box_attr_building_completeness",
]

BUILDING_PROPS_DICT = {
    "materials": {
        "brick_or_cement-concrete_block": 1,
        "plaster": 2,
        "wood_polished": 3,
        "wood_crude-plank": 4,
        "adobe": 5,
        "corrugated_metal": 6,
        "stone_with_mud-ashlar_with_lime_or_cement": 7,
        "container-trailer": 8,
        "plant_material": 9,
        "mix-other-unclear": 10,
    },
    "completeness": {
        "complete": 11,
        "incomplete": 12,
    },
    "use": {
        "residential": 13,
        "mixed": 14,
        "commercial": 15,
        "critical_infrastructure": 16,
    },
    "security": {
        "unsecured": 17,
        "secured": 18,
    },
    "condition": {
        "fair": 19,
        "poor": 20,
        "good": 21,
    },
}
BUILDING_PARTS_DICT = {
    "parts": {"window": 1, "door": 2, "garage": 3, "disaster_mitigation": 4}
}

BUILDING_PROPS = dic2d2dict(BUILDING_PROPS_DICT)


BUILDING_PARTS = dic2d2dict(BUILDING_PARTS_DICT)

IMAGE_SIDE = {
    "right": 3,
    "left": 1,
}
