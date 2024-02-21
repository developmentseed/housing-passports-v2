import os
import click
import geopandas as gpd
import pandas as pd

@click.command()
@click.argument('folder_path', type=click.Path(exists=True))
@click.argument('output_shapefile', type=click.Path())
def merge_geojson_to_shapefile(folder_path, output_shapefile):
    """Merge GeoJSON files into a single shapefile."""
    geojson_files = [os.path.join(folder_path, file) for file in os.listdir(folder_path) if file.endswith('.geojson')]
    gdfs = [gpd.read_file(file) for file in geojson_files]
    merged_gdf = gpd.GeoDataFrame(pd.concat(gdfs, ignore_index=True))
    merged_gdf.to_file(output_shapefile, driver='ESRI Shapefile')

if __name__ == "__main__":
    merge_geojson_to_shapefile()
