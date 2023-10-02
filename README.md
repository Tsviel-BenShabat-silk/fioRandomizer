Here's a revised `README.md` based on the given `main.py`:

---

# FIO Random Walk Simulator

This project provides a way to run FIO (Flexible I/O Tester) using parameters generated through a random walk simulation. The tool adjusts the IOPS values over time, allowing users to simulate various IO patterns.

## Features

- Simulate IO patterns through a random walk over fio command parameters.
- Adjusts IOPS values based on provided mean and standard deviation.
- Accepts user inputs for various parameters including device, job count, and output directory.
- Supports both read-only and write-enabled modes.

## Prerequisites

- Ensure you have `numpy` installed.
- FIO should be installed on your system.

## How to Use

1. Clone the repository:
```bash
git clone [repository_url]
cd [repository_directory]
```

2. Run the main script using the following command:
```bash
python main.py --device DEVICE_NAME --jobs NUMBER_OF_JOBS
```

### Parameters

- `--device`: Specifies the device to be tested. On Linux, this can be something like "nvme0n1p5" and on Windows, a drive letter like "C:".
  
- `--jobs`: (Optional) Number of jobs to run in parallel. Default is `1`.

- `--iops_mean`: (Optional) Starting mean value for IOPS. Default is `5000`.

- `--iops_stddev`: (Optional) Standard deviation for nudging the IOPS. Default is `1000`.

- `--output_dir`: (Optional) Directory where the output logs and results will be saved.

- `--write-enable`: (Optional) If provided, enables write mode. By default, it runs in read-only mode.

- `--random_seed`: (Optional) Seed for the random number generator to ensure reproducibility. Default is `1`.

- `--max_processes`: (Optional) Maximum number of processes for FioChainedRunner. Default is `2`.

### Examples:

For a Linux device with 4 jobs in read-only mode:
```bash
python main.py --device nvme0n1p5 --jobs 4
```

For a Windows device (drive C) with 1 job in read-write mode:
```bash
python main.py --device C: --jobs 1 --write-enable
```


## Limitations

- The simulation does not adjust io depth parameter yet

## Contributing

Contributions are welcome! Please submit a pull request or open an issue to discuss potential changes/additions.

--- 

Note: Ensure to replace `[repository_url]` and `[repository_directory]` with the actual URL of your repository and its directory name respectively.
