import shlex
import subprocess


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
        return fio_proc