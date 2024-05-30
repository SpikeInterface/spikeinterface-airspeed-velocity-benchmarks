# Write the benchmarking functions here.
# See "Writing benchmarks" in the asv docs for more information.
import tempfile


class IoSuite:
    """
    An example benchmark that times the performance of various kinds
    of iterating over dictionaries in Python.
    """
    def setup(self):
        from spikeinterface.core import generate_recording
        
        self.recording = generate_recording(num_channels=384, durations=[1.0])
        
        self.temporary_folder = tempfile.TemporaryDirectory()
        
    def time_write_binary(self):
        from spikeinterface.core import write_binary_recording
        
        save_path = self.temporary_folder.name + '/test.raw'
        file_paths = [save_path]
        job_kwargs = {"n_jobs": 1}
        write_binary_recording(recording=self.recording, file_paths=file_paths, **job_kwargs)
        
    def teardown(self):
        self.temporary_folder.cleanup()
        
class ImportSuite:
    
    def timeraw_import_full(self):
        
        return "import spikeinterface.full"
        
    def timeraw_import_core(self):
        
        return "spikeinterface.core"

