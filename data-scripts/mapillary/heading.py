"""
Script for Generating Visual Lines from Points to Illustrate Mapillary Headings
"""
import fire
from utils.index import read_geojson, write_geojson
import math
import copy


def compass_to_cartesian(compass_degrees):
    # Subtracting the compass degrees from 90 to get the equivalent Cartesian angle,
    # and then taking the modulus to keep the result between 0 and 360.
    cartesian_degrees = (90 - compass_degrees) % 360
    return round(cartesian_degrees, 2)


def point_to_line(start_point, angle_degrees, distance):
    x_start, y_start = start_point
    angle_radians = math.radians(angle_degrees)
    deltaX = distance * math.cos(angle_radians)
    deltaY = distance * math.sin(angle_radians)
    x_end = x_start + deltaX
    y_end = y_start + deltaY
    return (x_end, y_end)


def to_lineString(p1, p2, props):
    props_ = copy.deepcopy(props)
    return {
        "type": "Feature",
        "geometry": {"type": "LineString", "coordinates": [p1, p2]},
        "properties": props_,
    }


def create_line_features(features, distance):
    """Create line features from point features, including heading, left, and right sides."""

    ## Headding
    lines_features = []

    for feature in features:
        # cartesian_angle = compass_to_cartesian(feature["properties"]["compass_angle"])
        cartesian_angle=feature["properties"]["compass_angle"]
        start_point = feature["geometry"]["coordinates"]

        ######## Headding
        headding_end_point = point_to_line(start_point, cartesian_angle, distance)
        props_ahead = {"towards": "ahead", "angle": cartesian_angle}
        headding_side = to_lineString(start_point, headding_end_point, props_ahead)
        lines_features.append(headding_side)

        ######## Left side
        ## Make sure that the anngle is less that 360 degrees
        cartesian_left_angle = round((cartesian_angle + 90) % 360, 2)
        left_end_point = point_to_line(start_point, cartesian_left_angle, distance)
        props_left = {"towards": "left", "angle": cartesian_left_angle}
        left_side = to_lineString(start_point, left_end_point, props_left)
        lines_features.append(left_side)

        ######## Right side
        # Make positive angle in case it is negative
        cartesian_right_angle = round((cartesian_angle - 90 + 360) % 360, 2)
        ritgh_end_point = point_to_line(start_point, cartesian_right_angle, distance)
        props_right = {"towards": "right", "angle": cartesian_right_angle}
        right_side = to_lineString(start_point, ritgh_end_point, props_right)
        lines_features.append(right_side)

        ## Add props to feature point
        feature["properties"]["cartesian_angle_right"] = cartesian_right_angle
        feature["properties"]["cartesian_angle"] = cartesian_angle
        feature["properties"]["cartesian_angle_left"] = cartesian_left_angle

    return features, lines_features


def main(
    distance=0.00005,
    input_points_file="fixtures/points_inputs.geojson",
    output_points_file="fixtures/points_outputs_navi.geojson",
    output_lines_file="fixtures/lines_outputs_navi.geojson",
):
    features = read_geojson(input_points_file)
    points_outputs, lines_outputs = create_line_features(features, distance)
    write_geojson(output_lines_file, lines_outputs)
    write_geojson(output_points_file, points_outputs)


if __name__ == "__main__":
    fire.Fire(main)
