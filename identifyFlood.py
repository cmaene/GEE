#!/usr/bin/env python
"""from_fusion_table.py: Select rows from a fusion table."""
import ee, datetime, csv, time
import ee.mapclient

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

    ## example: https://ee-api.appspot.com/42582c90a626755098dce6d3274fe679
    ## sums up flood cells by commune/village using time-series image collection
    ## Use my own Vietnamese Communes boundaries - limit for Dong Nai region only (PROC=713)
    fc = ee.FeatureCollection('ft:1V-cFoyZ74cySom_0v8o0nY9E7BHFDgfj_JMACvmf').filter(ee.Filter().eq('FIRST_PROC', 713))

    # ee.mapclient.centerMap(107.2, 11.1, 10) # use only for checking
    # ee.mapclient.addToMap(fc, {'color': '800080'}) # test to see if it appears on the map
 
    ## Input images are MODIS - how about a week amount right after the 2006 flooding period..
    collection = (ee.ImageCollection('MYD09GA')
                .filterDate(datetime.datetime(2006, 9, 2),
                            datetime.datetime(2006, 9, 9)).select('sur_refl_b07'))

    ## the function being iterated over the time-series image collection..
    def floodic(image):
        ## threshold = 0.08
        ## gt = "greater than" evaluation method
        b7gt = image.multiply(0.0001).gt(0.08)
        ## zone summary statistics
        ## param: scale = 30 for landsat8 native 30m resolution?
        return b7gt.reduceRegions(fc, ee.Reducer.sum(), 1000)

    ## "map" will run "floodic" function over images in the image collection
    ## "flatten" was necessary
    floodFc = collection.map(floodic).flatten()
    # print(b7_gt.getInfo()) # just to check the result..
   
    ## export the zone counts as csv - will be saved in Google Drive
    fc2csv(floodFc, 'floodCountFlattenResult')


