# -*- coding: utf-8 -*- python version 2.7
##  GIS spatial analysis using Python geo libraries & without GIS
##  takes CSV file with xy coordinates, turn it into "points" shapefile
##  then identify which points are inside of which polygons - spatial join - spits the result as CSV
##  my clients had duplicated polygons (excatly the same geometry but different time stamp) - function to identify them were also added

import os, sys, csv, shapefile, fiona, rtree
from shapely.geometry import Point, Polygon, mapping

##  turn csv to points
def csv2point(csvname,pointshp):
    schema = {
        'geometry': 'Point',
        'properties': {'id': 'int','name': 'str','fips':'str','elev': 'float'}
        }
    with fiona.collection(
        pointshp, "w", "ESRI Shapefile", schema) as output:
        with open(csvname, 'rb') as f:
            reader = csv.DictReader(f)
            for row in reader:
                point = Point(float(row['lon']), float(row['lat']))
                output.write({
                    'properties': {
                        'id':   row['golfid'],
                        'name': row['name'],
                        'fips': row['cntyfips'],
                        'elev': row['elev']
                    },
                    'geometry': mapping(point)
                })

##  ref: http://rexdouglass.com/fast-spatial-joins-in-python-with-a-spatial-index/
def spjoin(polygonshp, pointshp):
    ## Load the shapefile of polygons and convert it to shapely polygon objects
    polygons_sf = shapefile.Reader(polygonshp)
    polygon_shapes = polygons_sf.shapes()
    polygon_points = [q.points for q in polygon_shapes ]
    polygons = [Polygon(q) for q in polygon_points]
    polygon_records=polygons_sf.records()
    #print "Total number of polygons", len(polygon_records)

    ## Load the shapefile of points and convert it to shapely point objects
    points_sf = shapefile.Reader(pointshp)
    point_shapes = points_sf.shapes()
    point_coords= [q.points[0] for q in point_shapes ]
    points = [Point(q.points[0]) for q in point_shapes ]
    point_records=points_sf.records()
    #print "Total number of points", len(point_records)

    ## Build a spatial index based on the bounding boxes of the polygons
    ## so that we don't need to query the whole set
    idx = rtree.index.Index()
    count = -1
    for q in polygon_shapes:
        count +=1
        idx.insert(count, q.bbox)

    ## Assign one or more matching polygons to each point
    matches = []
    for i in range(len(points)): #Iterate through each point
        ## Iterate only through the bounding boxes which contain the point
        for j in idx.intersection(point_coords[i]):
            ## Verify that point is within the polygon itself not just the bounding box
            if points[i].within(polygons[j]):
                #print "Match found! Polygon OBJECTID is: ", str(int(polygon_records[j][0]))
                newmatch = str(point_records[i][1])+","+str(polygon_records[j][0])
                matches.append(newmatch)
    outputcsvname = os.path.splitext(os.path.basename(polygonshp))[0] + "_" + os.path.splitext(os.path.basename(pointshp))[0] + "_spjoin.csv"
    with open(outputcsvname, 'w') as r:  
        for row in matches:
            r.write(row + '\n')
    file.close

# this find duplicates function is not perfect but I forgot what the problem was - will come back
def finddup(polygonshp):
    ## Load the shapefile of polygons and convert it to shapely polygon objects
    polygons_sf = shapefile.Reader(polygonshp)
    polygon_shapes = polygons_sf.shapes()
    polygon_points = [q.points for q in polygon_shapes ]
    polygons = [Polygon(q) for q in polygon_points]
    polygon_records=polygons_sf.records()

    ## Assign one or more matching polygons to each point
    matches = []
    foundalready = []
    for i in range(len(polygons)): #Iterate through each point
        if str(i) in foundalready:
            break
        #print "Polygon ", str(int(polygon_records[i][0]))
        ## Iterate only through the bounding boxes which contain the point
        for j in range(len(polygons)):
            ## Verify that point is within the polygon itself not just the bounding box
            if polygons[i].equals(polygons[j]) and polygon_records[i][0]!=polygon_records[j][0]:
                #print "Match found! Polygon OBJECTID is: ", str(int(polygon_records[i][0]))
                foundalready.append(str(j))
                newmatch = str(polygon_records[i][0])+","+str(polygon_records[j][0])
                matches.append(newmatch)
    outputcsvname = os.path.splitext(os.path.basename(polygonshp))[0] + "_duplicates.csv"
    with open(outputcsvname, 'w') as r:  
        for row in matches:
            r.write(row + '\n')
    file.close

# =============================
if __name__ == '__main__':
    # require two arguments (1) input xy CSV name (2) input polygon shapefile name
    # e.g. python pythonGIS_example1.py golf.csv publdsur.shp
    pointshape = os.path.splitext(os.path.basename(sys.argv[1]))[0] + ".shp"
    csv2point(sys.argv[1], pointshape)
    spjoin(sys.argv[2], pointshape)
    finddup(sys.argv[2])
