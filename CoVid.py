from utils.logger import logger, set_verbosity
from db.utils import Database, to_numpy
from analysis.model import SEIR, SEIRPopulation 
from visualize.plot import plot
import argparse


# Parse input arguments
def define_and_parse_args():

    parser = argparse.ArgumentParser(description='CoVid-19 analyzer tool')
    parser.add_argument("-d",
                        "--days",
                        help="Predict the number of confirmed infection in the next d days",
                        type=int,
                        required=True)
    parser.add_argument("-R0",
                        help="Infection R0",
                        type=float,
                        default=2.2)
    parser.add_argument("-l",
                        "--lockdown",
                        help="Lockdown day, from the beginning of the epidemic",
                        type=int,
                        default=60)
    parser.add_argument("-e",
                        "--effectivness",
                        help="Effectivness of the social isolation, as a percentage",
                        type=float,
                        default=0.3)
    parser.add_argument("-v", "--verbose", help="Verbose output", action="store_true")

    return parser.parse_args()


def main(args):
    # Set the verbosity
    set_verbosity(args.verbose)

    # Get the arguments
    logger.info("Italian Confirmed patients")
    italy_confirmed = to_numpy(Database("confirmed").get_patients_by_country("Italy"))
    plot(range(len(italy_confirmed)), [italy_confirmed], [("red", "total_confimred_in_italy")], filename="./italy_confirmed.png")

    model = SEIR(intervention_day=args.lockdown,
                 R0 = args.R0,
                 effectiveness = args.effectivness,
                 mean_incubation_time = 5.2,
                 mean_remove_time = 2.1)

    y0 = [60000000, 0, 1, 0]
    t =  list(range(args.days))
    S, E, I, R = model.integrate(t, y0)
    plot(t, [R], [("red", "total_infected")], filename="./literature_model.png")

    logger.info("Start fittting")
    population = SEIRPopulation(italy_confirmed, "analysis/configurations/100_generations.yaml")

    for idx, best_fitness in population.train():
        logger.info(f"Generation {idx}: best fitness={best_fitness}")

    best_model = population.best_models()[0]
    best_model.dump("ciao.yaml")
    S, E, I, R = best_model.simulate(t)
    plot(t, [R], [("red", "total_infected")], filename="./best_model.png")


if __name__ == "__main__":
    args = define_and_parse_args()
    main(args)
