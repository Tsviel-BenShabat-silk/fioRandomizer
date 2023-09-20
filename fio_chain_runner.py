import time
import multiprocessing


# Helper function
def _run_fio(io_runner, device, num_jobs, fio_cmd):
    print(f"Running fio command: {fio_cmd}")
    proc = io_runner.run_io(device=device, num_jobs=num_jobs, fio_cmd=fio_cmd)
    proc.wait()
    proc.kill()
    print(f"Finished fio command: {fio_cmd}")


class FioChainedRunner:

    def __init__(self, io_runner, fio_gen, median_delay_seconds, max_processes=2):
        self.io_runner = io_runner
        self.fio_gen = fio_gen
        self.median_delay_seconds = median_delay_seconds
        self.pool = multiprocessing.Pool(max_processes)

    def run_fio_with_delay(self):
        try:
            results = []  # List to keep track of async results

            while True:
                # Generate the next fio command using FioRandomWalk.
                fio_cmd = self.fio_gen.generate()

                # Adjust the --runtime value
                runtime_delay = self.fio_gen.RUNTIMESECONDS - self.median_delay_seconds

                # Run the fio command in a separate process using the helper function.
                async_result = self.pool.apply_async(_run_fio, args=(self.io_runner, "nvme0n1p5", 1, fio_cmd))
                results.append(async_result)  # Append the async result to the list

                # Check completed results and fetch them to clear them from memory.
                for res in results.copy():  # Iterate over a copy to safely modify the list during iteration
                    if res.ready():
                        res.get()  # Fetch the result. If you don't need the result, this just clears it from memory.
                        results.remove(res)  # Remove the completed result from the list

                # Delay for the remaining time.
                print(f"Sleeping for {runtime_delay} seconds")
                time.sleep(runtime_delay)

        except KeyboardInterrupt:
            self.pool.terminate()
            self.pool.close()
            self.pool.join()
            print("Interrupted, waiting for processes to finish...")
            print("All processes finished.")
