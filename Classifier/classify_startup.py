import sys
import datetime
import os.path
import init_data as init
import cPickle
import argparse
from operator import itemgetter
from Company import Company

################################################################################
FIVE_YEARS = 365 * 5
################################################################################

################################################################################
# USE: python classify_startup.py -n Generic -s operating -m 'Real Estate' -co USA -ci 'San Francisco' -fo 2012-01-01 -r 0 -fr 1 -ft 200000 -ff 2012-07-07 -lf 2012-07-07
################################################################################
#   TODO:
#   !Priority!
##
#   1. Change the sorting method of neighbours to be more efficient. (Data is
#      basically sorted)
#   2. Find a way to use NoneTypes in the distance calculation.
#      Ie). None Funding should be 0
#   3. Scale the influence of neighbours found by distance. All neighbours put
#      into the k_neighbours shouldn't be weighted the same in success calc
#   4. Rework so pickles aren't opened for every test. Also pickles shouldn't
#      need to be opened on initialization
#   4. Use Key verification to login to DB User instead of password
##
#
#   Quality Of Life
##
#   1. Get reasoning behind magic NUMBERS
#   2. Clean the DB so assumptions can be made
#   3. Look into using defualtdict to get rid of  dict initalization try/catch
#   4. Consolidate the For-loops in weight calc as they are the same logic
#   5. Rework checking for None dates, and defaulting. Feels like too many if's
##
#
#

################################################################################
# Calculates the distance between numerical points given.
# Will scale the distance to be a max of 1 for each point
#
# Returns - sum (The distance between the two companies)
#
################################################################################
#
def get_n_distance(points1, points2):
    sum = 0.0
    for index in range(len(points1)):
        diff = 1
        if points1[index] is not None and points2[index] is not None:
            diff = abs(points1[index] - points2[index])

            if isinstance(points1[index], datetime.date):
                scale = 1
                if diff.days < FIVE_YEARS:
                    scale = float(diff.days / FIVE_YEARS)
                sum += scale
            else:
                try:
                    sum += float(diff / (points1[index] + points2[index]))
                except ZeroDivisionError:
                    pass
        else:
            sum += diff

        # Both X and Y should be positive. Only 0 would be X = 0 and Y = 0

    return sum

################################################################################
# Gathers the k closest neighbours around the company. Will calculate the
# distance between two points and scale up or down depending on the relations
#
# Returns - k_neighbours (List of k companies that are closest)
#
################################################################################
#
def get_k_neighbors(company, k, data, country_weights, city_weights, market_weights):
    k_neighbours = []
    for ref_company in data:

        # Gets the distance based on anything numerical
        distance = get_n_distance(company.get_numerical_points(),
                                  ref_company.get_numerical_points())

        if(company.country == ref_company.country):
            distance *= country_weights[ref_company.country]

        if(company.city == ref_company.city):
            distance *= city_weights[ref_company.city]

        if(company.market == ref_company.market):
            distance *= market_weights[ref_company.market]

        if len(k_neighbours) >= k:
            if (distance < k_neighbours[k - 1][0]):
                k_neighbours[k - 1] = (distance, ref_company)
                k_neighbours.sort(key=itemgetter(0))
        else:
            k_neighbours.append((distance, ref_company))

    return k_neighbours

################################################################################
# Takes the neighbours and determines the success rate. If the rate is within
# the accepted range of sureness then classify.
#
# Returns - 1 (Successful)
#           0 (Unsuccessful)
#           -1 (Uncertain)
#
################################################################################
#
def success_rate(neighbors):
    num_successful = 0
    num_failures = 0
    for neighbor in neighbors:
        if neighbor[1].successful:
            num_successful += 1
        else:
            num_failures += 1

    diff = num_successful - num_failures

    # Has to have a diff
    sureness = float(num_successful) / float(len(neighbors))

    # At least 65% of results one way
    if sureness < 0.35 or sureness > 0.65:
        if diff > 0:
            return 1
        else:
            return 0

    # Return unsure doesn't fall into the acceptable results range
    return -1

################################################################################
# Initializes the data set (Determines successes and failures) and creates
# pickles for next time.
#
# Returns - 1 (Initialization was successful)
#
################################################################################
#
def initialize():
    print "Initializing Data.."
    ref_data, test_data, country_weights, city_weights, market_weights = [], [], {}, {}, {}
    ref_data, test_data, country_weights, city_weights, market_weights = init.parseData(
        'analytics_2')

    data_structs = (country_weights, city_weights, market_weights)
    iter_data = (ref_data, test_data)

    names = ('country_weights', 'city_weights', 'market_weights')
    iter_names = ('ref_data', 'test_data')

    print "Pickling Data.."
    if not os.path.exists('.pickle/'):
        print "No Pickle directory found.."
        print "Creating one at {0}/.pickle".format(os.getcwd())
        os.makedirs('.pickle/')

    for i in range(len(names)):
        with open('.pickle/.{0}.pickle'.format(names[i]), 'wb') as f:
            cPickle.dump(data_structs[i], f, protocol=cPickle.HIGHEST_PROTOCOL)

    for i in range(len(iter_names)):
        with open('.pickle/.{0}.pickle'.format(iter_names[i]), 'wb') as f:
            for data in iter_data[i]:
                cPickle.dump(data, f, protocol=cPickle.HIGHEST_PROTOCOL)

    return 1

