"""
Database objects for storing Housing Passports-relevant data

@author: Development Seed
"""
from collections import Counter

import numpy as np
from sqlalchemy import (Column, Integer, String, Float,
                        ForeignKey)
from sqlalchemy.dialects.postgresql.json import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from geoalchemy2 import Geometry

# Set the declarative base to prep creation of SQL classes
Base = declarative_base()


class Building(Base):
    """Geometry and properties for a single building

    Attributes
    ----------
    footprint: str
        Polygon outlining the building in WKT format.
    lon: float
        Longitude of building centroid
    lat: float
        Latitude of building centroid
    neighborhood: str
        Neighborhood where building exists
    building_metadata: str
        jsonb holding extra building metada (like parts or properties derived
        from ML)
    """

    __tablename__ = 'buildings'
    id = Column(Integer, primary_key=True)
    footprint = Column(Geometry('POLYGON'))
    lon = Column(Float)
    lat = Column(Float)
    neighborhood = Column(String)
    building_metadata = Column(JSONB)
    centroid = Column(Geometry('POINT'))

    # Add a relationship with the Detections class
    detections = relationship('Detection', back_populates='building')

    def __repr__(self):
        """Define string representation."""
        return f'<Building(n_detections={len(self.detections)}, neighborhood={self.neighborhood})>'


    def get_consolidated_properties(self, property_groups, prefix='sv_'):
        """Consolidate property detections into a single set of "true" property determinations.

        Determines the "true" building property for each category by summing up
        confidence values from different images that capture the same building.
        Returns this information (e.g., to set the building's metadata).

        Parameters
        ----------
        property_groups: dict
            Dictionary of property group with each key referring to a property
            (e.g., 'material', 'completeness', etc.) with a list of possible
            values (e.g., ['brick', 'metal', ...]).
        prefix: str
            Prefix to prepend to any properties stores in the metadata field.

        Returns
        -------
        metadata_updates: dict
            Dictionary containing distilled metadata concerning properties
        """

        metadata_updates = {}
        cumulative_conf = {}
        for det in self.detections:
            try:
                cumulative_conf[det.class_str] += det.confidence
            except KeyError:
                cumulative_conf[det.class_str] = det.confidence

        # Consolidate building properties
        for prop_group_key in property_groups.keys():
            group_conf = [cumulative_conf.get(prop, 0.)
                          for prop in property_groups[prop_group_key]]
            max_ind = np.argmax(group_conf)
            if group_conf[max_ind] > 0.:
                metadata_updates[prefix + prop_group_key] = \
                        property_groups[prop_group_key][max_ind]

        return metadata_updates


    def get_consolidated_parts(self, part_names, prefix='sv_'):
        """Consolidate part detections into a set of counts per image.

        Return this information (e.g., to set a building's metadata).

        Parameters
        ----------
        part_names: list
            List of building parts to consider
            (e.g., ['window', 'garage', 'etc.'])
        prefix: str
            Prefix to prepend to any json attributes stored in the metadata field.

        Returns
        -------
        metadata_updates: dict
            Dictionary containing distilled metadata concerning parts
        """

        # Get image ID for each detection that's in part_names
        parts_image_ids = {}
        metadata_updates = {}
        for det in [d for d in self.detections if d.class_str in part_names]:
            try:
                parts_image_ids[det.class_str].append(det.image_id)
            except KeyError:
                parts_image_ids[det.class_str] = [det.image_id]

        # Get max detections in a single image per part and set metadata
        for part_name in part_names:
            if part_name in parts_image_ids:
                counter = Counter(parts_image_ids[part_name])
                metadata_updates[prefix + part_name] = max(counter.values())

        return metadata_updates


class Image(Base):
    """Metadata on one image recorded from the car-mounted camera

    Attributes
    ----------
    lon: float
        Longitude of the car when image was taken
    lat: float
        Latitude of the car when image was taken
    heading: float
        Compass heading of car when image was taken
    neighborhood: str
        Neighborhood where frame was taken (part of filepath)
    subfolder: str
        Subfolder where image is stored (part of filepath)
    frame: str
        Frame number of the image (part of filename)
    cam: int
        Camera number (usually between 1-6)
    """

    __tablename__ = 'sv_images'
    id = Column(Integer, primary_key=True)

    lon, lat = Column(Float), Column(Float)
    heading = Column(Float)
    neighborhood = Column(String)
    subfolder = Column(String)
    frame = Column(String)
    image_fname = Column(String)
    cam = Column(Integer)
    
    # Add a relationship with the Detections class
    detections = relationship('Detection', back_populates='image')

    def __repr__(self):
        """Define string representation."""
        return f'<Image(neighborhood={self.neighborhood}, subfolder={self.subfolder}, frame={self.frame})>'


class Detection(Base):
    """Single detection within an image (i.e., on ML-derived bbox)

    Attributes
    ----------
    id: int
        The object UID for the relational DB
    building_id: int
        Building ID keyed to the Building table
    image_id: int
        Image ID keyed to the Image table
    x_min: float
        X value for top-left corner. Need underscore as `xmin` is a reserved
        name in PostGRES.
    y_min: float
        Y value for top-left corner
    x_max: float
        X value for bottom-right corner
    y_max: float
        Y value for bottom-right corner
    class_id: int
        Class integer
    class_str
        Class string
    confidence: float
        Model confidence in the prediction
    neighborhood: str
        Neighborhood of detection
    angle: float
        Heading of detection on interval [0, 360)
    detection_ray: str
        Linestring originating at car and eminating out towards detection.
        Should be in WKT format.
    """

    __tablename__ = 'sv_detections'
    id = Column(Integer, primary_key=True)
    building_id = Column(Integer, ForeignKey('buildings.id'))
    image_id = Column(Integer, ForeignKey('sv_images.id'))
    x_min, y_min = Column(Float), Column(Float)
    x_max, y_max = Column(Float), Column(Float)
    class_id, class_str = Column(Integer), Column(String)
    confidence = Column(Float)
    neighborhood = Column(String)
    angle = Column(Float)
    detection_ray = Column(Geometry('LINESTRING'))
    ray_buffer = Column(Geometry('POLYGON'))

    # Add a relationship with the Image and building class
    image = relationship('Image', back_populates='detections')
    building = relationship('Building', back_populates='detections')

    def __repr__(self):
        """Define string representation."""
        return f'<Detection(Class={self.class_str}, Confidence={self.confidence}, Image={self.image_id})>'
