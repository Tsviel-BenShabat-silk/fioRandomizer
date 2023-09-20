import subprocess
import statistics
import time
import shlex
import math
import re


class IOActivityChecker:
    """
    This class checks for IO activity by inspecting /proc/diskstats.
    """

    SECTOR_SIZE = None
    PATTERN = None

    def __init__(self, device):
        self.device = device
        self.SECTOR_SIZE = self._get_sector_size()
        self.PATTERN = re.compile(rf"\s+\d+\s+\d+\s+{self.device}\s+\d+\s+\d+\s+(\d+)\s+\d+\s+\d+\s+\d+\s+(\d+)")

    def _get_sector_size(self):
        try:
            size = subprocess.check_output(["blockdev", "--getss", f"/dev/{self.device}"], universal_newlines=True)
            return int(size.strip())
        except Exception as e:
            print(f"Error getting sector size for {self.device}: {e}")
            return 512  # default to 512 if there's an error

    def check_io_activity(self):
        try:
            with open('/proc/diskstats', 'r') as f:
                content = f.read()
                match = self.PATTERN.search(content)

                if match:
                    sectors_read = int(match.group(1))
                    bytes_read = sectors_read * self.SECTOR_SIZE
                    return bytes_read
        except Exception as e:
            print(f"Error reading /proc/diskstats: {e}")


class IORunner:
    """
    This class handles IO operations using the fio command.
    """

    FIO_BASE_CMD = "fio --name=mytest --filename=/dev/{} --rw=randread --numjobs={} --time_based --runtime=2s --rate_iops=1000 --iodepth=5"

    @staticmethod
    def run_io(device, num_jobs, fio_cmd=None):
        if not fio_cmd:
            cmd_string = IORunner.FIO_BASE_CMD.format(device, num_jobs)
        else:
            cmd_string = fio_cmd

        cmd_list = shlex.split(cmd_string)

        fio_proc = subprocess.Popen(cmd_list, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)
        # fio_proc = subprocess.Popen(cmd_list, shell=False)
        return fio_proc


class IOStatistics:
    """
    This class gathers and displays IO-related statistics.
    """

    Z_VALUE = 3.09  # approximately the z-value for the 99.9th percentile

    def __init__(self, io_checker: IOActivityChecker, io_runner: IORunner):
        self.io_checker = io_checker
        self.io_runner = io_runner

    def _gather_baseline(self):
        baseline_diffs = []
        prev_value = self.io_checker.check_io_activity()

        for _ in range(1000):  # Collect for 1 second (100 samples at 10ms intervals)
            time.sleep(0.05)  # Sleep for 10ms
            current_value = self.io_checker.check_io_activity()
            baseline_diffs.append(max(current_value - prev_value, 0))
            prev_value = current_value

        return self._compute_upper_confidence_interval(baseline_diffs)

    def _check_io_start(self, upper_bound):
        prev_value = self.io_checker.check_io_activity()
        iteration = 0

        while True:
            current_value = self.io_checker.check_io_activity()
            iteration += 1
            time.sleep(0.05)
            current_diff = current_value - prev_value

            if current_diff > upper_bound:
                print(f"Iteration: {iteration}")
                return  # I/O has started
            prev_value = current_value

    @staticmethod
    def _compute_upper_confidence_interval(data):
        mean = statistics.mean(data)
        std_dev = statistics.stdev(data)
        margin_error = IOStatistics.Z_VALUE * (std_dev / math.sqrt(len(data)))
        return mean + margin_error

    def gather_statistics(self, num_iterations, num_jobs, device):
        results = {}
        upper_bound = self._gather_baseline()
        print(f"Baseline: {upper_bound}")

        if type(num_jobs) is int:
            num_jobs = [num_jobs, ]

        for nj in num_jobs:
            elapsed_times = []

            for _ in range(num_iterations):
                start_time = time.time()
                fio_proc = self.io_runner.run_io(device, nj)
                self._check_io_start(upper_bound)
                elapsed = time.time() - start_time
                elapsed_times.append(elapsed)
                fio_proc.wait()

            mean = statistics.mean(elapsed_times)
            median = statistics.median(elapsed_times)
            std_dev = statistics.stdev(elapsed_times)
            results[nj] = (mean, median, std_dev)

        return results

    @staticmethod
    def display_statistics(stats):
        for key, value in stats.items():
            print(f"Num Jobs: {key}")
            print("Mean:", value[0], "Median:", value[1], "Std Dev:", value[2])
            print("------------")


if __name__ == "__main__":
    checker = IOActivityChecker("nvme0n1p5")
    runner = IORunner()
    stats_maker = IOStatistics(checker, runner)

    num_jobs = [8, ]
    stats = stats_maker.gather_statistics(5, num_jobs, "nvme0n1p5")
    stats_maker.display_statistics(stats)