################################################################################
# Checks to see if the data has been initialized. (If there are pickles)
#
# Returns - True (Initialized)
#         - False (Not Initialized)
#
################################################################################
#
def is_initialized():
    names = ('ref_data', 'test_data', 'country_weights',
             'city_weights', 'market_weights')
    for name in names:
        if not os.path.exists(".pickle/.{0}.pickle".format(name)):
            return False
    return True

################################################################################
# Partitions the data set and tests against itself.
#
# Prints
#
################################################################################
#
def test(k=9):
    print "Starting Test.."
    initialize()

    test_data = load_in('.pickle/.test_data.pickle')

    correct = 0
    wrong = 0

    for company in test_data:
        if classify(company, k) == company.successful:
            correct += 1
        else:
            print(company.name, company.status, company.market, company.country,
                  company.city, company.founded, company.relationships, company.invest_rounds,
                  company.first_invest, company.last_invest, company.funding_rounds,
                  company.funding_total, company.first_funding, company.last_funding,
                  company.successful)
            wrong += 1

        print "Accuracy: {0}%  Correct: {1}  Wrong: {2}".format(float(correct) / float(wrong + correct) * 100, correct, wrong)

    print "Tested {0} entries with k={2}:".format(total_to_test, k)
    if (wrong > 0):
        print "\n{0}% accuracy for {1} neighbors.".format(float(correct) / float(total_to_test) * 100, k)
    else:
        print "\n100% accuracy for {0} neighbors.".format(k)

################################################################################
# Classifies your startup based on the k closest neighbours
#
# Returns - 1 (Successful)
#           0 (Failure)
#           -1 (Uncertain)
#
################################################################################
#
def classify(company, k=9):
    if company.status in ('ipo', 'acquired'):
        return 1
    if company.status == 'closed':
        return 0
    ref_data, country_weights, city_weights, market_weights = grab_files()

    print("Crunching numbers. . .")
    comparable_companies = get_k_neighbors(company, k, ref_data, country_weights,
                                           city_weights, market_weights)
    # for data in comparable_companies:
    #     company = data[1]
    #     print(company.name,company.status,company.market,company.country,\
    #     company.city,company.founded,company.relationships, company.invest_rounds,\
    #     company.first_invest,company.last_invest,company.funding_rounds,\
    #     company.funding_total,company.first_funding,company.last_funding,
    #     company.successful)
    return success_rate(comparable_companies)

################################################################################
# Grabs the data needed from the pickled files
#
# Returns - ref_data (Iterator)
#         - country_weights (Hashmap)
#         - city_weights
#         - market_weights
#
################################################################################
#
def grab_files():
    print("Opening pickles. . .")

    ref_data = load_in('.pickle/.ref_data.pickle')

    with open('.pickle/.country_weights.pickle', 'rb') as f:
        country_weights = cPickle.load(f)
    with open('.pickle/.city_weights.pickle', 'rb') as f:
        city_weights = cPickle.load(f)
    with open('.pickle/.market_weights.pickle', 'rb') as f:
        market_weights = cPickle.load(f)
    return ref_data, country_weights, city_weights, market_weights

################################################################################
# Generator for a pickled file.
#
# Returns - A company object
#
#################################################################################
#
def load_in(f_name):
    with open(f_name, "rb") as f:
        while True:
            try:
                yield cPickle.load(f)
            except EOFError:
                break

################################################################################
# MAIN
################################################################################
#
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-test', action="store_true")
    parser.add_argument('-clean', action='store_true')
    parser.add_argument('-n', type=str)
    parser.add_argument('-s', type=str)
    parser.add_argument('-m', type=str)
    parser.add_argument('-co', type=str)
    parser.add_argument('-ci', type=str)
    parser.add_argument('-fo', type=str)
    parser.add_argument('-r', type=int)
    parser.add_argument('-ir', type=str)
    parser.add_argument('-fi', type=str)
    parser.add_argument('-li', type=str)
    parser.add_argument('-fr', type=int)
    parser.add_argument('-ft', type=float)
    parser.add_argument('-ff', type=str)
    parser.add_argument('-lf', type=str)
    parser.add_argument('-k', type=int, default=9)
    args = parser.parse_args()

    if args.test:
        test(args.k)
    else:
        if (not is_initialized()) or args.clean:
            initialize()

        date_inputs = [args.fi, args.li, args.ff, args.lf, args.fo]
        i = 0
        while i < len(date_inputs):
            if date_inputs[i]:
                date_inputs[i] = datetime.date(int(date_inputs[i][:4]),
                                               int(date_inputs[i][5:7]),
                                               int(date_inputs[i][8:10]))
            i += 1

        company = Company(args.n, args.s, args.m, args.co, args.ci,
                          date_inputs[4], args.r, args.ir, date_inputs[0],
                          date_inputs[1], args.fr, args.ft, date_inputs[2],
                          date_inputs[3])

        print(classify(company, args.k))


if __name__ == '__main__':
    main()
