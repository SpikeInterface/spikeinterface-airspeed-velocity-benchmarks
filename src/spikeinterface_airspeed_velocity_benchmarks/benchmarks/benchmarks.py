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
    

    def timeraw_import_spikeinterface(self):
            
        return "import spikeinterface"
    
    def timeraw_import_core(self):
        
        return "import spikeinterface.core"

    def timeraw_import_extractors(self):
            
        return "import spikeinterface.extractors"

    def timeraw_import_preprocessing(self):
            
        return "import spikeinterface.preprocessing"
    
    def timeraw_import_postprocessing(self):
                
        return "import spikeinterface.postprocessing"

    def timeraw_import_qualitymetrics(self):
            
        return "import spikeinterface.qualitymetrics"

    def timeraw_import_comparison(self):            
        return "import spikeinterface.comparison"

    def timeraw_import_exporters(self):
        
        return "import spikeinterface.exporters"
    
    def timeraw_import_sortingcomponents(self):
        
        return "import spikeinterface.sortingcomponents"

    def timeraw_import_widgets(self):
                
        return "import spikeinterface.widgets"
    

    def timeraw_import_full(self):
        
        return "import spikeinterface.full"
        