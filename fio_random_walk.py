import sys
import numpy as np


class FioRandomWalk:
    """
    A class to simulate a random walk over fio command parameters, specifically block size split (--bssplit)
    and IOPS rate (--rate_iops).

    Attributes:
        iops_mean (int): The mean value for IOPS around which variations will occur.
        iops_stddev (float): The standard deviation to use when generating IOPS values.
        block_sizes (list): A list of block sizes to be considered in the --bssplit argument.
        probs (numpy array): The probabilities associated with each block size.
        last_iops (int): The most recent IOPS value generated.
        random_seed (int): Seed for the random number generator to ensure reproducibility.
    """

    RUNTIMESECONDS = 10

    def __init__(self, iops_mean, iops_stddev, device, jobs, output_dir=None, readonly=True, random_seed=1):
        """
        Initializes the FioRandomWalk with the given parameters.

        Args:
            iops_mean (int): The starting mean value for IOPS.
            iops_stddev (float): The standard deviation for nudging the IOPS in the random walk.
            device (str): Device to run the fio command on.
            jobs (int): Number of jobs to run in parallel.
            output_dir (str, optional): Directory to save fio output logs. Defaults to None.
            readonly (bool, optional): Flag to indicate if only read operations should be performed. Defaults to True.
            random_seed (int, optional): Seed for random number generator for reproducibility. Defaults to 1.
        """

        np.random.seed(random_seed)  # Setting the seed for numpy's random number generator
        self.iops_mean = iops_mean
        self.iops_mean = iops_mean
        self.iops_stddev = iops_stddev
        self.device = device
        self.jobs = jobs
        self.block_sizes = ['512b', '4k', '8k', '16k', '64k', '256k', '512k', '1M']
        self.probs = np.array([0.125] * 8)  # Start with an equal distribution of block sizes
        self.last_iops = iops_mean  # Initialize the last_iops value
        self.iteration = 1
        self.output_dir = output_dir

        # Setting the initial read/write ratio to 80/20
        self.read_write_ratio = [0.8, 0.2]
        self.readonly = readonly

    def _nudge_probs(self):
        """
        Nudges the probabilities for block sizes using a normal distribution. Ensures that the probabilities
        always sum up to 1 and are between specified limits (1% and 30% in this case).
        """
        nudges = np.random.normal(0, 0.01, 8)  # Generate small nudges for probabilities
        new_probs = self.probs + nudges
        # new_probs = np.clip(new_probs, 0.01, 0.3)  # Ensure probabilities are between 1% and 30%
        self.probs = new_probs / new_probs.sum()  # Normalize to ensure they sum to 1

    def _nudge_iops(self):
        """
        Nudges the IOPS value using a normal distribution based on the last IOPS value,
        ensuring a non-negative result.

        Returns:
            int: The nudged IOPS value.
        """
        nudge = int(np.random.normal(0, self.iops_stddev))
        self.last_iops = max(10, self.last_iops + nudge)  # Ensure non-negative iops and update the last value
        return self.last_iops

    def _nudge_rw_ratio(self):
        """Nudges the read/write ratio using a normal distribution."""
        nudge = np.random.normal(0, 0.05)  # This is just an example, adjust based on your needs
        new_read_ratio = self.read_write_ratio[0] + nudge
        new_read_ratio = np.clip(new_read_ratio, 0.01, 0.99)  # Clipping between 1% and 99%

        self.read_write_ratio = [new_read_ratio, 1 - new_read_ratio]

    def generate(self):
        """
        Generates a fio command with the --bssplit, --rw, and --rate_iops parameters based on the random walk process.

        Returns:
            str: The generated fio command.
        """
        self._nudge_probs()
        if not self.readonly:
            self._nudge_rw_ratio()

        iops = self._nudge_iops()

        if self.readonly:
            rw = "randread"
            readonly_flag = "--readonly"
        else:
            rw = f"randrw"
            readonly_flag = ""
            iops = str(iops * self.read_write_ratio[0]) + "," + str(iops * self.read_write_ratio[1])
        # Determine the platform and adjust the filename accordingly
        if sys.platform.startswith("linux"):
            filename = f"/dev/{self.device}"
        elif sys.platform.startswith("win"):
            filename = fr"\\.\PhysicalDrive{self.device}"  # Assuming drive letter for Windows, e.g., C:
        elif sys.platform.startswith("darwin"):
            filename = f"/dev/{self.device}"  # This might need adjustment for macOS
        else:
            filename = self.device
        bssplit = ':'.join(f"{bs}/{prob:.2f}" for bs, prob in zip(self.block_sizes, self.probs * 100))
        cmd = (
            f"fio --filename={filename} "
            f"--name=mytest{np.random.randn()} "
            f"--rw={rw} "
            f"{readonly_flag} "
            f"--bssplit={bssplit} "
            f"--numjobs={self.jobs} "
            f"--time_based "
            f"--ioengine=libaio "
            f"--direct=1 "
            f"--time_based "
            f"--group_reporting "
            f"--iodepth=4 "
            f"--runtime={self.RUNTIMESECONDS}s "
            f"--rate_iops={iops} "
            f"--log_avg_msec=1000 "
        )
        if self.output_dir:
            cmd += (
                f"--write_lat_log={self.output_dir}/fio_latency_histogram{self.iteration} "
                f"--write_iops_log={self.output_dir}/fio_iops_histogram{self.iteration} "
                f"--write_bw_log={self.output_dir}/fio_bw_histogram{self.iteration}"
            )
        self.iteration += 1
        return cmd


if __name__ == "__main__":
    # Example usage:
    fio_gen = FioRandomWalk(10_000, np.sqrt(10_000), "nvme0n1p5", 1)
    for _ in range(1000):
        print(fio_gen.generate())
