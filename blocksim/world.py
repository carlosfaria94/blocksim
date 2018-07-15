import json
import simpy
from schema import Schema, And, Use, SchemaError


class SimulationWorld:
    """The world starts here. It sets the simulation world.

    The simulation world can be configured with the following characteristics:

    :param int sim_duration: duration of the simulation
    :param str blockchain: the type of blockchain being simulated (e.g. bitcoin or ethereum)
    :param dict time_between_block_distribution: Probability distribution to represent the time between blocks
    :param dict validate_tx_distribution: Probability distribution to represent the transaction validation delay
    :param dict validate_block_distribution: Probability distribution to represent the block validation delay

    Each distribution is represented as dictionary, with the following schema:
    ``{ 'name': str, 'parameters': tuple }``

    We use SciPy to work with probability distributions.

    You can see a complete list of distributions here:
    https://docs.scipy.org/doc/scipy/reference/stats.html

    You can use the ``scripts/test-fit-distribution.py`` to find a good distribution and its parameters which fits your input data measured.
    """

    def __init__(self,
                 sim_duration: int,
                 initial_time: int,
                 blockchain: str,
                 path_to_measure_latency: str,
                 path_to_measure_bandwidth: str,
                 time_between_block_delay: dict,
                 validate_tx_delay: dict,
                 validate_block_delay: dict):
        if isinstance(sim_duration, int) is False:
            raise TypeError(
                'sim_duration needs to be an integer')
        if isinstance(initial_time, int) is False:
            raise TypeError(
                'initial_time needs to be an integer')
        if isinstance(blockchain, str) is False:
            raise TypeError(
                'blockchain needs to be a string')
        self._validate_distribution(
            time_between_block_delay, validate_tx_delay, validate_block_delay)
        self._sim_duration = sim_duration
        self._initial_time = initial_time
        self._blockchain = blockchain
        self._path_to_measure_latency = path_to_measure_latency
        self._path_to_measure_bandwidth = path_to_measure_bandwidth
        self._time_between_block_delay = time_between_block_delay
        self._validate_tx_delay = validate_tx_delay
        self._validate_block_delay = validate_block_delay
        # Set the SimPy Environment
        self._env = simpy.Environment(initial_time=self._initial_time)
        self._set_delays()
        self._set_latencies()
        self._set_bandwidths()

    def _validate_distribution(self, *distributions: dict):
        for distribution in distributions:
            distribution_schema = Schema({
                'name': And(Use(str)),
                'parameters': And(Use(tuple))
            })
            try:
                distribution_schema.validate(distribution)
            except SchemaError:
                raise TypeError(
                    'Probability distribution must follow this schema: { \'name\': str, \'parameters\': tuple }')

    def _set_delays(self):
        """Injects the probability distribution delays in the environment variable to be
        used during the simulation"""
        self._env.delays = dict(
            VALIDATE_TX=self._validate_tx_delay,
            VALIDATE_BLOCK=self._validate_block_delay,
            TIME_BETWEEN_BLOCKS=self._time_between_block_delay,
        )

    def _set_latencies(self):
        """Reads the file with the latencies measurements taken"""
        with open(self._path_to_measure_latency) as f:
            data = json.load(f)
        self._locations = list(data['locations'])
        self._latencies = data['locations']

    def _set_bandwidths(self):
        """Reads the file with the bandwidths measurements taken"""
        with open(self._path_to_measure_bandwidth) as f:
            data = json.load(f)
        locations = list(data['locations'])
        if locations == self._locations:
            self._bandwidths = data['locations']
        else:
            raise RuntimeError(
                "The locations in latencies measurements are not equal in bandwidth measurements")

    @property
    def blockchain(self):
        return self._blockchain

    @property
    def locations(self):
        return self._locations

    @property
    def latencies(self):
        return self._latencies

    @property
    def bandwidths(self):
        return self._bandwidths

    @property
    def environment(self):
        return self._env

    @property
    def start_simulation(self):
        run = self._env.run(until=self._sim_duration)
        return run
