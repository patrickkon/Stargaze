# This file defines the satellite configuration used in our simulation. 
# We will be using Starlink Phase 1, shell 1, for our simulation. The following config is taken from Hypatia. 
import math
import yaml

def get_config_yaml_dict(filename):
    with open(filename, "r") as stream:
        try:
            return yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            raise ValueError(exc)

HYPATIA_DIR = "../dependencies/hypatia"
CLUSTER_DIR = "../k8s-emulator"
CLUSTER_CONFIG_FILE = "../k8s-emulator/cluster_config.yaml"
CLUSTER_CONFIG = get_config_yaml_dict(CLUSTER_CONFIG_FILE)

# WGS72 value; taken from https://geographiclib.sourceforge.io/html/NET/NETGeographicLib_8h_source.html
EARTH_RADIUS = 6378135.0

if CLUSTER_CONFIG["constellation_name"] == "Starlink-550":
    # GENERATION CONSTANTS
    BASE_NAME = "starlink_550"
    NICE_NAME = "Starlink-550"

    # STARLINK 550

    ECCENTRICITY = 0.0000001  # Circular orbits are zero, but pyephem does not permit 0, so lowest possible value
    ARG_OF_PERIGEE_DEGREE = 0.0
    PHASE_DIFF = True

    ################################################################
    # The below constants are taken from Starlink's FCC filing as below:
    # [1]: https://fcc.report/IBFS/SAT-MOD-20190830-00087
    ################################################################

    MEAN_MOTION_REV_PER_DAY = 15.19  # Altitude ~550 km
    ALTITUDE_M = 550000  # Altitude ~550 km

    # From https://fcc.report/IBFS/SAT-MOD-20181108-00083/1569860.pdf (minimum angle of elevation: 25 deg)
    SATELLITE_CONE_RADIUS_M = 940700 # the value used here is actually assuming 30.3 deg min angle of elevation. Refer to Notion.

    MAX_GSL_LENGTH_M = math.sqrt(math.pow(SATELLITE_CONE_RADIUS_M, 2) + math.pow(ALTITUDE_M, 2))

    # ISLs are not allowed to dip below 80 km altitude in order to avoid weather conditions
    MAX_ISL_LENGTH_M = 2 * math.sqrt(math.pow(EARTH_RADIUS + ALTITUDE_M, 2) - math.pow(EARTH_RADIUS + 80000, 2))

    NUM_ORBS = 72
    NUM_SATS_PER_ORB = 22
    INCLINATION_DEGREE = 53

if CLUSTER_CONFIG["constellation_name"] == "Starlink-560":
    # GENERATION CONSTANTS
    BASE_NAME = "starlink_560"
    NICE_NAME = "Starlink-560"

    # STARLINK 550

    ECCENTRICITY = 0.0000001  # Circular orbits are zero, but pyephem does not permit 0, so lowest possible value
    ARG_OF_PERIGEE_DEGREE = 0.0
    PHASE_DIFF = True

    ################################################################
    # The below constants are taken from Starlink's FCC filing as below:
    # [1]: https://fcc.report/IBFS/SAT-MOD-20190830-00087
    ################################################################

    MEAN_MOTION_REV_PER_DAY = 15.04  # Altitude ~560 km
    ALTITUDE_M = 560000  # Altitude ~560 km

    # From https://fcc.report/IBFS/SAT-MOD-20181108-00083/1569860.pdf (minimum angle of elevation: 25 deg)
    SATELLITE_CONE_RADIUS_M = 1200930 # the value used here is actually assuming 30.3 deg min angle of elevation. Refer to Notion.

    MAX_GSL_LENGTH_M = math.sqrt(math.pow(SATELLITE_CONE_RADIUS_M, 2) + math.pow(ALTITUDE_M, 2))

    # ISLs are not allowed to dip below 80 km altitude in order to avoid weather conditions
    MAX_ISL_LENGTH_M = 2 * math.sqrt(math.pow(EARTH_RADIUS + ALTITUDE_M, 2) - math.pow(EARTH_RADIUS + 80000, 2))

    NUM_ORBS = 6
    NUM_SATS_PER_ORB = 58
    INCLINATION_DEGREE = 97.6

