import argparse
from visound.core.AudioController import AudioController
from visound.core.TraversalMode import TraversalMode
from pedalboard import Pedalboard, Reverb, Compressor, PitchShift

class SonifyGUI:
    def __init__(self):
        self.audio_controller = AudioController()
        self.parser = argparse.ArgumentParser(description="Sonify an image into audio")
        self.parser.add_argument("--input", type=str, help="Path to the input image")
        self.parser.add_argument("--width", type=int, default=256, help="Image width")
        self.parser.add_argument("--height", type=int, default=256, help="Image height")
        self.parser.add_argument("--dpc", type=float, default=0.01,
                            help="Duration per column (seconds)")
        self.parser.add_argument("--sample_rate", type=int, default=44100, help="Sample rate of the audio")
        self.parser.add_argument("--mode", choices=["ltr", "rtl"], default="ltr",
                            help="Traversal Mode\n"
                            "Modes are as follows:\n"
                            "ltr - Left to right\n"
                            "rtl - Right to left")
        self.parser.add_argument("--output", type=str, default=".",
                            help="Path to the output file where the audio file should be saved")
        self.parser.add_argument("--color", type=str, default="#00FF00",
                            help="Color of the bar")
        self.args = self.parser.parse_args()
        self.GUI()

    def pause_or_resume(self, pause: bool) -> None:
        if pause:
            self.audio_controller.resume()
        else:
            self.audio_controller.pause()

    def reset(self) -> None:
        self.audio_controller.reset()

    def GUI(self):

        from GUI import MainWindow
        from PyQt6.QtWidgets import QApplication
        from visound.core.Sonify import Sonify
        import sys

        sonify = Sonify(
            file_path=self.args.input,
            dimension=(self.args.height, self.args.width),
            duration_per_column=self.args.dpc,
            sample_rate=self.args.sample_rate,
        )

        audio = None
        traversal_mode: int = -1

        match self.args.mode:
            case "ltr":
                audio = sonify.LTR()
                traversal_mode = TraversalMode.LeftToRight

            case "rtl":
                audio = sonify.RTL()
                traversal_mode = TraversalMode.RightToLeft



        sonify.save(self.args.output)

        board = Pedalboard([
            Compressor(threshold_db=-24, ratio=6),
            Reverb(room_size=0.25),
            PitchShift(semitones=4.0, )
        ])

        effected = board(audio, self.args.sample_rate)
        self.audio_controller.set_params(effected, self.args.sample_rate)

        app = QApplication(sys.argv)
        self.GUI = MainWindow()
        self.GUI.traversal_mode = traversal_mode
        self.GUI.loadImage(sonify.image)
        self.GUI.dpc = self.args.dpc
        self.GUI.init_bar_position()
        self.GUI.reset_signal.connect(self.reset)
        self.GUI.bar_color = "#FF5000"
        self.GUI.pause_resume_signal.connect(self.pause_or_resume)
        app.exec()

if __name__ == "__main__":
    s = SonifyGUI()
