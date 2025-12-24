import asyncio
from google import genai
import pyaudio
import os


class GeminiLiveClient:
    def __init__(self, api_key, on_message_callback, on_status_callback):
        os.environ["GOOGLE_API_KEY"] = api_key
        self.client = genai.Client()#http_options={'api_version': 'v1alpha'})
        self.on_message = on_message_callback
        self.on_status = on_status_callback
        self.running = False
        
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.SEND_SAMPLE_RATE = 16000
        self.CHUNK_SIZE = 512 # Genelde 1024 kullanılır ama gecikmeyi azaltmak için küçük tuttum.
        self.pya = pyaudio.PyAudio()
        
        self.MODEL = "gemini-2.5-flash-native-audio-preview-12-2025"
        self.CONFIG = {
            "response_modalities": ["AUDIO"],
            "input_audio_transcription": {}, 
            "output_audio_transcription": {},
            "system_instruction": "You are an assistant helping with interview preparation. "
                    "The text provided contains real-time conversational data. "
                    "Identify and answer the questions within this text, excluding personal questions answer questions in language of questions",
        }

        self.audio_queue_mic = asyncio.Queue(maxsize=5)
        self.input_text_buffer = []
        self.output_text_buffer = []

    async def _listen_audio(self):
        device_index = None
        device_name = None
        
        # Stereo Mix araması
        for i in range(self.pya.get_device_count()):
            dev_info = self.pya.get_device_info_by_index(i)
            name_lower = dev_info['name'].lower()
            # Windows'ta genelde 'stereo mix', Mac'te 'blackhole' veya 'loopback'
            if dev_info['maxInputChannels'] > 0 and any(k in name_lower for k in ['stereo mix', 'loopback', 'what u hear', 'blackhole']):
                device_index = i
                device_name = dev_info['name']
                print(f"DEBUG: Stereo Mix Bulundu: {device_name}")
                break
        
        if device_index is None:
             default_device = self.pya.get_default_input_device_info()
             device_index = default_device["index"]
             device_name = default_device["name"]
             print(f"DEBUG: Stereo Mix bulunamadı, Mikrofon kullanılıyor: {device_name}")

        self.on_status(f"Dinleniyor: {device_name}")

        try:
            audio_stream = await asyncio.to_thread(
                self.pya.open,
                format=self.FORMAT,
                channels=self.CHANNELS,
                rate=self.SEND_SAMPLE_RATE,
                input=True,
                input_device_index=device_index,
                frames_per_buffer=self.CHUNK_SIZE,
            )
        except Exception as e:
            self.on_status(f"Ses Cihazı Hatası: {e}")
            return

        kwargs = {"exception_on_overflow": False}
        
        while self.running:
            try:
                data = await asyncio.to_thread(audio_stream.read, self.CHUNK_SIZE, **kwargs)
                if not self.audio_queue_mic.full():
                    await self.audio_queue_mic.put({"data": data, "mime_type": "audio/pcm"})
            except Exception as e:
                print(f"Ses okuma hatası: {e}")
                break
        
        audio_stream.stop_stream()
        audio_stream.close()

    async def _send_realtime(self, session):
        while self.running:
            msg = await self.audio_queue_mic.get()
            await session.send_realtime_input(audio=msg)

    async def _receive_text(self, session):
        while self.running:
            try:
                turn = session.receive()
                async for response in turn:
                    if not self.running: break

                    if response.server_content and response.server_content.input_transcription:
                        text = response.server_content.input_transcription.text
                        if text:
                            print(f"[User (Raw)]: {text}")
                            self.input_text_buffer.append(text)
                            full_text = "".join(self.input_text_buffer)
                            if len(full_text) > 50 or any(c in text for c in ".!?"):
                                self.on_message("User", full_text)
                                self.input_text_buffer = []

                    if response.server_content and response.server_content.output_transcription:
                        text = response.server_content.output_transcription.text
                        if text:
                            print(f"[Gemini (Raw)]: {text}")
                            self.output_text_buffer.append(text)
                            
                            full_text = "".join(self.output_text_buffer)
                            if len(full_text) > 50 or any(c in text for c in ".!?"):
                                self.on_message("Gemini", full_text)
                                self.output_text_buffer = []
            except Exception as e:
                print(f"Alma hatası: {e}")
                break

    async def start_session(self):
        self.running = True
        try:
            async with self.client.aio.live.connect(model=self.MODEL, config=self.CONFIG) as session:
                self.on_status("Gemini'ye Bağlandı! Konuşun...")
                async with asyncio.TaskGroup() as tg:
                    tg.create_task(self._send_realtime(session))
                    tg.create_task(self._listen_audio())
                    tg.create_task(self._receive_text(session))
        except Exception as e:
            self.on_status(f"Bağlantı Hatası: {str(e)}")
            print(f"Bağlantı Hatası Detay: {e}")
        finally:
            self.running = False
            self.pya.terminate()
            self.on_status("Bağlantı sonlandırıldı.")

    def stop(self):
        self.running = False