from utils.utils import dic2d2dict

BUILDING_PROPERTIES_BOX_CVAT = [
    "use",
    "material",
    "security",
    "condition",
    "complete",
]

BUILDING_PROPS_DICT = {
    "material": {
        "brick_or_cement-concrete_block": 1,
        "plaster": 2,
        "wood_polished": 3,
        "wood_crude-plank": 4,
        "adobe": 5,
        "corrugated_metal": 6,
        "stone_with_mud-ashlar_with_lime_or_cement": 7,
        "container-trailer": 8,
        "mix-other-unclear": 9,
    },
    "complete": {
        "complete": 10,
        "incomplete": 11,
    },
    "use": {
        "residential": 12,
        "mixed": 13,
        "commercial": 14,
        "critical_infrastructure": 15,
    },
    "security": {
        "unsecured": 16,
        "secured": 17,
    },
    "condition": {
        "fair": 18,
        "poor": 19,
        "good": 20,
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
