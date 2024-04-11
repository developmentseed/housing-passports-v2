#  Housing Passports triangulation algorithm

The Housing Passports project is a collaboration with the World Bank to improve housing resilience.

The WB is interested in detecting specific construction features within geotagged street view imagery. Their goal is to find building features that are potentially dangerous during earthquakes, high winds, floods, etc. A good example is their initial push in Guatemala where they were looking for "soft story" buildings; These are 2+ level structures that have large windows or garage doors on the ground floor -- the large openings correspond to a high risk that the building will collapse and pancake during earthquakes. Other features could include incomplete construction, age of the building, construction material, etc.

Their hope is to detect dangerous features in street view images using ML, extract the specific locations of these features, and then rely on local groups to deploy fixes or improvements.

[Document to attach predictions to building footprints](COMPILING_FILE_INTO_DB.md)