if CLUSTER_CONFIG["constellation_name"] == "Kuiper-630":
    # GENERATION CONSTANTS
    BASE_NAME = "kuiper_630"
    NICE_NAME = "Kuiper-630"

    # KUIPER 630

    ECCENTRICITY = 0.0000001  # Circular orbits are zero, but pyephem does not permit 0, so lowest possible value
    ARG_OF_PERIGEE_DEGREE = 0.0
    PHASE_DIFF = True

    ################################################################
    # The below constants are taken from Kuiper's FCC filing as below:
    # [1]: https://www.itu.int/ITU-R/space/asreceived/Publication/DisplayPublication/8716
    ################################################################

    MEAN_MOTION_REV_PER_DAY = 14.80  # Altitude ~630 km
    ALTITUDE_M = 630000  # Altitude ~630 km

    # Considering an elevation angle of 30 degrees; possible values [1]: 20(min)/30/35/45
    SATELLITE_CONE_RADIUS_M = ALTITUDE_M / math.tan(math.radians(30.0))

    MAX_GSL_LENGTH_M = math.sqrt(math.pow(SATELLITE_CONE_RADIUS_M, 2) + math.pow(ALTITUDE_M, 2))

    # ISLs are not allowed to dip below 80 km altitude in order to avoid weather conditions
    MAX_ISL_LENGTH_M = 2 * math.sqrt(math.pow(EARTH_RADIUS + ALTITUDE_M, 2) - math.pow(EARTH_RADIUS + 80000, 2))

    NUM_ORBS = 34
    NUM_SATS_PER_ORB = 34
    INCLINATION_DEGREE = 51.9

if CLUSTER_CONFIG["constellation_name"] == "Telesat-1015":
    # GENERATION CONSTANTS
    BASE_NAME = "telesat_1015"
    NICE_NAME = "Telesat-1015"

    # TELESAT 1015

    ECCENTRICITY = 0.0000001  # Circular orbits are zero, but pyephem does not permit 0, so lowest possible value
    ARG_OF_PERIGEE_DEGREE = 0.0
    PHASE_DIFF = True

    ################################################################
    # The below constants are taken from Telesat's FCC filing as below:
    # [1]: https://fcc.report/IBFS/SAT-MPL-20200526-00053/2378318.pdf
    ################################################################

    MEAN_MOTION_REV_PER_DAY = 13.66  # Altitude ~1015 km
    ALTITUDE_M = 1015000  # Altitude ~1015 km
    SATELLITE_CONE_RADIUS_M = ALTITUDE_M / math.tan(math.radians(10.0))  # Considering an elevation angle of 10 degrees;
    MAX_GSL_LENGTH_M = math.sqrt(math.pow(SATELLITE_CONE_RADIUS_M, 2) + math.pow(ALTITUDE_M, 2))
    # ISLs are not allowed to dip below 80 km altitude in order to avoid weather conditions
    MAX_ISL_LENGTH_M = 2 * math.sqrt(math.pow(EARTH_RADIUS + ALTITUDE_M, 2) - math.pow(EARTH_RADIUS + 80000, 2))
    NUM_ORBS = 27
    NUM_SATS_PER_ORB = 13
    INCLINATION_DEGREE = 98.98

if CLUSTER_CONFIG["constellation_name"] == "Starlink-550-72-72":
    # GENERATION CONSTANTS
    BASE_NAME = "starlink_550_72_72"
    NICE_NAME = "Starlink-550-72-72"

    # STARLINK 550 72 72

    ECCENTRICITY = 0.0000001  # Circular orbits are zero, but pyephem does not permit 0, so lowest possible value
    ARG_OF_PERIGEE_DEGREE = 0.0
    PHASE_DIFF = True

    ################################################################
    # The below constants are taken from Starlink's FCC filing as below:
    # [1]: https://fcc.report/IBFS/SAT-MOD-20190830-00087
    ################################################################

    MEAN_MOTION_REV_PER_DAY = 15.19  # Altitude ~550 km
    ALTITUDE_M = 550000  # Altitude ~550 km

    # From https://fcc.report/IBFS/SAT-MOD-20181108-00083/1569860.pdf (minimum angle of elevation: 25 deg)
    SATELLITE_CONE_RADIUS_M = ALTITUDE_M / math.tan(math.radians(25.0))

    MAX_GSL_LENGTH_M = math.sqrt(math.pow(SATELLITE_CONE_RADIUS_M, 2) + math.pow(ALTITUDE_M, 2))

    # ISLs are not allowed to dip below 80 km altitude in order to avoid weather conditions
    MAX_ISL_LENGTH_M = 2 * math.sqrt(math.pow(EARTH_RADIUS + ALTITUDE_M, 2) - math.pow(EARTH_RADIUS + 80000, 2))

    NUM_ORBS = 72
    NUM_SATS_PER_ORB = 72
    INCLINATION_DEGREE = 53

