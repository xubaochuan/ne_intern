#! /usr/bin/env python
# -*- coding: utf-8 -*-
#auther:xubaochuan
#date:2016.11.30

import os

west = 73.66
east = 135.04
south = 17.98
north = 53.55

west100 = 12883
east100 = 13504
south100 = 1798
north100 = 5355

def getAreaData(file_path):
    areas_dict = {}
    areas = os.listdir(file_path)
    for name in areas:
        area_path = os.path.join(file_path, name)
        fr = open(area_path)
        data = fr.readline().strip()
        if data == '':
            continue
        point_list = []
        tuples = data.split(';')
        for couple in tuples:
               couple_list = couple.split(',')
               x = float(couple_list[0])
               y = float(couple_list[1])
               point_list.append([x,y])
        area_name = name[:-4]
        areas_dict[area_name] = point_list
    return areas_dict

def loadMapData():
    city_dir = 'all/city'
    province_dir = 'all/province'
    map_dict = {}
    province_dict = getAreaData(province_dir)
    map_dict['province'] = province_dict
    province_list = os.listdir(city_dir)
    map_dict['city'] = {}
    for name in province_list:
        province_path = os.path.join(city_dir, name)
        city_dict = getAreaData(province_path)
        map_dict['city'][name] = city_dict
    return map_dict

def getLocation(position_x, position_y, areas_dict):
    for (name, point_list) in areas_dict.items():
        if isIn(position_x, position_y, point_list):
            return name
    return 'None'

def isIn(position_x, position_y, array):
    n = len(array)
    i = 0
    j = n-1
    c = False
    for i in range(n):
        if(((array[i][1] > position_y) != (array[j][1] > position_y)) and (position_x < (array[j][0] - array[i][0])*(position_y - array[i][1])/(array[j][1] - array[i][1]) + array[i][0])):
            c = not c
        j = i
        i += 1
    return c


def get_province(x, y, map_dict):
    province = getLocation(x, y, map_dict['province'])
    if province in ['110000','310000','120000','500000','810000','820000','710000']:
        return {'code':200, 'type':'district' , 'province':province}
    elif province != 'None':
        city = getLocation(x, y, map_dict['city'][province])
        if city != 'None':
            return {'code':200, 'type':'city' , 'province':province, 'city':city}
        else:
            return {'code':200, 'type':'province' , 'province':province}
    else:
        return {'code':400, 'type':'notfound'}

def main():
    map_dict = loadMapData()
    write_file = 'data/area_map10.txt'
    fw = open(write_file, 'w')
    for x in range(west100, east100):
        for y in range(south100, north100):
            pos_x = round(float(x)/100, 2)
            pos_y = round(float(y)/100, 2)
            response = get_province(pos_x, pos_y, map_dict)
            if response['code'] == 200:
                if response['type'] in ['province', 'district']:
                    print str(x)+str(y)+'\t'+response['province']
                    fw.write(str(x)+str(y)+'\t'+response['province'] + '\n')
                elif response['type'] in ['city']:
                    print str(x)+str(y)+'\t'+response['city']
                    fw.write(str(x) + str(y) + '\t' + response['city'] + '\n')
            else:
                print str(x)+str(y)+' not found'
    fw.close()
    print "10 generate finished"

if __name__=='__main__':
    # main(117.9731410000,36.6498370000)
    main()
