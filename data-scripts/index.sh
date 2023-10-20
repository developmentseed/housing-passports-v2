#!/usr/bin/env bash
set -e

# Calculate the Cartesian angle from a heading, accounting for directions to the right and left sides
mapillary_img_angles \
    --distance=0.000045 \
    --input_points_file="fixtures/points_inputs.geojson" \
    --output_points_file="fixtures/points_outputs_navi.geojson" \
    --output_lines_file="fixtures/lines_outputs_navi.geojson"
