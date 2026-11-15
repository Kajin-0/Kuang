import math
import tempfile
import unittest
import wave
from pathlib import Path

from kuang.house_section_levels import analyze
from kuang.schema import ValidationError

class SectionLevelsTests(unittest.TestCase):
    def _wav(self, path):
        with wave.open(str(path),"wb") as w:
            w.setnchannels(2);w.setsampwidth(3);w.setframerate(48000)
            data=bytearray()
            for i in range(48000*2):
                sec=i/48000
                amp=.1 if sec<1 else .3
                sample=round(8388607*amp*math.sin(2*math.pi*100*sec))
                data.extend(sample.to_bytes(3,"little",signed=True)*2)
            w.writeframes(data)

    def test_section_peaks_and_percentiles_detect_time_variation(self):
        with tempfile.TemporaryDirectory() as d:
            file=Path(d)/"signal.wav"
            self._wav(file)
            r=analyze(file,[("Intro",0,1),("Drop",1,2)])
            self.assertEqual(r,analyze(file,[("Intro",0,1),("Drop",1,2)]))
            x=r["sections"]["Intro"]
            y=r["sections"]["Drop"]
            self.assertAlmostEqual(y["sample_peak_dbfs"]-x["sample_peak_dbfs"],9.542,delta=.1)
            self.assertAlmostEqual(y["window_100ms"]["p95_rms_dbfs"]-x["window_100ms"]["p95_rms_dbfs"],9.542,delta=.1)
            self.assertEqual(x["window_100ms"]["windows"],10)
            self.assertEqual(r["measurement"],"PCM amplitude/sample peak, no oversampled true peak")
            self.assertEqual(x["perceptual_quality"],"NOT_EVALUATED")
    def test_bad_regions_fail_closed(self):
        with tempfile.TemporaryDirectory() as d:
            file=Path(d)/"signal.wav";self._wav(file)
            for spec in [("A",2,3),("A",-1,1),("A",0,.01),("A",0,float("nan"))]:
                with self.assertRaises(ValidationError):
                    analyze(file,[spec])
            with self.assertRaises(ValidationError):
                analyze(file,[])
            with self.assertRaises(ValidationError):
                analyze(Path(d)/"missing.wav",[("A",0,1)])

if __name__=="__main__":
    unittest.main()
