#!/usr/bin/env python
"""from_fusion_table.py: Select rows from a fusion table."""
import ee, datetime, csv, time
import ee.mapclient

def classify(img, trainfc):
    ## define param for trainClassifier. Use 30 meter per pixel, which is the native landsat resolution.
    vectorization_scale = 30
    ## define param for trainClassifier. Approximate the 1 meter scale in a 1 by 1 degree WGS square.
    ## 6378100 * 2 * 3.1415927 / 360 = 111318 - where 6378100 = approx.radius of earth, as a sphere (not spherecal)
    wgs_scale = vectorization_scale / 111318. # python needs to be told of real number type..

    ## classification method
    ## https://sites.google.com/site/earthengineapidocs/advanced-image-processing/classification
    classifier = img.trainClassifier(
      training_features=trainfc,
      training_property='classvalue',
      classifier_name='Cart',
      crs="EPSG:4326",                                       # not sure why fails if I don't add this
      crs_transform=[wgs_scale, 0, -180, 0, -wgs_scale, 90]  # not sure why fails if I don't add this
    )
    # print(classifier.getInfo()) # get a summary of the created trainClassifier

    ## Classify the input image
    classified = img.classify(classifier)
    return classified

def fc2csv(inputfc, outputname):
    # based on Tyler Erickson's 1/23 GEE Group python script
    startTime = datetime.datetime(2001, 1, 1)
    endTime = datetime.datetime(2001, 2, 1)
    ## Turn the result into a feature collection and export it. 
    ## my GEE "public" folder location: https://drive.google.com/folderview?id=0B1mDLYsP2TftfmxsSDNFd2hOVjBEazBHcFFkc3Y5RlZhVEx3akFSSnBuUFFoWGE5aWdRZ0U&usp=sharing
    taskParams = {
        'driveFolder' : 'GEE',
        'driveFileNamePrefix': outputname,
        'fileFormat' : 'CSV'
    };
    exportTable = ee.batch.Export.table(inputfc, 'export_fc', taskParams)
    exportTable.start()
    state = exportTable.status()['state']
    while state in ['READY', 'RUNNING']:
      print state + '...'
      time.sleep(1)
      state = exportTable.status()['state']
    print 'Done.', exportTable.status()

# =============================
if __name__ == '__main__':

    ee.Initialize()
    ee.mapclient.centerMap(-117.3, 33.0, 9) 

    ## Use my own study area - selected CA county subdivisions
    fc = ee.FeatureCollection('ft:1rY5cp4zTg5PtsjLPsmKPBTblFaJmzuXhxDfgmQGm','geometry')
    ee.mapclient.addToMap(fc, {'color': '0000FF'}) # test to see if it appears on the map

    ## A region of the image to train with - landcover classes including wildwire burned area
    train_fc = ee.FeatureCollection('ft:1nOsawIA_mWW-b0-OVHTlbU8Dzj4lIOZ3fdFL3dHB')
    ee.mapclient.addToMap(train_fc, {'color': '800080'}) # test to see if it appears on the map

    ## Input images are Landsat 7 after the 2007 December wildfire
    image1 = ee.Image('LE7_L1T_32DAY_RAW/20071219').select('B[1-5,7]') # bands B1-5 & 7

    ## the following are for avarage fall value - not a good idear: too many clouds
    #image0 = (ee.ImageCollection('LC8_L1T_8DAY_TOA').filterDate(datetime.datetime(2013, 9, 1),datetime.datetime(2013, 10, 31)))
    #image1 = image0.median()

    ## limit the analysis area for the study area (dong nai region) only
    image2 = image1.clip(fc)
    ee.mapclient.addToMap(image2) # test to see if it appears on the map
    # print(image2.getInfo()) # to get the image info

    ## call classify = supervised classification function
    classified = classify(image2, train_fc)
    ee.mapclient.addToMap(classified) # test to see if it appears on the map

    ## visualize the classified according to values
    PALETTE = ','.join([
    'ff4500', # burned area
    '006400', # forest
    '7fff00', # shrub, grass, savanah
    'ffd700', # croplands
    'aec3d4', # water
    'c0c0c0', # urban
    'ffffff' # snow and ice
    ])
    ee.mapclient.addToMap(classified, vis_params={'min':1, 'max':7, 'palette':PALETTE}) # test to see if it appears on the map
'''
    ## Produce a CSV file for all polygons, count classified cells (water class) within each zone (commune/villages)
    ## param: scale = 30 for landsat8 native 30m resolution?
    train_result = classified.reduceRegions(fc, ee.Reducer.count(), 30)
    ## export the zone counts as csv - will be saved in Google Drive
    fc2csv(train_result, 'classifyResult')
'''

