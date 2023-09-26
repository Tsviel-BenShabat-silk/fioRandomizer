import argparse
from fio_random_walk import FioRandomWalk
from fio_chain_runner import FioChainedRunner
from io_runner import IORunner


def main(args):
    print("Estimating the delay time it takes for fio to start running...")
    runner = IORunner()
    median_delay = 0.05
    print("The assessed delay time for fio to start running is:", median_delay, "seconds")

    fio_gen = FioRandomWalk(
        iops_mean=args.iops_mean,
        iops_stddev=args.iops_stddev,
        device=args.device,
        jobs=args.jobs,
        output_dir=args.output_dir,
        readonly=args.readonly,
        random_seed=args.random_seed
    )

    chain_runner = FioChainedRunner(runner, fio_gen, median_delay, max_processes=args.max_processes)
    chain_runner.run_fio_with_delay()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run FioRandomWalk with parameters.")

    parser.add_argument("--device", type=str, default="nvme0n1p5", help="The device name or drive letter to be tested. On Linux, it can be 'nvme0n1p5'. On Windows, it can be a drive letter like 'C'.")
    parser.add_argument("--jobs", type=int, default=1, help="Number of jobs to run in parallel.")
    parser.add_argument("--iops_mean", type=int, default=5000, help="Starting mean value for IOPS.")
    parser.add_argument("--iops_stddev", type=float, default=1000, help="Standard deviation for nudging the IOPS.")
    parser.add_argument("--output_dir", type=str, help="Output directory for logs.")
    parser.add_argument("--write-enable", dest="readonly", action="store_false", help="Enable write mode. Default is read-only mode.")
    parser.add_argument("--random_seed", type=int, default=1, help="Seed for random number generator.")
    parser.add_argument("--max_processes", type=int, default=2,
                        help="Maximum number of processes for FioChainedRunner.")

    args = parser.parse_args()
    main(args)
