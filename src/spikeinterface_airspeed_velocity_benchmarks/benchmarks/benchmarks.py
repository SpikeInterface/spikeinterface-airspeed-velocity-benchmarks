"""Import times (cheap; catches import-time regressions)."""


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
        