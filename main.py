from osgeo import ogr
import osr

inputDataFileName = r'F:\YandexDisk\Work\Projects\20201229_Ugohan_PointClassification\data\ugahan_inversion_data\ugahan_inversion_data_GK20.shp'
outputDataFileName = r'F:\YandexDisk\Work\Projects\20201229_Ugohan_PointClassification\data\outputData\ugohanClassInvertion.shp'

driver = ogr.GetDriverByName('ESRI Shapefile')

inDS = ogr.Open(inputDataFileName, 0)
outDS = driver.CreateDataSource(outputDataFileName)

srs = osr.SpatialReference().ImportFromEPSG(28420)

layer = inDS.GetLayer('ugahan_inversion_data_GK20')
print(layer.GetFeatureCount())

for feat in layer:
    featuresOnPos = []
    geom = feat.geometry()