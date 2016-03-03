from osgeo import ogr, osr
import os
import thread

countyBoundariesDriver = ogr.GetDriverByName('ESRI Shapefile')
countyBoundariesDataSet = countyBoundariesDriver.Open('./county_boundaries/county_boundaries.shp')
countyBoundariesLayer = countyBoundariesDataSet.GetLayer('county_boundaries')

countyList = { 'names': [] }
county = countyBoundariesLayer.GetNextFeature()
countyNames = ['ADAMS', 'ARMSTRONG', 'BEDFORD', 'BLAIR', 'CAMBRIA', 'CAMERON', 'CARBON', 'CLARION', 'CLEARFIELD', 'COLUMBIA', 'CRAWFORD', 'CUMBERLAND', 'ELK', 'ERIE', 'FAYETTE', 'FULTON', 'GREENE', 'HUNTINGDON', 'JEFFERSON', 'JUNIATA', 'LAWRENCE', 'LEHIGH', 'LUZERNE', 'LYCOMING', 'MCKEAN', 'MERCER', 'MONROE', 'MONTOUR', 'NORTHUMBERLAND', 'PERRY', 'PIKE', 'POTTER', 'SCHUYLKILL', 'SOMERSET', 'SUSQUEHANNA', 'SULLIVAN', 'TIOGA', 'UNION', 'WARREN', 'WAYNE', 'WESTMORELAND', 'WYOMING', 'ALLEGHENY', 'BUCKS', 'BRADFORD', 'CENTRE', 'CLINTON', 'FOREST', 'LACKAWANNA', 'LANCASTER', 'LEBANON', 'MIFFLIN', 'PHILADELPHIA', 'VENANGO']

def getCounty(pt):
    countyBoundariesLayer.SetSpatialFilter(pt)
    if countyBoundariesLayer.GetFeatureCount() != 1:
        return { 'name': 'outside_of_counties', 'FIPS': 'NULL' }
    else:
        county = countyBoundariesLayer.GetNextFeature()
        try:
            ply = county.GetGeometryRef()
        except AttributeError:
            print county.GetField(1)
        if ply.Contains(pt):
            return { 'name': county.GetField(1), 'FIPS': county.GetField(3) }

inDriver = ogr.GetDriverByName('OpenFileGDB')
outDriver = ogr.GetDriverByName('ESRI Shapefile')

# get the input layer
inDataSet = inDriver.Open('./PAMAP_Building/CountyBuildings.gdb')
inLayer = inDataSet.GetLayer('BuildingPoint')

# input SpatialReference
inSpatialRef = inLayer.GetSpatialRef()

# output SpatialReference
outSpatialRef = osr.SpatialReference()
outSpatialRef.ImportFromEPSG(4326)

# create the CoordinateTransformation
coordTrans = osr.CoordinateTransformation(inSpatialRef, outSpatialRef)


outputShapefiles = {}
for i in range(0, len(countyNames)):
    newpath = './data/' + countyNames[i]
    if not os.path.exists(newpath):
        os.makedirs(newpath)
    out_shp = newpath + '/' + countyNames[i] + '_addresses.shp'
    if os.path.exists(out_shp):
        outDriver.DeleteDataSource(out_shp)
    out_ds = outDriver.CreateDataSource(out_shp)
    out_ly = out_ds.CreateLayer('addresses', geom_type=ogr.wkbPoint)
    outputShapefiles[countyNames[i]] = { 'path': out_shp, 'DataSet': out_ds, 'Layer': out_ly }

OCP = './data/outside_of_counties/'
if not os.path.exists(OCP):
    os.makedirs(OCP)
OCPShp = OCP + '/outside_of_counties.shp'
if os.path.exists(OCPShp):
    outDriver.DeleteDataSource(OCPShp)
OCPDataSet = outDriver.CreateDataSource(OCPShp)
OCPLayer = OCPDataSet.CreateLayer('addresses', geom_type=ogr.wkbPoint)
outputShapefiles['outside_of_counties'] = { 'path': OCPShp, 'DataSet': OCPDataSet, 'Layer': OCPLayer }

# add fields
inLayerDefn = inLayer.GetLayerDefn()
for i in range(0, inLayerDefn.GetFieldCount()):
    for n in range(0, len(countyNames)):
        fieldDefn = inLayerDefn.GetFieldDefn(i)
        outputShapefiles[countyNames[n]]['Layer'].CreateField(fieldDefn)

# COF : County FIPS Code
# FNAME : Building or Landmark Name
# SAN : Street Number
# PRD : Street Directional Prefix
# STP : Street Type Prefix
# STN : Street Name
# STS : Street Type Suffix
# MCN : Unofficial Municipal Name
# ADD_DATE : Date Feature Added
# EDIT_DATE : Date Feature Editted


# loop through the input features
count = 1
inFeature = inLayer.GetNextFeature()
while inFeature:
    # get the input geometry
    geom = inFeature.GetGeometryRef()
    # reproject the geometry
    geom.Transform(coordTrans)

    countyInfo = getCounty(geom)

    if countyInfo and ( countyInfo['name'] in countyNames or countyInfo['name'] == 'outside_of_counties'):
        outLayer = outputShapefiles[countyInfo['name']]['Layer']
        outLayerDefn = outLayer.GetLayerDefn()

        # create a new feature
        outFeature = ogr.Feature(outLayerDefn)
        # set the geometry and attribute
        outFeature.SetGeometry(geom)
        #print inFeature.GetField(7) + inFeature.GetField(8)
        for i in range(0, outLayerDefn.GetFieldCount()):
            outFeature.SetField(outLayerDefn.GetFieldDefn(i).GetNameRef(), inFeature.GetField(i))
        # add the feature to the shapefile
        outLayer.CreateFeature(outFeature)
        # destroy the features and get the next input feature
        outFeature.Destroy()
        inFeature.Destroy()
        if count % 1000 == 0:
            print count
        inFeature = inLayer.GetNextFeature()
        count = count + 1

# close the shapefiles
inDataSet.Destroy()
for n in range(0, len(countyNames)):
    outputShapefiles[countyNames[i]]['DataSet'].Destroy()

print 'Total Addresses: ' + count
