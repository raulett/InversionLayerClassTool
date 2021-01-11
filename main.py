from osgeo import ogr
import osr
import os

delta = 2

# Открываем входной слой с интерполяцией и выходной слой
inputDataFileName = r'F:\YandexDisk\Work\Projects\20201229_Ugohan_PointClassification\data\ugahan_inversion_data\ugahan_inversion_data_GK20.shp'
outputDataFileName = r'F:\YandexDisk\Work\Projects\20201229_Ugohan_PointClassification\data\outputData\\'

# Создаем драйвер для работы с SHP
shpDriver = ogr.GetDriverByName('ESRI Shapefile')
memDriver = ogr.GetDriverByName('MEMORY')

# Remove output shapefile if it already exists
if os.path.exists(outputDataFileName):
    shpDriver.DeleteDataSource(outputDataFileName)


# Открываем входной слой на запись чтобы собрать там пространственный индекс
inDS = shpDriver.Open(inputDataFileName, 1)
inDS.ExecuteSQL('CREATE SPATIAL INDEX ON {0}'.format('ugahan_inversion_data_GK20'))


# После создания пространственного индекса открываем слой датасорс для чтения
inDS = shpDriver.Open(inputDataFileName, 0)



# Создаем новый датасорс и открываем его на запись
outDS = shpDriver.CreateDataSource(outputDataFileName)
# out = shpDriver.Open(outputDataFileName, 1)


inputLayer = inDS.GetLayer('ugahan_inversion_data_GK20')
print("input layer spatial ref is: {}".format(inputLayer.GetSpatialRef()))
# srs = osr.SpatialReference().ImportFromEPSG(28420)
# Вытаскиваем проекцию из входного леера
inSrs = inputLayer.GetSpatialRef()

# Создаем временный слой для входных данных
tmpDS = memDriver.CreateDataSource('tmpData')
tmp = memDriver.Open('tmpData', 1)
tmpLayer = tmpDS.CopyLayer(inputLayer, 'tmpLayer', ['OVERWRITE=YES'])
# tmpLayer.CreateField(ogr.FieldDefn('level_Num', ogr.OFTInteger))
print("Field count in tmpLayer is: {}".format(tmpLayer.GetFeatureCount()))


inputLayerDefn = inputLayer.GetLayerDefn()
print("Field count in input Layer is: {}".format(inputLayerDefn.GetFieldCount()))

print('input layer feature count is: {}'.format(inputLayer.GetFeatureCount()))

# Создадим выходной слой для накопления данных
outLayer = outDS.CreateLayer('ugahan_inv_GK20_classyfy', srs = inSrs, geom_type = ogr.wkbPoint)

# Add input Layer Fields to the output Layer
for i in range(0, inputLayerDefn.GetFieldCount()):
    fieldDefn = inputLayerDefn.GetFieldDefn(i)
    outLayer.CreateField(fieldDefn)

# Добавляем поле целочисленное для номера уровня
outLayer.CreateField(ogr.FieldDefn('level_Num', ogr.OFTInteger))
outLayerDefn = outLayer.GetLayerDefn()
# print('Output layer definition is: {}'.format(outLayerDefn))

# # Корректировка полей X и Y
# xDefn = outLayerDefn.GetFieldDefn(0)
# width = xDefn.GetWidth() + 20
# precision = xDefn.GetPrecision() + 20
# xDefn.SetWidth(width)
# xDefn.SetPrecision(precision)
# flag = ogr.ALTER_WIDTH_PRECISION_FLAG
# outLayer.AlterFieldDefn(0, xDefn, flag)
# outLayer.AlterFieldDefn(1, xDefn, flag)



# Идея такая проходим по всем фичурам входного слоя. Для каждой фичи берем всех соседей которые в плане отстоят от
# нее небольшое количество (delta) метров. Будем считать что это и есть разные высоты одной и той же точки. Выбираем
# эти фичи в отдельный список, и удаляем их из входного слоя. Потом сортируем их по высоте и присваеваем им
# порядковый номер, и записываем его в новое поле аттрибутов. Потом добавляем их в выходной слой и сохраняем. Потом
# дальше итерируем.
#
# n=0
feat = tmpLayer.GetNextFeature()
while feat is not None:
    # outFeat = ogr.Feature(outLayerDefn)
    geom = feat.geometry()
    x = geom.GetX()
    y = geom.GetY()
    tmpLayer.SetSpatialFilterRect(x-delta, y-delta, x+delta, y+delta)
    filteredFeats = []
    for filtFeat in tmpLayer:
        filteredFeats.append(filtFeat)
    filteredFeats.sort(key= lambda result : result.GetField('Z'), reverse=True)
    counter = 0
    for ft in filteredFeats:
        outFeat = ogr.Feature(outLayerDefn)
        outFeat.SetGeometry(ft.geometry())
        outFeat.SetField('Z', ft.GetField('Z'))
        outFeat.SetField('mag', ft.GetField('mag'))
        outFeat.SetField('level_Num', counter)
        outFeat.SetField('X', float('{:.2f}'.format(ft.GetFieldAsDouble('X'))))
        outFeat.SetField('Y', float('{:.2f}'.format(ft.GetFieldAsDouble('Y'))))
        counter += 1
        outLayer.CreateFeature(outFeat)
        tmpLayer.DeleteFeature(ft.GetFID())

    tmpLayer.SetSpatialFilter(None)
    tmpLayer.ResetReading()
    feat = tmpLayer.GetNextFeature()


print('out layer feature count is: {}'.format(outLayer.GetFeatureCount()))
outDS.SyncToDisk()
inDS.Destroy()
tmpDS.Destroy()
outDS.Destroy()
