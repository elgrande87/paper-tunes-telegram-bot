import os
import torch
import torchaudio
import zlib
from encodec import EncodecModel
from encodec.utils import convert_audio

class AudioEncoder:
    def __init__(self, bandwidth=3.0):
        \"\"\"
        Initialisiert das EnCodec-Modell.
        Standard-Bandbreite ist 3.0 kbit/s (optimaler Kompromiss aus Qualität und Größe).
        Mögliche Werte für das 24kHz-Modell: 1.5, 3.0, 6.0, 12.0, 24.0.
        \"\"\"
        print(f"Lade EnCodec-Modell mit {bandwidth} kbit/s...")
        # Das 24kHz Modell laden (sehr gute Kompression für Musik & Sprache)
        self.model = EncodecModel.encodec_model_24khz()
        self.model.set_target_bandwidth(bandwidth)
        self.model.eval() # Wichtig: Evaluierungsmodus (kein Training, spart RAM)
        
        # Auf dem Raspberry Pi wird meist die CPU genutzt.
        # Falls doch mal eine kompatible GPU da ist, nutzen wir sie.
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.model.to(self.device)

    def encode_audio(self, audio_path):
        \"\"\"
        Nimmt eine Audiodatei (MP3/WAV/M4A), komprimiert sie über EnCodec 
        und gibt die extrem komprimierten rohen Bytes zurück.
        \"\"\"
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Die Datei {audio_path} wurde nicht gefunden.")

        # 1. Audio laden
        wav, sr = torchaudio.load(audio_path)
        
        # 2. Audio an das Modell anpassen 
        # EnCodec 24kHz Modell erwartet 24kHz Audio und 1 Kanal (Mono) für optimale Kompression
        wav = convert_audio(wav, sr, self.model.sample_rate, self.model.channels)
        
        # Batch-Dimension hinzufügen: [batch, channels, time]
        wav = wav.unsqueeze(0).to(self.device)

        # 3. Encodieren 
        # Wichtig für den Raspberry Pi: torch.no_grad() verhindert das Anlegen
        # von Zwischenspeichern für das Training. Das spart massiv Arbeitsspeicher!
        with torch.no_grad():
            encoded_frames = self.model.encode(wav)
        
        # 4. Daten extrahieren
        # encoded_frames ist eine Liste von (codes, scale). 'codes' sind die Musik-Tokens.
        codes = encoded_frames[0][0]  
        
        # Umwandeln in ein Numpy-Array (16-Bit Integer reicht völlig)
        codes_np = codes.cpu().numpy().astype('int16')
        
        # In rohe Bytes konvertieren
        raw_bytes = codes_np.tobytes()
        
        # 5. Packen für QR-Codes (Zusätzliche Kompression)
        # Da die EnCodec-Tokens 10-Bit nutzen, wir aber 16-Bit speichern, verschenken wir Platz.
        # zlib (Level 9 = Maximum) drückt diese Nullen perfekt weg.
        compressed_bytes = zlib.compress(raw_bytes, level=9)
        
        # Shape speichern, damit der Decoder später weiß, wie er die Daten rekonstruieren muss
        original_shape = codes_np.shape
        
        return compressed_bytes, original_shape

    def process_and_save(self, audio_path, output_raw_path):
        \"\"\"
        Hilfsfunktion für den Bot: Nimmt MP3, erzeugt das raw-Format und speichert es.
        \"\"\"
        compressed_bytes, shape = self.encode_audio(audio_path)
        
        # Wir speichern die Shape-Daten mit in der Datei (die ersten paar Bytes),
        # damit die Rückrichtung (Papier -> Musik) problemlos funktioniert.
        # Format: (Batch-Größe, Anzahl Quantisierer, Frames)
        shape_header = f"{shape[0]},{shape[1]},{shape[2]}\\n".encode('utf-8')
        
        with open(output_raw_path, 'wb') as f:
            f.write(shape_header)
            f.write(compressed_bytes)
        
        # Rückgabe der finalen Dateigröße in Bytes
        return len(shape_header) + len(compressed_bytes)

# Kurztest für die Konsole (wird nur ausgeführt, wenn du die Datei direkt startest)
if __name__ == "__main__":
    encoder = AudioEncoder(bandwidth=3.0)
    # Beispielaufruf (kommentiere dies aus, wenn du eine Test-MP3 hast):
    # final_size = encoder.process_and_save("test_song.mp3", "music.raw")
    # print(f"Erfolg! Größe für QR-Codes: {final_size / 1024:.2f} KB")