if CLUSTER_CONFIG["constellation_name"] == "Starlink-550-48-48":
    # GENERATION CONSTANTS
    BASE_NAME = "starlink_550_48_48"
    NICE_NAME = "Starlink-550-48-48"

    # STARLINK 550 48 48

    ECCENTRICITY = 0.0000001  # Circular orbits are zero, but pyephem does not permit 0, so lowest possible value
    ARG_OF_PERIGEE_DEGREE = 0.0
    PHASE_DIFF = True

    ################################################################
    # The below constants are taken from Starlink's FCC filing as below:
    # [1]: https://fcc.report/IBFS/SAT-MOD-20190830-00087
    ################################################################

    MEAN_MOTION_REV_PER_DAY = 15.19  # Altitude ~550 km
    ALTITUDE_M = 550000  # Altitude ~550 km

    # From https://fcc.report/IBFS/SAT-MOD-20181108-00083/1569860.pdf (minimum angle of elevation: 25 deg)
    SATELLITE_CONE_RADIUS_M = ALTITUDE_M / math.tan(math.radians(25.0))

    MAX_GSL_LENGTH_M = math.sqrt(math.pow(SATELLITE_CONE_RADIUS_M, 2) + math.pow(ALTITUDE_M, 2))

    # ISLs are not allowed to dip below 80 km altitude in order to avoid weather conditions
    MAX_ISL_LENGTH_M = 2 * math.sqrt(math.pow(EARTH_RADIUS + ALTITUDE_M, 2) - math.pow(EARTH_RADIUS + 80000, 2))

    NUM_ORBS = 48
    NUM_SATS_PER_ORB = 48
    INCLINATION_DEGREE = 53

if CLUSTER_CONFIG["constellation_name"] == "Starlink-550-100-100":
    # GENERATION CONSTANTS
    BASE_NAME = "starlink_550_100_100"
    NICE_NAME = "Starlink-550-100-100"

    # STARLINK 550 100 100

    ECCENTRICITY = 0.0000001  # Circular orbits are zero, but pyephem does not permit 0, so lowest possible value
    ARG_OF_PERIGEE_DEGREE = 0.0
    PHASE_DIFF = True

    ################################################################
    # The below constants are taken from Starlink's FCC filing as below:
    # [1]: https://fcc.report/IBFS/SAT-MOD-20190830-00087
    ################################################################

    MEAN_MOTION_REV_PER_DAY = 15.19  # Altitude ~550 km
    ALTITUDE_M = 550000  # Altitude ~550 km

    # From https://fcc.report/IBFS/SAT-MOD-20181108-00083/1569860.pdf (minimum angle of elevation: 25 deg)
    SATELLITE_CONE_RADIUS_M = ALTITUDE_M / math.tan(math.radians(25.0))

    MAX_GSL_LENGTH_M = math.sqrt(math.pow(SATELLITE_CONE_RADIUS_M, 2) + math.pow(ALTITUDE_M, 2))

    # ISLs are not allowed to dip below 80 km altitude in order to avoid weather conditions
    MAX_ISL_LENGTH_M = 2 * math.sqrt(math.pow(EARTH_RADIUS + ALTITUDE_M, 2) - math.pow(EARTH_RADIUS + 80000, 2))

    NUM_ORBS = 100
    NUM_SATS_PER_ORB = 100
    INCLINATION_DEGREE = 53

if CLUSTER_CONFIG["constellation_name"] == "Starlink-550-130-130":
    # GENERATION CONSTANTS
    BASE_NAME = "starlink_550_130_130"
    NICE_NAME = "Starlink-550-130-130"

    # STARLINK 550 130 130

    ECCENTRICITY = 0.0000001  # Circular orbits are zero, but pyephem does not permit 0, so lowest possible value
    ARG_OF_PERIGEE_DEGREE = 0.0
    PHASE_DIFF = True

    ################################################################
    # The below constants are taken from Starlink's FCC filing as below:
    # [1]: https://fcc.report/IBFS/SAT-MOD-20190830-00087
    ################################################################

    MEAN_MOTION_REV_PER_DAY = 15.19  # Altitude ~550 km
    ALTITUDE_M = 550000  # Altitude ~550 km

    # From https://fcc.report/IBFS/SAT-MOD-20181108-00083/1569860.pdf (minimum angle of elevation: 25 deg)
    SATELLITE_CONE_RADIUS_M = ALTITUDE_M / math.tan(math.radians(25.0))

    MAX_GSL_LENGTH_M = math.sqrt(math.pow(SATELLITE_CONE_RADIUS_M, 2) + math.pow(ALTITUDE_M, 2))

    # ISLs are not allowed to dip below 80 km altitude in order to avoid weather conditions
    MAX_ISL_LENGTH_M = 2 * math.sqrt(math.pow(EARTH_RADIUS + ALTITUDE_M, 2) - math.pow(EARTH_RADIUS + 80000, 2))

    NUM_ORBS = 130
    NUM_SATS_PER_ORB = 130
    INCLINATION_DEGREE = 53

