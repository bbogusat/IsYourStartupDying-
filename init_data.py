import csv

#self, name, status, market, country, funding_value, funding_rounds):
def parseData_array(csvfile):
    with open(csvfile, 'rb') as data_file:
        data_reader = csv.reader(data_file, delimiter=',', quotechar='"')
        comp_arr = []
        country_totals = {}

        for line in data_reader:
            comp_arr.append(Company(line[0], line[3], line[1], line[4], line[2], line[7]))


            if(line[4] in country_totals):
                if(successfulMarker(line[3])):
                    country_totals[line[4]][0] += 1
                else:
                    country_totals[line[4]][1] += 1
            else:
                if(successfulMarker(line[3])):
                    country_totals[line[4]] = [1,0]
                else:
                    country_totals[line[4]] = [0,1]


    return comp_arr ,

def countryWeight():

    if()

def marketWeight():

def successfulMarker(operation):
    if(operation == 'ipo' or operation == 'aquired'):
        return true
    else:
        return false

