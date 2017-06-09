import datetime
import MySQLdb
import ConfigParser
from Company import Company

# MAGIC NUMBERS MHMM... (~^-^)~
################################################################################
# Last time the DB was updated
#
LAST_REFRESH = datetime.date(2014, 10, 1)

# Based on 2.4 million a year
#
AVG_DAILY_BURN = float(2400000 / 365.0)

# Start ups that last more than 2.5 years are successful
#
OPERATION_RATING_PER_DAY = float(0.4 / 365.0)

# Start ups that have more than 2 years of runway are successful
#
RUNWAY_RATING_PER_DAY = float(0.5 / 365.0)

# Gain some points for relationships with key people
#
RELATIONSHIP_RATING = 0.2

# Companies that aren't auto successes and have no entered funding value
# are evaluated by last inflow, 1 - (inflow * rating)
#
INFLOW_RATING_PER_DAY = float(0.5 / 365.0)

# Two and a half years in days rounded down
#
TWO_HALF_YEARS = 912
################################################################################


################################################################################
# Calculates the success rates and individual success of all companies in the
# dataset
#
# Returns - ref_data (The new dataset)
#           test_data (Portion of the dataset for testing purposes)
#           country_map (Contains country influence rates)
#           city_map
#           market_map
#
################################################################################
#
def parseData(dbName):
    config = ConfigParser.RawConfigParser()
    config.read('../private/.crunchdb.ini')
    db_user = config.get('mysql_creds', 'user')
    db_pass = config.get('mysql_creds', 'passwd')

    ref_data = []
    test_data = []
    country_map = {}
    city_map = {}
    market_map = {}
    maps = (country_map, city_map, market_map)

    entry_num = 0

    try:
        db = MySQLdb.connect(user=db_user, passwd=db_pass, db=dbName)
        cursor = db.cursor(MySQLdb.cursors.DictCursor)
    except Exception as e:
        print("Unable to connect to Database {}:\n {}".format(dbName, e))
        raise SystemExit()

    query = ("SELECT normalized_name, category_code, status, "
             "country_code, state_code, city, region, invested_companies, "
             "first_investment_at, last_investment_at, investment_rounds, "
             "first_funding_at, last_funding_at, funding_rounds, "
             "funding_total_usd, founded_at, relationships FROM object_analysis "
             "WHERE entity_type NOT IN ('Product', 'People')")

    cursor.execute(query)

    for result in cursor:

        # Grab points for ease.

        # WIP data points:
        #state_code = result['state_code']
        #region = result['region']
        #invested_companies = result['invested_companies']
        #
        name = result['normalized_name']
        market = result['category_code']
        funding_total = result['funding_total_usd']
        status = result['status']
        country = result['country_code']
        city = result['city']
        founded = result['founded_at']
        relationships = result['relationships']

        invest_rounds = result['investment_rounds']
        first_invest = result['first_investment_at']
        last_invest = result['last_investment_at']

        funding_rounds = result['funding_rounds']
        first_funding = result['first_funding_at']
        last_funding = result['last_funding_at']

        # Create company object
        #
        current_company = Company(name, status, market, country, city, founded,
                                  relationships, invest_rounds, first_invest,
                                  last_invest, funding_rounds, funding_total,
                                  first_funding, last_funding)

        # Check if the company is successful
        #
        current_company.successful = _is_successful(current_company)

        # Updates the maps and starts paritioning some test data
        #
        if entry_num % 500 != 0:
            country_map, city_map, market_map = _update_maps(country_map,
                                                             city_map,
                                                             market_map,
                                                             current_company)

            ref_data.append(current_company)
        else:
            test_data.append(current_company)
        entry_num += 1

    cursor.close()
    db.close()

    # Create the weight or 'influence rating' for each key in every map
    # 50% is considered no influence. Anything over 50% is considered an
    # influence
    #
    for current_map in maps:
        for key in current_map:
            key_total = current_map[key][0] + current_map[key][1]
            if (key_total < 5 or current_map[key][0] > 0):

                current_map[key] = \
                    float(current_map[key][1]) / float(key_total)
                current_map[key] = abs(current_map[key] - 0.5)
            else:
                current_map[key] = 0.5

    return ref_data, test_data, country_map, city_map, market_map

################################################################################
# Determines a companies success bases on its data points.
# A rating >= 1 is considered successful
#
# Returns - bool: True (Successful), False (Unsuccessful)
#
################################################################################
#
def _is_successful(current_company):
    rating = 0

    # Company that has ipo'd or been acquired is auto success.
    # Company that is closed is deemed a failure.
    # Any operating company must be categorized.
    #
    if current_company.status in ('ipo', 'acquired'):
        rating = 1
    elif ((current_company.first_funding or current_company.first_invest or
           current_company.founded) and (current_company.status != 'closed')):

        valid_dates = []
        runway = 0

        # Calculate start date
        #
        if current_company.first_funding:
            valid_dates.append(current_company.first_funding)
        if current_company.first_invest:
            valid_dates.append(current_company.first_invest)
        if current_company.founded:
            valid_dates.append(current_company.founded)

        start_date = min(valid_dates)

        # Operation is a maxed out at the Last refresh of the DB. 2014-10-01
        #
        days_operating = (LAST_REFRESH - start_date).days

        # Calc runway if there is any funding info.
        #
        if(current_company.funding_total):
            days_funded = \
                float(current_company.funding_total) / AVG_DAILY_BURN

            runway = days_operating - days_funded

        # If there is no numerical funding info then calc the time since their
        # last funding. (Idea is that funding should be worth something even if
        # we don't know the value)
        #
        elif (days_operating < TWO_HALF_YEARS) and \
                (current_company.last_funding or current_company.last_invest):

            # Cases where funding is before founding date
            # Curtousy of ditry data
            #
            valid_dates = []
            if current_company.last_funding:
                valid_dates.append(current_company.last_funding)
            if current_company.last_invest:
                valid_dates.append(current_company.last_invest)
            last_inflow_at = max(valid_dates)

            # Calcs the time since last funding
            #
            days_since_inflow = (LAST_REFRESH - last_inflow_at).days

            flow_rating = (1 - (days_since_inflow * INFLOW_RATING_PER_DAY))
            if flow_rating > 0:
                rating += flow_rating

        # Relationship factor
        #
        if current_company.relationships:
            rating += current_company.relationships * RELATIONSHIP_RATING

        rating += days_operating * (OPERATION_RATING_PER_DAY)
        rating += runway * (RUNWAY_RATING_PER_DAY)

    return bool(rating >= 1)

################################################################################
# Updates the influence rating of each non numerical data point.
# More than a counter to give scale
#
# Returns - country_map (Hash map containing Success and Failure counts)
#         - city_map
#         - market_map
#
################################################################################
#
def _update_maps(country_map, city_map, market_map, current_company):
    if current_company.successful:
        # Company is deemed successful
        try:
            country_map[current_company.country][0] += 1
        except KeyError:
            country_map[current_company.country] = [1, 0]

        try:
            market_map[current_company.market][0] += 1
        except KeyError:
            market_map[current_company.market] = [1, 0]

        try:
            city_map[current_company.city][0] += 1
        except KeyError:
            city_map[current_company.city] = [1, 0]
    else:
        try:
            country_map[current_company.country][1] += 1
        except KeyError:
            country_map[current_company.country] = [0, 1]

        try:
            market_map[current_company.market][1] += 1
        except KeyError:
            market_map[current_company.market] = [0, 1]

        try:
            city_map[current_company.city][1] += 1
        except KeyError:
            city_map[current_company.city] = [0, 1]

    return country_map, city_map, market_map