if CLUSTER_CONFIG["constellation_name"] == "Starlink-550-150-150":
    # GENERATION CONSTANTS
    BASE_NAME = "starlink_550_150_150"
    NICE_NAME = "Starlink-550-150-150"

    # STARLINK 550 150 150

    ECCENTRICITY = 0.0000001  # Circular orbits are zero, but pyephem does not permit 0, so lowest possible value
    ARG_OF_PERIGEE_DEGREE = 0.0
    PHASE_DIFF = True

    ################################################################
    # The below constants are taken from Starlink's FCC filing as below:
    # [1]: https://fcc.report/IBFS/SAT-MOD-20190830-00087
    ################################################################

    MEAN_MOTION_REV_PER_DAY = 15.19  # Altitude ~550 km
    ALTITUDE_M = 550000  # Altitude ~550 km

    # From https://fcc.report/IBFS/SAT-MOD-20181108-00083/1569860.pdf (minimum angle of elevation: 25 deg)
    SATELLITE_CONE_RADIUS_M = ALTITUDE_M / math.tan(math.radians(25.0))

    MAX_GSL_LENGTH_M = math.sqrt(math.pow(SATELLITE_CONE_RADIUS_M, 2) + math.pow(ALTITUDE_M, 2))

    # ISLs are not allowed to dip below 80 km altitude in order to avoid weather conditions
    MAX_ISL_LENGTH_M = 2 * math.sqrt(math.pow(EARTH_RADIUS + ALTITUDE_M, 2) - math.pow(EARTH_RADIUS + 80000, 2))

    NUM_ORBS = 150
    NUM_SATS_PER_ORB = 150
    INCLINATION_DEGREE = 53

if CLUSTER_CONFIG["constellation_name"] == "Starlink-550-200-200":
    # GENERATION CONSTANTS
    BASE_NAME = "starlink_550_200_200"
    NICE_NAME = "Starlink-550-200-200"

    # STARLINK 550 200 200

    ECCENTRICITY = 0.0000001  # Circular orbits are zero, but pyephem does not permit 0, so lowest possible value
    ARG_OF_PERIGEE_DEGREE = 0.0
    PHASE_DIFF = True

    ################################################################
    # The below constants are taken from Starlink's FCC filing as below:
    # [1]: https://fcc.report/IBFS/SAT-MOD-20190830-00087
    ################################################################

    MEAN_MOTION_REV_PER_DAY = 15.19  # Altitude ~550 km
    ALTITUDE_M = 550000  # Altitude ~550 km

    # From https://fcc.report/IBFS/SAT-MOD-20181108-00083/1569860.pdf (minimum angle of elevation: 25 deg)
    SATELLITE_CONE_RADIUS_M = ALTITUDE_M / math.tan(math.radians(25.0))

    MAX_GSL_LENGTH_M = math.sqrt(math.pow(SATELLITE_CONE_RADIUS_M, 2) + math.pow(ALTITUDE_M, 2))

    # ISLs are not allowed to dip below 80 km altitude in order to avoid weather conditions
    MAX_ISL_LENGTH_M = 2 * math.sqrt(math.pow(EARTH_RADIUS + ALTITUDE_M, 2) - math.pow(EARTH_RADIUS + 80000, 2))

    NUM_ORBS = 200
    NUM_SATS_PER_ORB = 200
    INCLINATION_DEGREE = 53

def config_generate_constellation():
    """Pass constellation config information to calling function"""
    return [    
        BASE_NAME,
        NICE_NAME,
        ECCENTRICITY,
        ARG_OF_PERIGEE_DEGREE,
        PHASE_DIFF,
        MEAN_MOTION_REV_PER_DAY,
        ALTITUDE_M,
        MAX_GSL_LENGTH_M,
        MAX_ISL_LENGTH_M,
        NUM_ORBS,
        NUM_SATS_PER_ORB,
        INCLINATION_DEGREE,
    ]