import logging
import random

import stormpy as sp
import stormpy.pomdp
import stormpy.simulator

import gridstorm.models as models
import gridstorm.plotter as plotter
import gridstorm.recorder

logger = logging.getLogger(__name__)


class SimulationExecutor:
    """
    Base class that wraps the stormpy simulator
    """
    def __init__(self, model, seed):
        self._model = model
        self._simulator = sp.simulator.create_simulator(model, seed=seed)
        self._simulator.set_full_observability(True) # We want to access the full state space for visualisations.

    def simulate(self, recorder, nr_good_runs = 1, total_nr_runs = 5, maxsteps=200):
        result = []
        good_runs = 0
        for m in range(total_nr_runs):
            finished = False
            state, _, _ = self._simulator.restart()
            logger.info("Start new episode.")
            recorder.start_path()
            recorder.record_state(state)
            for n in range(maxsteps):
                actions = self._simulator.available_actions()
                action = random.randint(0, len(actions) - 1)
                logger.debug(f"Select action: {action}")
                state, _, _ = self._simulator.step(action)
                recorder.record_available_actions(actions)
                recorder.record_allowed_actions(actions)
                recorder.record_selected_action(action)
                recorder.record_state(state)

                if self._simulator.is_done():
                    logger.info(f"Done after {n} steps!")
                    finished = True
                    good_runs += 1
                    break
            actions = self._simulator.available_actions()
            recorder.record_available_actions(actions)
            recorder.record_allowed_actions(actions)
            recorder.end_path(finished)
            result.append(self._simulator.is_done())
            if good_runs == nr_good_runs:
                break
        return result


def build_pomdp(program, formula):
    options = sp.BuilderOptions([formula])
    options.set_build_state_valuations()
    options.set_build_choice_labels()
    options.set_build_all_labels()
    logger.debug("Start building the POMDP")
    return sp.build_sparse_model_with_options(program, options)


experiment_to_grid_model_names = {
    "avoid": models.surveillance,
    "refuel": models.refuel,
    'obstacle': models.obstacle,
    "intercept": models.intercept,
    'evade': models.evade,
    'rocks': models.rocks
}

def demo(model_name, constants, gif):
    """
    Demonstrates how to use the library.

    :param model_name: Name of the model, must be one of the experiment_to_grid_model_names.
    :param constants: Dictionary of constant values that matches the model description
    :param gif: Render a gif or an MP4.
    """
    logging.basicConfig(filename='demo.log', level=logging.DEBUG)
    model = experiment_to_grid_model_names[model_name]
    constants = dict(item.split('=') for item in constants.split(","))
    input = model(**constants)
    prism_program = sp.parse_prism_program(input.path)
    prop = sp.parse_properties_for_prism_program(input.properties[0], prism_program)[0]
    prism_program, props = sp.preprocess_symbolic_input(prism_program, [prop], input.constants)
    prop = props[0]
    prism_program = prism_program.as_prism_program()
    raw_formula = prop.raw_formula

    logger.info("Construct POMDP representation...")
    model = build_pomdp(prism_program, raw_formula)
    if model.is_partially_observable:
        # TODO: Once version stormpy 1.7.1 is released, we do not need the if here.
        model = sp.pomdp.make_canonic(model)

    renderer = plotter.Plotter(prism_program, input.annotations, model)
    renderer.set_title("Demo")
    recorder = gridstorm.recorder.VideoRecorder(renderer, False)
    executor = SimulationExecutor(model, seed=42)
    executor.simulate(recorder)
    recorder.save(".", "demo", gif=gif)

if __name__ == "__main__":
    demo("evade", "N=6,RADIUS=2", gif=False)




