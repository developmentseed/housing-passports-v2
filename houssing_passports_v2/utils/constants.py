from utils.utils import dic2d2dict

BUILDING_PROPS_DICT = {
    "complete": {
        "complete": 1,
        "incomplete": 2,
    },
    "condition": {
        "poor": 3,
        "fair": 4,
        "good": 5,
    },
    "material": {
        "mix-other-unclear": 6,
        "brick_or_cement-concrete_block": 7,
        "wood_polished": 8,
        "stone_with_mud-ashlar_with_lime_or_cement": 9,
        "corrugated_metal": 10,
        "wood_crude-plank": 11,
        "container-trailer": 12,
        "plaster": 19,
        "adobe": 20,
    },
    "security": {
        "secured": 13,
        "unsecured": 14,
    },
    "use": {
        "residential": 15,
        "critical_infrastructure": 16,
        "mixed": 17,
        "commercial": 18,
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
