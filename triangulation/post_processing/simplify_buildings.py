import click
import geopandas as gpd
from shapely.ops import unary_union

@click.command()
@click.argument('input_shapefile', type=click.Path(exists=True))
@click.argument('output_shapefile', type=click.Path())
def simplify_and_remove_overlap(input_shapefile, output_shapefile):
    """Simplify polygons and remove overlaps in a shapefile."""
    # Read the input shapefile
    gdf = gpd.read_file(input_shapefile)

    # Check if the input GeoDataFrame has a 'geometry' column
    if 'geometry' not in gdf.columns:
        raise ValueError("The input GeoDataFrame must have a 'geometry' column.")

    # Perform unary union to merge overlapping polygons
    unified_geom = unary_union(gdf['geometry'])

    # Create a new GeoDataFrame with simplified and non-overlapping polygons
    simplified_gdf = gpd.GeoDataFrame(geometry=[unified_geom])

    # Save the result to a new shapefile
    simplified_gdf.to_file(output_shapefile)

if __name__ == "__main__":
    simplify_and_remove_overlap()

# python post_processing/simplify_buildings.py files_for_db/shp_building/shp_building.shp files_for_db/shp_building/building_simplified.shp
