import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, LineString
import math
import click

def create_line(row):
    start_point = row['geometry']
    angle_grades = row['heading[deg]']
    heading_angle_radians = math.radians(angle_grades)

    # Calculate the coordinates of the end point at a distance of 5 meters in the specified direction
    end_point_x = start_point.x + 0.00005 * math.cos(heading_angle_radians)
    end_point_y = start_point.y + 0.00005 * math.sin(heading_angle_radians)

    # Create a LineString geometry from the start and end points
    return LineString([start_point, Point(end_point_x, end_point_y)])

@click.command()
@click.option('--input', help='Input CSV file path', required=True)
@click.option('--output_points', help='Output Shapefile for points', required=True)
@click.option('--output_lines', help='Output Shapefile for lines', required=True)
def create_line_from_point(input, output_points, output_lines):
    # Read the CSV file as a DataFrame
    df = pd.read_csv(input)

    # Assuming the CSV contains columns 'latitude' and 'longitude' for point coordinates
    geometry = [Point(xy) for xy in zip(df['longitude[deg]'], df['latitude[deg]'])]
    gdf = gpd.GeoDataFrame(df, geometry=geometry)

    gdf.to_file(output_points, driver='ESRI Shapefile')

    # Create a new GeoDataFrame with the lines using the apply function
    lines_gdf = gpd.GeoDataFrame(geometry=gdf.apply(create_line, axis=1), crs=gdf.crs)

    # Save the GeoDataFrame with all the lines to a Shapefile
    lines_gdf.to_file(output_lines, driver='ESRI Shapefile')

if __name__ == '__main__':
    create_line_from_point()


# python post_processing/trajectory_angle.py \
# --input=files_for_db/padang_trajectory_fixed_1000.csv \
# --output_points=files_for_db/padang_trajectory_fixed_1000_points.shp \
# --output_lines=files_for_db/padang_trajectory_fixed_1000_lines.shp 
    
